from typing import Optional
import asyncio
import time
import structlog
from aiogram.types import Message
from unit_of_work.unit_of_work import UnitOfWork
from models.novel import NovelState, NovelMessage
from utils.openai_helper import openai_client, send_assistant_response
from utils.text_utils import extract_images_and_clean_text
from keyboards.menu import get_main_menu
from config_reader import get_config, BotConfig

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

# Константы
SKIP_COMMANDS = {
    "🎮 Новелла", "📖 Продолжить", "🔄 Рестарт", 
    "💝 Донат", "❓ Помощь", "🔗 Реферальная ссылка",
    "📊 Статистика", "🗑 Очистить базу"
}

class NovelService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.openai_client = openai_client
        
    async def get_novel_state(self, user_id: int) -> Optional[NovelState]:
        """Получение состояния новеллы пользователя"""
        async with self.uow as uow:
            return await uow.novels.get_by_user_id(user_id)
    
    async def create_novel_state(self, user_id: int) -> Optional[NovelState]:
        """Создает новое состояние новеллы"""
        async with self.uow as uow:
            try:
                # Проверяем старое состояние
                old_state = await uow.novels.get_by_user_id(user_id)
                if old_state and old_state.needs_payment:
                    logger.info(f"Blocked novel creation - payment required for user {user_id}")
                    return None
                
                # Удаляем старое состояние если есть
                if old_state:
                    try:
                        if old_state.thread_id:
                            await self.openai_client.beta.threads.delete(thread_id=old_state.thread_id)
                    except Exception as e:
                        logger.error(f"Error deleting thread: {e}")
                    
                    await uow.novels.delete(old_state.id)
                
                # Создаем новый тред с повторными попытками
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        thread = await self.openai_client.beta.threads.create()
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(1)
                
                # Создаем новое состояние
                novel_state = await uow.novels.create(
                    user_id=user_id,
                    thread_id=thread.id,
                    current_scene=0,
                    is_completed=False,
                    needs_payment=False
                )
                await uow.commit()
                
                return novel_state
                
            except Exception as e:
                logger.error(f"Error creating novel state: {e}")
                await uow.rollback()
                raise
    
    async def process_message(self, message: Message, novel_state: NovelState, initial_message: bool = False) -> None:
        """Обработка сообщения пользователя"""
        try:
            # Проверяем существование треда
            try:
                thread = await self.openai_client.beta.threads.retrieve(thread_id=novel_state.thread_id)
                if not thread:
                    raise Exception("Thread not found")
            except Exception as e:
                logger.error(f"Thread validation failed: {e}")
                thread = await self.openai_client.beta.threads.create()
                async with self.uow as uow:
                    novel_state.thread_id = thread.id
                    await uow.commit()
                logger.info(f"Created new thread: {thread.id}")

            text = message.text
            logger.info(f"Processing message: {text}")

            if initial_message:
                await self._handle_initial_message(novel_state)
            else:
                await self._handle_regular_message(message, novel_state, text)

            # Получаем и обрабатываем ответ
            assistant_message = await self._process_assistant_response(novel_state)
            
            # Сохраняем и отправляем ответ
            await self._save_and_send_response(message, novel_state, assistant_message)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await message.answer("Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз.")

    async def _handle_initial_message(self, novel_state: NovelState) -> None:
        """Обработка первого сообщения"""
        await self.openai_client.beta.threads.messages.create(
            thread_id=novel_state.thread_id,
            role="user",
            content="Начни с шага '0. Инициализация:' и спроси моё имя."
        )
        logger.info("Sent initial prompt")

    async def _handle_regular_message(self, message: Message, novel_state: NovelState, text: str) -> None:
        """Обработка обычного сообщения"""
        # Сохраняем сообщение пользователя
        await self.save_message(novel_state, text, is_user=True)
        
        # Получаем список сообщений из треда
        messages = await self.openai_client.beta.threads.messages.list(
            thread_id=novel_state.thread_id
        )
        
        # Если это второе сообщение (после инициализации), обрабатываем как имя
        if len(messages.data) == 2:
            await self._handle_name_response(novel_state, text)
        else:
            # Иначе отправляем обычное сообщение в тред
            await self.openai_client.beta.threads.messages.create(
                thread_id=novel_state.thread_id,
                role="user",
                content=text
            )

    async def _handle_name_response(self, novel_state: NovelState, name: str) -> None:
        """Обработка ответа с именем"""
        character_prompt = f"""Теперь представь персонажей, строго следуя формату из сценария, и только после этого начни первую сцену. 
        
        ВАЖНО: Замени все упоминания "Игрок", "Саша" и подобные на имя игрока "{name}". История должна быть полностью персонализирована под это имя.
        
        Каждый персонаж должен быть представлен с фотографией на отдельной строке в формате [AI отправляет фото: ![название](ссылка)]"""
        
        await self.openai_client.beta.threads.messages.create(
            thread_id=novel_state.thread_id,
            role="user",
            content=character_prompt
        )
        logger.info("Sent character introduction prompt")

    async def _process_assistant_response(self, novel_state: NovelState) -> str:
        """Обработка ответа ассистента"""
        run = await self.openai_client.beta.threads.runs.create(
            thread_id=novel_state.thread_id,
            assistant_id=bot_config.assistant_id
        )
        
        start_time = time.time()
        while True:
            run = await self.openai_client.beta.threads.runs.retrieve(
                thread_id=novel_state.thread_id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            elif run.status == "failed":
                raise Exception("Assistant run failed")
            elif time.time() - start_time > 30:
                raise Exception("Assistant run timeout")
            await asyncio.sleep(1)
            
        messages = await self.openai_client.beta.threads.messages.list(
            thread_id=novel_state.thread_id
        )
        return messages.data[0].content[0].text.value

    async def _save_and_send_response(self, message: Message, novel_state: NovelState, assistant_message: str) -> None:
        """Сохранение и отправка ответа"""
        cleaned_text, image_ids = extract_images_and_clean_text(assistant_message)
        
        async with self.uow as uow:
            await self.save_message(novel_state, cleaned_text, is_user=False)
            await uow.commit()
            
        await send_assistant_response(message, assistant_message)

    async def end_story(self, novel_state: NovelState, message: Message, silent: bool = False) -> None:
        """Завершает новеллу и очищает данные"""
        try:
            async with self.uow as uow:
                novel_state.needs_payment = True
                novel_state.is_completed = True
                await uow.commit()
            
            try:
                await self.openai_client.beta.threads.delete(thread_id=novel_state.thread_id)
            except Exception as e:
                logger.error(f"Error deleting thread: {e}")
            
            if not silent:
                await message.answer(
                    "История завершена! Чтобы начать новую, нажмите '🎮 Новелла'",
                    reply_markup=get_main_menu(has_active_novel=False)
                )
                
        except Exception as e:
            logger.error(f"Error ending story: {e}")
            if not silent:
                await message.answer("Произошла ошибка при завершении истории")

    async def save_message(self, novel_state: NovelState, content: str, is_user: bool = False) -> NovelMessage:
        """Сохранение сообщения в базу данных"""
        async with self.uow as uow:
            message = await uow.novel_messages.create(
                novel_state_id=novel_state.id,
                content=content,
                is_user=is_user
            )
            await uow.commit()
            return message

    async def get_last_assistant_message(self, novel_state: NovelState) -> Optional[str]:
        """Получение последнего сообщения ассистента"""
        try:
            async with self.uow as uow:
                # Получаем последнее сообщение ассистента из базы
                last_message = await uow.novel_messages.get_last_assistant_message(
                    novel_state_id=novel_state.id
                )
                if last_message:
                    return last_message.content
                
                # Если в базе нет сообщений, пробуем получить из OpenAI
                try:
                    messages = await self.openai_client.beta.threads.messages.list(
                        thread_id=novel_state.thread_id
                    )
                    if messages.data:
                        return messages.data[0].content[0].text.value
                except Exception as e:
                    logger.error(f"Error getting messages from OpenAI: {e}")
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting last assistant message: {e}")
            return None