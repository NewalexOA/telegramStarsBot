import pytest
from utils.referral import create_ref_link, get_user_ref_link


@pytest.mark.asyncio
async def test_create_ref_link(db_session):
    """Test referral link creation"""
    async with db_session.begin():
        user_id = 123456
        ref_link = await create_ref_link(db_session, user_id)
        await db_session.flush()
        
        assert ref_link.user_id == user_id
        assert len(ref_link.code) == 8

@pytest.mark.asyncio
async def test_get_user_ref_link(db_session):
    """Test getting user's referral link"""
    # Создаем уникального пользователя для этого теста
    user_id = 999999  # Используем другой user_id чтобы избежать конфликтов
    
    # Создаем ссылку в одной транзакции
    async with db_session.begin():
        created_link = await create_ref_link(db_session, user_id)
        await db_session.flush()
    
    # Получаем ссылку в другой транзакции
    async with db_session.begin():
        fetched_link = await get_user_ref_link(db_session, user_id)
        
        assert fetched_link is not None
        assert fetched_link.id == created_link.id
        assert fetched_link.code == created_link.code
