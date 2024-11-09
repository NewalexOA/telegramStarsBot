from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Column, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from enum import Enum

class RewardType(str, Enum):
    """Types of referral rewards"""
    CHAPTER = "chapter"
    STARS = "stars"

class ReferralLink(Base):
    """Model for storing referral links"""
    __tablename__ = "referral_links"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь с рефералами
    referrals = relationship("Referral", back_populates="link", cascade="all, delete-orphan")

class Referral(Base):
    """Model for tracking referrals"""
    __tablename__ = "referrals"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("referral_links.id"))
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь с реферальной ссылкой
    link = relationship("ReferralLink", back_populates="referrals")
    reward = relationship("ReferralReward", back_populates="referral", uselist=False)

class PendingReferral(Base):
    """Model for storing pending referrals until subscription"""
    __tablename__ = "pending_referrals"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    ref_code: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    __table_args__ = (
        Index('ix_pending_referrals_user_created', 'user_id', 'created_at'),
    )

class ReferralReward(Base):
    """Model for tracking referral rewards"""
    __tablename__ = 'referral_rewards'

    id: Mapped[int] = mapped_column(primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey('referrals.id'), unique=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    reward_type: Mapped[str] = mapped_column(String(32))
    reward_data: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    referral = relationship("Referral", back_populates="reward")

    def get_reward_type(self) -> RewardType:
        return RewardType(self.reward_type)

    __table_args__ = (
        Index('ix_referral_rewards_user_id_type', 'user_id', 'reward_type'),
    )