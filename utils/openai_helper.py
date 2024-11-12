import aiohttp
import structlog
from aiogram.types import Message, BufferedInputFile
from openai import AsyncOpenAI
from config_reader import get_config, BotConfig
from utils.image_cache import ImageCache
from utils.text_utils import extract_images_and_clean_text

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")
openai_client = AsyncOpenAI(
    api_key=bot_config.openai_api_key.get_secret_value()
)

# Инициализация кэша
image_cache = ImageCache()

async def create_assistant():
    """Создание ассистента OpenAI"""
    with open('scenario.txt', 'r', encoding='utf-8') as file:
        scenario = file.read()
    
    # Определяем функцию для ассистента
    tools = [
        {
            "type": "function",
            "function": {
                "name": "end_story",
                "description": "Завершает историю и очищает данные пользователя",
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
        {"type": "retrieval"}
    ]
    
    assistant = await openai_client.beta.assistants.create(
        name="Novel Game Assistant",
        instructions=scenario + "\n\nКогда история достигает финальной сцены или завершается, вызови функцию end_story с соответствующей причиной.",
        model="gpt-4-turbo-preview",
        tools=tools
    )
    return assistant.id

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
    logger.info(f"Raw messages: {messages}")  # Добавляем вывод сырых данных
    
    # Проверяем формат каждого сообщения
    formatted_messages = []
    for msg in messages:
        logger.info(f"Processing message item: {msg}")
        if isinstance(msg, tuple) and len(msg) == 2:
            formatted_messages.append(msg)
        elif isinstance(msg, str):
            formatted_messages.append((msg, None))
        else:
            logger.error(f"Unexpected message format: {msg}")
            continue
    
    logger.info(f"Formatted messages: {formatted_messages}")
    
    # Отправляем сообщения
    for i, (text, image_id) in enumerate(formatted_messages, 1):
        logger.info(f"\nProcessing message {i}/{len(formatted_messages)}")
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
