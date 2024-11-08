import re
from typing import Tuple, List
import aiohttp
import structlog
from aiogram.types import Message, BufferedInputFile
from openai import AsyncOpenAI
from config_reader import get_config, BotConfig
from utils.image_cache import ImageCache

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

def extract_images_and_clean_text(text: str) -> Tuple[str, List[str]]:
    """Извлекает ссылки на изображения и очищает текст"""
    image_patterns = [
        r'\[AI отправляет фото:.*?https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing.*?\]',
        r'!\(https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing\)',
        r'\(https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing\)'
    ]
    
    brackets_pattern = r'\[.*?\]|\]|\['
    service_patterns = [
        r'\*\*СЦЕНА \d+:.*?\*\*\n*',
        r'\*\*Описание:\*\*\n*',
        r'---\n*',
        r'Цель достигнута:.*?\n',
        r'### СЦЕНА.*?\n',
        r'^\d+\.\s+(?=[А-Я])',
        r'Теперь мы готовы начать!.*?\n'
    ]
    
    image_ids = []
    cleaned_parts = []
    last_end = 0
    
    for pattern in image_patterns:
        matches = list(re.finditer(pattern, text))
        for match in matches:
            cleaned_parts.append(text[last_end:match.start()])
            image_ids.append(match.group(1))
            last_end = match.end()
    
    cleaned_parts.append(text[last_end:])
    intermediate_text = ''.join(cleaned_parts)
    intermediate_text = re.sub(brackets_pattern, '', intermediate_text)
    
    for pattern in service_patterns:
        intermediate_text = re.sub(pattern, '', intermediate_text)
    
    intermediate_text = re.sub(r'\*\*', '', intermediate_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', intermediate_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text, image_ids

async def send_assistant_response(message: Message, assistant_message: str):
    """Отправка ответа ассистента с разбивкой на части с изображениями"""
    parts = re.split(r'(\[AI отправляет фото:.*?\]|\!\(https://drive\.google\.com/.*?\)|\(https://drive\.google\.com/.*?\))', assistant_message)
    
    for part in parts:
        if not part.strip():
            continue
            
        cleaned_text, image_ids = extract_images_and_clean_text(part)
        
        for image_id in image_ids:
            try:
                image_url = f"https://drive.google.com/uc?export=view&id={image_id}"
                logger.info(f"Processing image: {image_id}")
                image_data = await download_image(image_url)
                await message.answer_photo(BufferedInputFile(image_data, filename="image.webp"))
            except Exception as e:
                logger.error(f"Error sending image: {e}")
                await message.answer("Не удалось загрузить изображение")
        
        if cleaned_text:
            await message.answer(cleaned_text)