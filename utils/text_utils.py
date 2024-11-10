import re
from typing import Tuple, List

def extract_images_and_clean_text(text: str) -> Tuple[str, List[str]]:
    """Извлекает ссылки на изображения и очищает текст"""
    image_patterns = [
        r'\[AI отправляет фото:.*?https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing.*?\]',
        r'!\(https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing\)',
        r'\(https://drive\.google\.com/file/d/(.*?)/view\?usp=sharing\)',
        r'\(https://drive\.google\.com/file/d/(.*?)/view\?usp=drive_link\)',
        r'https://drive\.google\.com/file/d/(.*?)/view\?usp=drive_link'
    ]
    
    brackets_pattern = r'\[.*?\]|\]|\['
    service_patterns = [
        r'\*\*СЦЕНА \d+:.*?\*\*\n*',
        r'\*\*Описание:\*\*\n*',
        r'---\n*',
        r'Цель достигнута:.*?\n',
        r'### СЦЕНА.*?\n',
        r'^\d+\.\s+(?=[А-Я])',
        r'Теперь мы готовы начать!.*?\n',
        r'https://drive\.google\.com/file/d/.*?/view\?usp=drive_link',
        r'AI отправляет фото:'
    ]
    
    image_ids = set()
    cleaned_parts = []
    last_end = 0
    
    for pattern in image_patterns:
        matches = list(re.finditer(pattern, text))
        for match in matches:
            cleaned_parts.append(text[last_end:match.start()])
            image_ids.add(match.group(1))
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
    
    return cleaned_text, list(image_ids)