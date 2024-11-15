import re
from typing import List, Tuple, Optional

# Паттерны для поиска изображений в тексте
image_patterns = [
    # Формат [AI отправляет фото: ![название](ссылка)]
    r'\[AI отправляет фото:[ \t\r\n]*!\[.*?\]\(https://drive\.google\.com/file/d/(.*?)/view\?(?:usp=sharing|usp=drive_link)\)\]\.?',
    
    # Формат [AI отправляет фото: ссылка]
    r'\[AI отправляет фото:[ \t\r\n]*https://drive\.google\.com/file/d/(.*?)/view\?(?:usp=sharing|usp=drive_link)\]\.?',
    
    # Формат ![имя](ссылка)
    r'!\[.*?\]\(https://drive\.google\.com/file/d/(.*?)/view\?(?:usp=sharing|usp=drive_link)\)\.?',
    
    # Формат [AI отправляет фото: \n]
    r'\[AI отправляет фото:[ \t\r\n]*\]\.?',
    
    # Формат [AI отправляет фото:]
    r'\[AI отправляет фото:[ \t\r\n]*\]?\.?',
]

# Паттерны для очистки служебных сообщений
service_patterns = [
    r'\*\*СЦЕНА \d+:.*?\*\*\n*',      # **СЦЕНА 1: ...**
    r'\*\*Описание:\*\*\n*',          # **Описание:**
    r'Инициализация:.*?\n',           # Инициализация: ...
    r'---\n*',                        # Разделители
    r'Цель достигнута:.*?\n',         # Цель достигнута: ...
    r'### СЦЕНА.*?\n',                # ### СЦНА ...
    r'СЦЕНА \d+:.*?\n',               # СЦЕНА 1: ...
    r'### Переход к.*?сцен[еу].*?\n', # ### Переход к сцене ...
    r'### ФИНАЛЬНАЯ СЦЕНА:.*?\n',     # ### ФИНАЛЬНАЯ СЦЕНА: ...
    r'^\d+\.\s+(?=[А-Я])',           # 1. Начало предложения
    r'Шаг \d+\..*?\n',                # Шаг 1. ...
    r'Теперь мы готовы начать!.*?\n', # Теперь мы готовы начать!
    r'["""]Развитие сцены["""]:\s*\n*',  # Учитываем переносы строк после двоеточия
    r'Развитие сцены:\s*\n*',            # Вариант без кавычек
    r'\*\*Развитие сцены\*\*:\s*\n*',    # Вариант с звездочками
    r'\[Описание:[ \t\r\n]*',         # [Описание:
    r'\][ \t\r\n]*$',                 # Закрывающая скобка в конце
    r'!\[.*?\]\(',                    # Очистка markdown разметки изображений
    r'\)[ \t\r\n]*',                  # Закрывающая скобка изображения
    r'\[\s*AI.*?\]\.?',                  # [AI ...] с возможными пробелами и точкой
    r'\[.*?AI.*?\]\.?',                  # [...AI...] - любой текст с AI внутри и точкой
    r'functions\.[a-zA-Z_][a-zA-Z0-9_]*\(.*?\)',   # Любые вызовы функций
]

def clean_assistant_message(text: str) -> str:
    """
    Очищает сообщение ассистента от ссылок и служебных пометок,
    возвращая только чистый текст для сохранения в базе
    """
    try:
        messages = extract_images_and_clean_text(text)
        clean_text_parts = []
        
        for msg in messages:
            if isinstance(msg, tuple):
                text_part, _ = msg
                if text_part:
                    clean_text_parts.append(text_part)
                
        result = "\n".join(clean_text_parts)
        return result if result else text
    except Exception:
        return text

def extract_images_and_clean_text(text: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """
    Извлекает изображения и очищает текст, возвращая список кортежей (текст, image_id).
    """
    if not text:
        return []
        
    result = []
    remaining_text = text
    
    while remaining_text:
        # Ищем первое изображение
        image_match = None
        image_start = len(remaining_text)
        image_end = image_start
        image_id = None
        
        # Проверяем все паттерны изображений
        for pattern in image_patterns:
            match = re.search(pattern, remaining_text)
            if match and (match.start() < image_start):
                image_match = match
                image_start = match.start()
                image_end = match.end()
                image_id = match.group(1)
        
        if image_match:
            # Обрабатываем текст до изображения
            text_before = remaining_text[:image_start]
            if text_before:
                clean_text = clean_text_content(text_before, service_patterns)
                if clean_text:
                    result.append((clean_text, None))
            
            # Добавляем изображение
            result.append((None, image_id))
            
            # Обновляем оставшийся текст
            remaining_text = remaining_text[image_end:].strip()
        else:
            # Если изображений больше нет, обрабатываем весь оставшийся текст
            clean_text = clean_text_content(remaining_text, service_patterns)
            if clean_text:
                result.append((clean_text, None))
            remaining_text = ""
    
    return result if result else [(text, None)]

def clean_text_content(text: str, service_patterns: List[str]) -> Optional[str]:
    """Очищает текст от служебных паттернов."""
    try:
        cleaned = text
        
        # Очищаем от служебных паттернов
        for pattern in service_patterns:
            # Добавляем флаги re.DOTALL для обработки переносов строк
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.DOTALL)
        
        cleaned = cleaned.strip()
        return cleaned if cleaned else None
    except Exception:
        return text
