from utils.text_utils import extract_images_and_clean_text

def test_remove_ai_photo_text():
    text = """4. Максим — друг детства Кати, старший брат Иры. Работает тренером в Зареченске. 
    Все детство был как старший брат для Иры и Кати, но недавно понял, что Ира ему нравится, 
    но боится признаться. Он стабилен, привязан к городу и не хочет, чтобы Ира уехала.

    AI отправляет фото:"""
    
    cleaned_text, _ = extract_images_and_clean_text(text)
    assert "AI отправляет фото:" not in cleaned_text 