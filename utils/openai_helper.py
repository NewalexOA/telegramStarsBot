import aiohttp
import structlog
from aiogram.types import Message, BufferedInputFile
from openai import AsyncOpenAI, PermissionDeniedError
from config_reader import bot_config
from utils.image_cache import ImageCache
from utils.text_utils import extract_images_and_clean_text
import json
from openai.types.beta.threads import Run
from typing import TypedDict, List, TYPE_CHECKING

# Используем TYPE_CHECKING для избежания циклических импортов
if TYPE_CHECKING:
    from services.novel import NovelService
    from models.novel import NovelState

logger = structlog.get_logger()
openai_client = AsyncOpenAI(
    api_key=bot_config.openai_api_key.get_secret_value()
)

# Инициализация кэша
image_cache = ImageCache()

async def create_assistant():
    """Создает или получает существующего ассистента"""
    try:
        with open('scenario.txt', 'r', encoding='utf-8') as file:
            scenario = file.read()
        
        # Определяем функцию для ассистента
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "end_story",
                    "description": "Завершает текущую историю",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "enum": ["completed", "final_scene", "user_choice"],
                                "description": "Причина завершения истории"
                            }
                        },
                        "required": ["reason"]
                    }
                }
            },
        ]
        
        instructions = """
        ... существующие инструкции ...
        
        ВАЖНО: При достижении финальной сцены:
        1. НЕ спрашивай разрешения у пользователя
        2. НЕ пиши фразы типа "История подошла к концу. Если ты хочешь, я могу завершить её"
        3. Сразу вызывай функцию end_story с параметром reason="final_scene"
        4. После описания рассвета на набережной сразу заканчивай историю
        
        Пример правильного завершения:
        "...глядя на поднимающееся солнце, она понимает, что её решения уже определили дальнейший путь и отношения с каждым."
        [Вызов end_story]
        """
        
        assistant = await openai_client.beta.assistants.create(
            name="Novel Game Assistant",
            instructions=scenario + instructions,
            model="gpt-4-turbo-preview",
            tools=tools
        )
        
        return assistant.id
        
    except PermissionDeniedError as e:
        error_details = {}
        try:
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                error_json = e.response.json()
                error_details = error_json.get('error', {})
        except Exception:
            error_details = {'message': str(e)}
            
        logger.error(
            "Ошибка доступа к API OpenAI",
            error_code=error_details.get('code'),
            error_message=error_details.get('message'),
            error_type=error_details.get('type'),
            error_param=error_details.get('param'),
            status_code=getattr(e, 'status_code', None),
            raw_error=str(e),
            region_info=True
        )
        
        # Возвращаем фиксированный ID для тестирования
        return "asst_test_123456789"  # Временное решение
        
    except Exception as e:
        logger.error(
            "Неожиданная ошибка при создании ассистента",
            error=str(e),
            error_type=type(e).__name__,
            traceback=True
        )
        raise

async def download_image(url: str) -> bytes:
    """Скачивание изображения по URL"""
    try:
        # Извлекаем ID изображения из URL
        if "id=" in url:
            image_id = url.split("id=")[1].split("&")[0]
        elif "/file/d/" in url:
            image_id = url.split("/file/d/")[1].split("/")[0]
        else:
            image_id = url
            
        logger.info(f"Extracted image ID: {image_id}")
        
    except Exception as e:
        logger.error(f"Failed to extract image ID from URL {url}: {e}")
        raise
    
    # Пробуем получить из кэша
    cached_data = await image_cache.get(image_id)
    if cached_data:
        logger.info(f"Cache hit for image {image_id}")
        return cached_data
    
    # Если нет в кэше, скачиваем
    async with aiohttp.ClientSession() as session:
        try:
            # Используем прямой URL для скачивания
            direct_url = f"https://drive.google.com/uc?export=download&id={image_id}"
            logger.info(f"Downloading image from URL: {direct_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(direct_url, headers=headers) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.read()
                    await image_cache.put(image_id, data)
                    logger.info(f"Cached new image {image_id}")
                    return data
                    
                raise Exception(f"Failed to download image: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading image {image_id}: {e}")
            raise

async def send_assistant_response(message: Message, assistant_message: str) -> None:
    """Отправка ответа ассистента пользователю."""
    logger.info("Starting extract_images_and_clean_text")
    logger.info(f"Original message:\n{assistant_message}")
    
    # Получаем список кортежей (текст, image_id)
    messages = extract_images_and_clean_text(assistant_message)
    
    logger.info(f"Number of extracted messages: {len(messages)}")
    logger.info(f"Raw messages: {messages}")
    
    # Отправляем сообщения
    for i, (text, image_id) in enumerate(messages, 1):
        logger.info(f"\nProcessing message {i}/{len(messages)}")
        logger.info(f"Text: {text[:200]}..." if text else "No text")
        logger.info(f"Image ID: {image_id}" if image_id else "No image")
        
        if image_id:
            try:
                image_url = f"https://drive.google.com/uc?export=view&id={image_id}"
                logger.info(f"Processing image: {image_id}")
                image_data = await download_image(image_url)

                await message.answer_photo(
                    BufferedInputFile(image_data, filename="image.webp"),
                    caption=text if text else None
                )
                logger.info("Image sent successfully")
            except Exception as e:
                logger.error(f"Error sending image: {e}")
                await message.answer("Не удалось загрузить изображение")
                if text:
                    logger.info("Sending text after image error")
                    await message.answer(text)
        else:
            if text:
                logger.info("Sending text-only message")
                await message.answer(text)

class ToolOutput(TypedDict):
    tool_call_id: str
    output: str

async def handle_tool_calls(
    run: Run, 
    thread_id: str, 
    novel_service: 'NovelService',  # Используем строковую аннотацию
    novel_state: 'NovelState',      # Используем строковую аннотацию
    message: Message
) -> List[ToolOutput]:
    """
    Обрабатывает вызовы инструментов от ассистента
    
    Args:
        run: Текущий запуск ассистента
        thread_id: ID треда беседы
        novel_service: Сервис для работы с новеллой
        novel_state: Текущее состояние новеллы
        message: Сообщение пользователя
    
    Returns:
        List[ToolOutput]: Список результатов выполнения инструментов
    """
    logger.info(
        "Processing tool calls",
        thread_id=thread_id,
        user_id=message.from_user.id,
        run_id=run.id
    )
    
    if not hasattr(run, 'required_action') or not run.required_action:
        logger.warning(
            "No required action in run",
            run_id=run.id,
            thread_id=thread_id
        )
        return []

    if not hasattr(run.required_action, 'submit_tool_outputs'):
        logger.warning(
            "No tool outputs to submit",
            run_id=run.id,
            thread_id=thread_id
        )
        return []
    
    tool_outputs: List[ToolOutput] = []
    
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        try:
            function_name = tool_call.function.name  # Добавляем получение имени функции
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(
                "Processing tool call",
                function_name=function_name,
                arguments=arguments,
                user_id=message.from_user.id
            )
            
            if function_name == "end_story":
                try:
                    # Валидация аргументов
                    if "reason" not in arguments:
                        raise ValueError("Missing required argument 'reason'")
                        
                    reason = arguments["reason"]
                    if reason not in ["completed", "final_scene", "user_choice"]:
                        raise ValueError(f"Invalid reason: {reason}")
                        
                    logger.info(
                        "Ending story",
                        reason=reason,
                        user_id=message.from_user.id,
                        thread_id=thread_id
                    )
                    
                    await novel_service.end_story(novel_state, message)
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({
                            "status": "success",
                            "reason": reason
                        })
                    })
                    
                except Exception as e:
                    logger.error(
                        "Error ending story",
                        error=str(e),
                        user_id=message.from_user.id,
                        thread_id=thread_id
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({
                            "status": "error",
                            "error": str(e)
                        })
                    })
            else:
                logger.warning(
                    "Unknown function called",
                    function_name=function_name,
                    user_id=message.from_user.id
                )
                
        except Exception as e:
            logger.error(
                "Error processing tool call",
                error=str(e),
                user_id=message.from_user.id,
                thread_id=thread_id
            )
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps({
                    "status": "error",
                    "error": "Internal error processing tool call"
                })
            })
    
    return tool_outputs
