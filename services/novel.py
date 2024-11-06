import asyncio
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message
from config_reader import get_config, BotConfig
from typing import Optional

from models.novel import NovelState, NovelMessage
from utils.openai_helper import openai_client
from utils.text_utils import extract_images_and_clean_text
from keyboards.menu import get_main_menu

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

# В начале файла
SKIP_COMMANDS = {
    "🎮 Новелла", "📖 Продолжить", "🔄 Рестарт", 
    "💝 Донат", "❓ Помощь", "🔗 Реферальная ссылка",
    "📊 Статистика", "🗑 Очистить базу"
}

class NovelService:
    # Увеличиваем максимальное время ожидания
    MAX_WAIT_TIME = 60  # секунд
    MAX_RETRIES = 3     # количество попыток
    
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
        """Обработка сообщения через OpenAI Assistant"""
        try:
            # Проверяем, не является ли сообщение командой или кнопкой меню
            if message.text in SKIP_COMMANDS:
                return

            # Очищаем текст от изображений
            clean_text = await extract_images_and_clean_text(message.text)
            
            # Отправляем сообщение ассистенту
            response = await self._get_assistant_response(clean_text, novel_state)
            
            if response:
                # Проверяем на наличие маркеров финальной сцены
                is_final = any(marker in response.lower() for marker in [
                    "финальная сцена:",
                    "final scene:",
                    "### финальная сцена",
                    "### final scene"
                ])
                
                # Очищаем текст от служебных маркеров
                cleaned_response = response
                for marker in [
                    "### ФИНАЛЬНАЯ СЦЕНА:", 
                    "ФИНАЛЬНАЯ СЦЕНА:", 
                    "### Final Scene:", 
                    "Final Scene:"
                ]:
                    cleaned_response = cleaned_response.replace(marker, "").strip()
                
                # Отправляем очищенный ответ
                await message.answer(cleaned_response)
                
                # Если это финальная сцена, завершаем новеллу
                if is_final:
                    await logger.ainfo("Final scene detected, ending story")
                    await self.end_story(novel_state, message)
                    return
                    
            else:
                await message.answer("Произошла ошибка при обработке сообщения")
                
        except Exception as e:
            await logger.aerror("Error processing message", error=str(e))
            await message.answer("Произошла ошибка при обработке сообщения")

    async def end_story(self, novel_state: NovelState, message: Message, silent: bool = False) -> None:
        """Завершает новеллу и очищает д��нные"""
        try:
            # Устанавливаем флаги в БД
            novel_state.needs_payment = True
            novel_state.is_completed = True
            try:
                await self.session.commit()
            except Exception as e:
                logger.error(f"Error saving novel state: {e}")
                raise
            
            # Удаляем тред в OpenAI
            if novel_state.thread_id:
                try:
                    await openai_client.beta.threads.delete(thread_id=novel_state.thread_id)
                except Exception as e:
                    logger.error(f"Error deleting OpenAI thread: {e}", 
                               thread_id=novel_state.thread_id)
                    # Не прерываем выполнение из-за ошибки удаления треда
            
            if not silent:
                await message.answer(
                    "История завершена! Чтобы начать новую, нажмите '🎮 Новелла'",
                    reply_markup=get_main_menu(has_active_novel=False)
                )
                
        except Exception as e:
            logger.error(f"Error ending story: {e}", exc_info=True)
            if not silent:
                await message.answer("Произошла ошибка при завершении истории")
            raise

    async def process_message_openai(self, message: str) -> Optional[str]:
        """Обработка сообщения через OpenAI Assistant"""
        logger = structlog.get_logger()
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Отправляем сообщение ассистенту
                await self.client.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content=message
                )
                
                # Запускаем обработку
                run = await self.client.runs.create(
                    thread_id=self.thread_id,
                    assistant_id=self.assistant_id
                )
                
                start_time = asyncio.get_event_loop().time()
                
                # Ожидаем завершения с периодической проверкой
                while True:
                    run = await self.client.runs.retrieve(
                        thread_id=self.thread_id,
                        run_id=run.id
                    )
                    
                    if run.status == "completed":
                        # Получаем ответ
                        messages = await self.client.messages.list(
                            thread_id=self.thread_id
                        )
                        return messages.data[0].content[0].text.value
                        
                    elif run.status == "failed":
                        await logger.aerror(
                            "Assistant run failed",
                            status=run.status,
                            last_error=run.last_error
                        )
                        break
                        
                    # Проверяем таймаут
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > self.MAX_WAIT_TIME:
                        await logger.awarning(
                            "Assistant run timeout",
                            attempt=attempt + 1,
                            elapsed_time=elapsed
                        )
                        break
                        
                    await asyncio.sleep(1)
                    
            except Exception as e:
                await logger.aerror(
                    "Error processing message",
                    error=str(e),
                    attempt=attempt + 1
                )
                
            # Если это была последняя попытка
            if attempt == self.MAX_RETRIES - 1:
                raise Exception(
                    f"Assistant run failed after {self.MAX_RETRIES} attempts"
                )
                
            # Делаем паузу перед следующей попыткой
            await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
            
        return None