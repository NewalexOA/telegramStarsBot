import re
from typing import List, Tuple, Optional


def clean_assistant_message(text: str) -> str:
    """
    Очищает сообщение ассистента от ссылок и служебных пометок,
    возвращая только чистый текст для сохранения в базе
    """
    messages = extract_images_and_clean_text(text)
    clean_text_parts = []
    
    for msg in messages:
        if isinstance(msg, tuple):
            text_part, _ = msg
            if text_part:
                clean_text_parts.append(text_part)
        elif isinstance(msg, str):
            clean_text_parts.append(msg)
            
    return "\n".join(clean_text_parts)

def extract_images_and_clean_text(text: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """Извлекает изображения и очищает текст, возвращая список кортежей (текст, image_id)."""
    image_patterns = [
        # Формат [AI отправляет фото: ![название](ссылка)]
        r'\[AI отправляет фото:.*?https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing\]',
        # Формат [AI отправляет фото: ссылка]
        r'\[AI отправляет фото:.*?https://drive\.google\.com/file/d/(.*?)/view\?usp=drive_link\]',
        # Просто ссылка
        r'https://drive\.google\.com/file/d/(.*?)/view\?usp=drive_link',
        # Другие форматы ссылок
        r'https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing'
    ]
    
    service_patterns = [
        r'\*\*СЦЕНА \d+:.*?\*\*\n*',
        r'\*\*Описание:\*\*\n*',
        r'Инициализация:.*?\n',
        r'---\n*',
        r'Цель достигнута:.*?\n',
        r'### СЦЕНА.*?\n',
        r'### Переход к.*?сцен[еу].*?\n',
        r'### ФИНАЛЬНАЯ СЦЕНА:.*?\n',
        r'^\d+\.\s+(?=[А-Я])',
        r'Шаг \d+\..*?\n',
        r'Теперь мы готовы начать!.*?\n',
        r'\[AI отправляет фото:[ \t\r\n]*',
        r'^\[Описание:[ \t]*',  # Добавляем паттерн для начала описания
        r'\][ \t]*$',  # Добавляем паттерн для конца описания
    ]
    
    messages = []
    current_text = []
    lines = text.split('\n')
    
    for line in lines:
        # Проверяем, содержит ли строка изображение
        image_id = None
        for pattern in image_patterns:
            match = re.search(pattern, line)
            if match:
                image_id = match.group(1)
                break
        
        if image_id:
            # Если есть накопленный текст, добавляем его
            if current_text:
                clean_text = clean_text_content('\n'.join(current_text), service_patterns)
                if clean_text:
                    messages.append((clean_text, None))
                current_text = []
            # Добавляем изображение
            messages.append((None, image_id))
        else:
            current_text.append(line)
    
    # Добавляем оставшийся текст
    if current_text:
        clean_text = clean_text_content('\n'.join(current_text), service_patterns)
        if clean_text:
            messages.append((clean_text, None))
    
    return messages

def clean_text_content(text: str, service_patterns: List[str]) -> Optional[str]:
    """Очищает текст от служебных паттернов."""
    # Сначала обрабатываем многострочные квадратные скобки
    cleaned = re.sub(r'^\[(?:Описание:)?[ \t]*(.*?)\][ \t]*$', r'\1', text, flags=re.DOTALL)
    
    # Очищаем от остальных служебных паттернов
    for pattern in service_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
    
    # Очищаем от markdown и лишних пробелов
    cleaned = re.sub(r'\*\*', '', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned if cleaned else None
