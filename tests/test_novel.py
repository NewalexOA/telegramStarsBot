from typing import AsyncGenerator, Protocol
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message
from services.novel import NovelService
from models.novel import NovelState

# Определяем протокол для фикстуры
class NovelServiceFixture(Protocol):
    async def __call__(self, session: AsyncSession) -> NovelService: ...

class NovelStateFixture(Protocol):
    async def __call__(self, service: NovelService, message: Message) -> NovelState: ...

@pytest.fixture
async def novel_service(
    db_session: AsyncSession
) -> AsyncGenerator[NovelService, None]:
    """Фикстура для создания сервиса новеллы"""
    service = NovelService(db_session)
    yield service

@pytest.fixture
async def novel_state(
    novel_service: NovelService,
    message: Message
) -> AsyncGenerator[NovelState, None]:
    """Фикстура для создания состояния новеллы"""
    state = await novel_service.create_novel_state(message.from_user.id)
    yield state
    # Очистка после теста
    if state and state.thread_id:
        await novel_service.end_story(state, message, silent=True)

async def test_create_novel_state(
    novel_service: NovelService,
    message: Message
) -> None:
    """Тест создания состояния новеллы"""
    state = await novel_service.create_novel_state(message.from_user.id)
    assert state is not None
    assert state.user_id == message.from_user.id
    assert state.thread_id is not None
    assert state.current_scene == 0
    assert not state.is_completed
    assert not state.needs_payment

async def test_process_message(
    novel_service: NovelService,
    novel_state: NovelState,
    message: Message
) -> None:
    """Тест обработки сообщения"""
    test_message = "Тестовое сообщение"
    message.text = test_message
    
    await novel_service.process_message(message, novel_state)
    
    # Проверяем сохранение сообщения
    last_message = await novel_service.get_last_assistant_message(novel_state)
    assert last_message is not None

async def test_end_story(
    novel_service: NovelService,
    novel_state: NovelState,
    message: Message
) -> None:
    """Тест завершения новеллы"""
    await novel_service.end_story(novel_state, message, silent=True)
    
    assert novel_state.is_completed
    assert novel_state.needs_payment