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
from keyboards.menu import get_main_menu

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

class NovelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_novel_state(self, user_id: int) -> NovelState | None:
        """Получение состояния новеллы пользователя"""
        result = await self.session.execute(
            select(NovelState).where(NovelState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_novel_state(self, user_id: int) -> NovelState:
        """Создание нового состояния новеллы"""
        thread = await openai_client.beta.threads.create()
        novel_state = NovelState(
            user_id=user_id,
            thread_id=thread.id
        )
        self.session.add(novel_state)
        await self.session.commit()
        return novel_state

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
            if not initial_message:
                # Проверяем, не является ли сообщение командой или служебным текстом
                text = message.text
                if text.startswith('/') or text in ["🎮 Новелла", "📖 Продолжить", "🔄 Рестарт", "💝 Донат", "❓ Помощь"]:
                    return
                
                # Получаем последние сообщения треда для проверки финальной сцены
                messages = await openai_client.beta.threads.messages.list(
                    thread_id=novel_state.thread_id
                )
                
                # Проверяем, не была ли достигнута финальная сцена или конец истории
                if messages.data and ("Финальная сцена:" in messages.data[0].content[0].text.value or 
                                    "Конец истории" in messages.data[0].content[0].text.value):
                    await self.end_story(novel_state, message)
                    return
                
                # Сохраняем сообщение пользователя
                await self.save_message(novel_state, text, is_user=True)
                
                # Добавляем сообщение пользователя в тред
                await openai_client.beta.threads.messages.create(
                    thread_id=novel_state.thread_id,
                    role="user",
                    content=text
                )
                
                # Проверяем, является ли это первым ответом (имя)
                if len(messages.data) == 2:  # Первый вопрос и первый ответ
                    logger.info("Sending character introduction prompt")
                    await openai_client.beta.threads.messages.create(
                        thread_id=novel_state.thread_id,
                        role="user",
                        content=f"""Теперь представь персонажей, строго следуя формату из сценария, и только после этого начни первую сцену. 
                        
                        ВАЖНО: Замени все упоминания "Игрок", "Саша" и подобные на имя игрока "{text}". История должна быть полностью персонализирована под это имя.
                        
                        Каждый персонаж должен быть представлен с фотографией на отдельной строке в формате [AI отправляет фото: ![название](ссылка)]"""
                    )

            # Запускаем выполнение
            start_time = time.time()
            run = await openai_client.beta.threads.runs.create(
                thread_id=novel_state.thread_id,
                assistant_id=bot_config.assistant_id
            )
            logger.info(f"Started run {run.id}")

            # Ждём завершения выполнения
            while True:
                run_status = await openai_client.beta.threads.runs.retrieve(
                    thread_id=novel_state.thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    logger.info(f"Run completed in {time.time() - start_time:.2f} seconds")
                    break
                elif run_status.status == 'requires_action':
                    # Обрабатываем вызов функции end_story
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    
                    for tool_call in tool_calls:
                        if tool_call.function.name == "end_story":
                            await self.end_story(novel_state, message)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": "Story ended successfully"
                            })
                    
                    # Отправляем результаты выполнения функций
                    await openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=novel_state.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status == 'failed':
                    logger.error(f"Run failed: {run_status.last_error}")
                    raise Exception("Assistant run failed")
                await asyncio.sleep(1)

            # Получаем и сохраняем ответ ассистента
            messages = await openai_client.beta.threads.messages.list(
                thread_id=novel_state.thread_id
            )
            assistant_message = messages.data[0].content[0].text.value
            
            # Логируем сырой ответ и результаты обработки
            logger.info(f"Raw assistant response:\n{assistant_message}")
            cleaned_text, image_ids = extract_images_and_clean_text(assistant_message)
            logger.info(f"Found image IDs: {image_ids}")
            logger.info(f"Cleaned text:\n{cleaned_text}")
            
            # Сохраняем очищенный текст, если это не служебное сообщение
            if not any(pattern in cleaned_text.lower() for pattern in [
                "у вас уже есть активная новелла",
                "пожалуйста, нажмите кнопку",
                "произошла ошибка",
                "история завершена",
                "спасибо за подписку"
            ]):
                await self.save_message(novel_state, cleaned_text)
            
            # Отправляем ответ пользователю
            await send_assistant_response(message, assistant_message)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await message.answer("Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз.")

    async def end_story(self, novel_state: NovelState, message: Message, silent: bool = False) -> None:
        """Завершает новеллу и очищает данные"""
        try:
            # Увеличиваем счетчик завершений
            novel_state.completions_count += 1
            novel_state.is_completed = True
            await self.session.commit()
            
            # Удаляем тред в OpenAI
            try:
                await openai_client.beta.threads.delete(thread_id=novel_state.thread_id)
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