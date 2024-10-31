from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.referral import ReferralReward
from models.enums import RewardType

async def give_reward(
    session: AsyncSession,
    user_id: int,
    referral_id: int,
    reward_type: RewardType,
    reward_data: Optional[str] = None
) -> ReferralReward:
    """Выдать награду пользователю"""
    reward = ReferralReward(
        user_id=user_id,
        referral_id=referral_id,
        reward_type=reward_type.value,
        reward_data=reward_data
    )
    session.add(reward)
    await session.commit()
    return reward

async def process_reward(
    session: AsyncSession,
    reward: ReferralReward
) -> bool:
    """Обработать награду в зависимости от типа"""
    reward_type = reward.get_reward_type()
    
    if reward_type == RewardType.CHAPTER_UNLOCK:
        # Логика разблокировки главы
        chapter_number = int(reward.reward_data)
        # TODO: Разблокировать главу
        return True
        
    elif reward_type == RewardType.BONUS_STARS:
        # Логика начисления звезд
        stars_amount = int(reward.reward_data)
        # TODO: Начислить звезды
        return True
        
    elif reward_type == RewardType.SPECIAL_SCENE:
        # Логика доступа к специальной сцене
        scene_id = reward.reward_data
        # TODO: Открыть доступ к сцене
        return True
    
    return False

async def get_user_rewards(
    session: AsyncSession,
    user_id: int,
    reward_type: Optional[RewardType] = None
) -> list[ReferralReward]:
    """Получить все награды пользователя"""
    query = select(ReferralReward).where(ReferralReward.user_id == user_id)
    if reward_type:
        query = query.where(ReferralReward.reward_type == reward_type.value)
    result = await session.execute(query)
    return result.scalars().all() 