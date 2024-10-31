import random
import string
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.referral import ReferralLink, Referral

def generate_ref_code(length: int = 8) -> str:
    """Генерирует случайный реферальный код"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

async def create_ref_link(session: AsyncSession, user_id: int) -> ReferralLink:
    """Создает новую реферальную ссылку"""
    while True:
        code = generate_ref_code()
        # Проверяем, не существует ли уже такой код
        existing = await session.execute(
            select(ReferralLink).where(ReferralLink.code == code)
        )
        if not existing.scalar_one_or_none():
            break
    
    ref_link = ReferralLink(user_id=user_id, code=code)
    session.add(ref_link)
    await session.commit()
    return ref_link

async def get_user_ref_link(session: AsyncSession, user_id: int) -> Optional[ReferralLink]:
    """Получает реферальную ссылку пользователя"""
    result = await session.execute(
        select(ReferralLink).where(ReferralLink.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def process_referral(
    session: AsyncSession, 
    ref_code: str, 
    new_user_id: int
) -> Optional[Referral]:
    """Обрабатывает переход по реферальной ссылке"""
    # Находим ссылку по коду
    result = await session.execute(
        select(ReferralLink).where(ReferralLink.code == ref_code)
    )
    ref_link = result.scalar_one_or_none()
    if not ref_link or ref_link.user_id == new_user_id:
        return None
    
    # Создаем запись о реферале
    referral = Referral(
        referrer_id=ref_link.user_id,
        referred_id=new_user_id,
        link_id=ref_link.id
    )
    session.add(referral)
    await session.commit()
    return referral 