import asyncio
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message
from config_reader import get_config, BotConfig
import time

from models.novel import NovelState, NovelMessage
from utils.openai_helper import openai_client, send_assistant_response
from utils.text_utils import extract_images_and_clean_text
from keyboards.factory import KeyboardFactory

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")
keyboard_factory = KeyboardFactory()

# В начале файла
SKIP_COMMANDS = {
    "🎮 Новелла", "📖 Продолжить", "🔄 Рестарт", 
    "💝 Донат", "❓ Помощь", "🔗 Реферальная ссылка",
    "📊 Статистика", "🗑 Очистить базу"
}

class NovelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_novel_state(self, user_id: int) -> NovelState | None:
        """Получение состояния новеллы пользователя"""
        result = await self.session.execute(
            select(NovelState).where(NovelState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_novel_state(self, user_id: int) -> NovelState | None:
        """Создает новое состояние новеллы"""
        try:
            # Сначала получаем старое состояние
            old_state = await self.get_novel_state(user_id)
            
            # Если есть старое состояние и требуется оплата - запрещаем создание нового
            if old_state and old_state.needs_payment:
                logger.info(f"Blocked novel creation - payment required for user {user_id}")
                return None
                
            # Если есть старое состояние без требования оплаты - удаляем его
            if old_state:
                # Сначала удаляем тред в OpenAI
                try:
                    if old_state.thread_id:
                        await openai_client.beta.threads.delete(thread_id=old_state.thread_id)
                except Exception as e:
                    logger.error(f"Error deleting thread: {e}")
                    # Продолжаем выполнение даже при ошибке удаления
                    
                # Затем удаляем запись из БД
                await self.session.delete(old_state)
                await self.session.commit()
            
            # Создаем новый тред в OpenAI с повторными попытками
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    thread = await openai_client.beta.threads.create()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to create thread after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(1)
            
            # Создаем новое состояние
            novel_state = NovelState(
                user_id=user_id,
                thread_id=thread.id,
                current_scene=0,
                is_completed=False,
                needs_payment=False
            )
            
            self.session.add(novel_state)
            await self.session.commit()
            await self.session.refresh(novel_state)
            
            return novel_state
            
        except Exception as e:
            logger.error(f"Error creating novel state: {e}")
            await self.session.rollback()
            raise

    async def save_message(self, novel_state: NovelState, content: str, is_user: bool = False) -> NovelMessage:
        """Сохранение сообщения в базу"""
        message = NovelMessage(
            novel_state_id=novel_state.id,
            content=content,
            is_user=is_user
        )
        self.session.add(message)
        await self.session.commit()
        return message

    async def get_last_assistant_message(self, novel_state: NovelState) -> str | None:
        """Получение последнего сообщения ассистента"""
        result = await self.session.execute(
            select(NovelMessage)
            .where(
                NovelMessage.novel_state_id == novel_state.id,
                ~NovelMessage.is_user
            )
            .order_by(NovelMessage.created_at.desc())
            .limit(1)
        )
        message = result.scalar_one_or_none()
        return message.content if message else None

    async def process_message(self, message: Message, novel_state: NovelState, initial_message: bool = False) -> None:
        """Обработка сообщения пользователя"""
        try:
            # Проверяем существование треда
            try:
                thread = await openai_client.beta.threads.retrieve(novel_state.thread_id)
                logger.info(
                    "Retrieved thread",
                    thread_id=thread.id,
                    user_id=message.from_user.id
                )
            except Exception as e:
                logger.error(
                    "Error retrieving thread, creating new one",
                    error=str(e),
                    thread_id=novel_state.thread_id,
                    user_id=message.from_user.id
                )
                # Создаем новый тред если старый не существует
                thread = await openai_client.beta.threads.create()
                novel_state.thread_id = thread.id
                await self.session.commit()
                
            # Отправляем сообщение в тред
            if initial_message:
                content = "Начни с шага '0. Инициализация:' и спроси моё имя."
            else:
                content = message.text
                
            try:
                await openai_client.beta.threads.messages.create(
                    thread_id=thread.id,
                    content=content,
                    role="user"
                )
                logger.info(
                    "Message sent to thread",
                    thread_id=thread.id,
                    user_id=message.from_user.id
                )
            except Exception as e:
                logger.error(
                    "Error sending message to thread",
                    error=str(e),
                    thread_id=thread.id,
                    user_id=message.from_user.id
                )
                raise
                
            # Запускаем обработку
            run = await openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=bot_config.assistant_id
            )
            logger.info(
                "Started run",
                run_id=run.id,
                thread_id=thread.id,
                user_id=message.from_user.id
            )
            
            # Ожидаем завершения
            start_time = time.time()
            while True:
                run = await openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run.status == "completed":
                    break
                elif run.status == "failed":
                    raise Exception("Assistant run failed")
                elif time.time() - start_time > 30:
                    raise Exception("Assistant run timeout")
                await asyncio.sleep(1)

            duration = time.time() - start_time
            logger.info(f"Run completed in {duration:.2f} seconds")

            # Получаем и обрабатываем ответ ассистента
            messages = await openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            assistant_message = messages.data[0].content[0].text.value
            
            logger.info(f"Raw assistant response:\n{assistant_message}")
            cleaned_text, image_ids = extract_images_and_clean_text(assistant_message)
            logger.info(f"Found image IDs: {image_ids}")
            logger.info(f"Cleaned text:\n{cleaned_text}")
            
            # Сохраняем ответ ассистента
            await self.save_message(novel_state, cleaned_text)
            logger.info("Assistant message saved to database")
            
            # Отправляем ответ пользователю
            await send_assistant_response(message, assistant_message)
            logger.info("Response sent to user")

        except Exception as e:
            logger.error(
                "Error processing message",
                error=str(e),
                user_id=message.from_user.id,
                thread_id=novel_state.thread_id if novel_state else None,
                exc_info=True
            )
            # Сбрасываем состояние при критической ошибке
            novel_state.needs_payment = True
            novel_state.is_completed = True
            await self.session.commit()
            await message.answer(
                "Произошла ошибка при обработке сообщения. Пожалуйста, начните новую новеллу."
            )

    async def end_story(self, novel_state: NovelState, message: Message, silent: bool = False) -> None:
        """Завершает новеллу и очищает данные"""
        try:
            # Устанавливаем флаг необходимости оплаты
            novel_state.needs_payment = True
            novel_state.is_completed = True
            await self.session.commit()
            
            # Удаляем тред в OpenAI
            try:
                await openai_client.beta.threads.delete(thread_id=novel_state.thread_id)
            except Exception as e:
                logger.error(f"Error deleting thread: {e}")
            
            if not silent:
                # Используем фабрику для создания клавиатуры
                keyboard = keyboard_factory.create_keyboard(
                    keyboard_type="reply",
                    is_subscribed=True,
                    has_active_novel=False
                )
                await message.answer(
                    "История завершена! Чтобы начать новую, нажмите '🎮 Новелла'",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error ending story: {e}")
            if not silent:
                await message.answer("Произошла ошибка при завершении истории")

    async def get_stats(self) -> dict:
        """
        Получает статистику по новеллам
        """
        logger.info("Getting novel statistics")
        try:
            # Получаем общее количество новелл
            total_novels_query = select(NovelState)
            total_novels = len((await self.session.execute(total_novels_query)).all())

            # Получаем количество завершенных новелл
            completed_novels_query = select(NovelState).where(NovelState.is_completed is True)
            completed_novels = len((await self.session.execute(completed_novels_query)).all())

            # Получаем количество активных (незавершенных) новелл
            active_novels_query = select(NovelState).where(NovelState.is_completed is False)
            active_novels = len((await self.session.execute(active_novels_query)).all())

            # Получаем общее количество сообщений
            total_messages_query = select(NovelMessage)
            total_messages = len((await self.session.execute(total_messages_query)).all())

            logger.info(
                "Stats retrieved successfully",
                total_novels=total_novels,
                completed_novels=completed_novels,
                active_novels=active_novels,
                total_messages=total_messages
            )

            return {
                "total_novels": total_novels,
                "completed_novels": completed_novels,
                "active_novels": active_novels,
                "total_messages": total_messages
            }
        except Exception as e:
            logger.error(
                "Error getting stats",
                error=str(e)
            )
            raise