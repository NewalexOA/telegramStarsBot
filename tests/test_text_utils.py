from utils.text_utils import extract_images_and_clean_text

def test_remove_ai_photo_text():
    text = """4. Максим — друг детства Кати, старший брат Иры. Работает тренером в Зареченске. 
    Все детство был как старший брат для Иры и Кати, но недавно понял, что Ира ему нравится, 
    но боится признаться. Он стабилен, привязан к городу и не хочет, чтобы Ира уехала.

    AI отправляет фото:"""
    
    messages = extract_images_and_clean_text(text)
    # Проверяем, что в первом сообщении нет "AI отправляет фото:"
    assert len(messages) > 0
    first_message = messages[0]
    assert isinstance(first_message, tuple)
    text, image_id = first_message
    assert "AI отправляет фото:" not in text

def test_clean_multiline_description():
    text = """[Описание: Анжела встречается с Катей в небольшом уютном кафе,
где они часто проводили время. Вечернее солнце мягко освещает их столик у окна,
и в этом спокойном месте, под лёгкий аромат кофе, Катя решает открыть свои переживания.]"""
    
    messages = extract_images_and_clean_text(text)
    assert len(messages) == 1
    cleaned_text, _ = messages[0]
    assert "[Описание:" not in cleaned_text
    assert "]" not in cleaned_text
    assert cleaned_text.startswith("Анжела встречается")