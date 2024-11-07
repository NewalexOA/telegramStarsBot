from typing import List, Dict

class AdminKeyboardData:
    """Данные для админских кнопок"""
    STATS = {
        'text': "📊 Статистика",
        'callback': "admin_stats"
    }
    CLEAR_DB = {
        'text': "🗑 Очистить базу",
        'callback': "clear_db"
    }

def get_admin_button_data() -> List[Dict]:
    """
    Возвращает конфигурацию админских кнопок
    """
    return [AdminKeyboardData.STATS, AdminKeyboardData.CLEAR_DB] 