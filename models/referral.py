from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import Index

from .base import Base

class ReferralLink(Base):
    """Model for storing referral links"""
    __tablename__ = 'referral_links'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)  # Индекс для быстрого поиска
    code = Column(String(16), unique=True, nullable=False)  # Ограничиваем длину кода
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с рефералами
    referrals = relationship("Referral", back_populates="link", lazy="selectin")

    # Индекс для быстрого поиска по коду
    __table_args__ = (
        Index('ix_referral_links_code', 'code'),
    )

class Referral(Base):
    """Model for tracking referral relationships"""
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey('referral_links.user_id'), index=True)
    referred_id = Column(Integer, nullable=False, index=True)
    link_id = Column(Integer, ForeignKey('referral_links.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reward_claimed = Column(Boolean, default=False)
    
    # Связь с реферальной ссылкой
    link = relationship("ReferralLink", back_populates="referrals", lazy="selectin")

    # Уникальный индекс, чтобы пользователь мог быть приглашен только один раз
    __table_args__ = (
        Index('ix_referrals_unique_referred', 'referred_id', unique=True),
    )

class ReferralReward(Base):
    """Model for tracking referral rewards"""
    __tablename__ = 'referral_rewards'

    id = Column(Integer, primary_key=True)
    referral_id = Column(Integer, ForeignKey('referrals.id'), unique=True)
    user_id = Column(Integer, nullable=False, index=True)  # Кто получил награду
    reward_type = Column(String(32), nullable=False)  # Тип награды (например, "chapter_unlock")
    reward_data = Column(String(255))  # Дополнительные данные о награде (например, номер главы)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Индекс для быстрого поиска наград пользователя
    __table_args__ = (
        Index('ix_referral_rewards_user_id_type', 'user_id', 'reward_type'),
    )