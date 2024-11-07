from typing import List, Union, Optional
from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_reader import get_config, BotConfig
from keyboards.confirm import get_confirm_keyboard
from keyboards.admin import get_admin_button_data

class KeyboardFactory:
    """Универсальный конструктор клавиатур"""
    
    def __init__(self):
        self.bot_config = get_config(BotConfig, "bot")
        
    def _get_novel_buttons(self, has_active_novel: bool) -> List[List[Union[KeyboardButton, InlineKeyboardButton]]]:
        """Получить кнопки для новеллы"""
        if has_active_novel:
            return [[
                KeyboardButton(text="📖 Продолжить"),
                KeyboardButton(text="🔄 Рестарт")
            ]]
        return [[KeyboardButton(text="🎮 Новелла")]]

    def _get_common_buttons(self) -> List[List[Union[KeyboardButton, InlineKeyboardButton]]]:
        """Получить общие кнопки"""
        return [
            [
                KeyboardButton(text="💝 Донат"),
                KeyboardButton(text="❓ Помощь")
            ],
            [KeyboardButton(text="🔗 Реферальная ссылка")]
        ]

    def _get_admin_buttons(self, inline: bool = False) -> List[List[Union[KeyboardButton, InlineKeyboardButton]]]:
        """Получить админские кнопки"""
        buttons = []
        for button_data in get_admin_button_data():
            if inline:
                buttons.append(InlineKeyboardButton(
                    text=button_data['text'],
                    callback_data=button_data['callback']
                ))
            else:
                buttons.append(KeyboardButton(text=button_data['text']))
        return [buttons]  # Возвращаем как строку кнопок

    def _get_subscription_buttons(self) -> List[List[InlineKeyboardButton]]:
        """Получить кнопки подписки"""
        return [[
            InlineKeyboardButton(
                text="📚 Подписаться на канал",
                url=self.bot_config.required_channel_invite
            )
        ], [
            InlineKeyboardButton(
                text="🔄 Проверить подписку",
                callback_data="check_subscription"
            )
        ]]

    def create_keyboard(
        self,
        keyboard_type: str = "reply",
        is_admin: bool = False,
        is_subscribed: bool = False,
        has_active_novel: bool = False,
        resize_keyboard: bool = True,
        input_field_placeholder: Optional[str] = None
    ) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
        """
        Создать клавиатуру на основе параметров
        
        :param keyboard_type: тип клавиатуры ("reply" или "inline")
        :param is_admin: является ли пользователь админом
        :param is_subscribed: подписан ли пользователь
        :param has_active_novel: есть ли активная новелла
        :param resize_keyboard: изменять ли размер клавиатуры
        :param input_field_placeholder: подсказка в поле ввода
        """
        if keyboard_type == "inline":
            kb = InlineKeyboardBuilder()
            
            if not is_subscribed:
                for row in self._get_subscription_buttons():
                    for button in row:
                        kb.add(button)
            else:
                kb.button(
                    text="🎮 Запустить новеллу",
                    callback_data="start_novel"
                )
                if is_admin:
                    for row in self._get_admin_buttons(inline=True):
                        for button in row:
                            kb.add(button)
            
            kb.adjust(1)  # Кнопки в столбик
            return kb.as_markup()
        
        else:  # reply keyboard
            buttons = []
            
            if is_subscribed:
                buttons.extend(self._get_novel_buttons(has_active_novel))
                buttons.extend(self._get_common_buttons())
                if is_admin:
                    buttons.extend(self._get_admin_buttons())
            
            return ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=resize_keyboard,
                input_field_placeholder=input_field_placeholder
            ) 

    def create_confirm_keyboard(self, action: str) -> InlineKeyboardMarkup:
        """Создает клавиатуру подтверждения"""
        return get_confirm_keyboard(action)