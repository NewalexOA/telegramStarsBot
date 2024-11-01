from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship

from models.base import Base
from models.enums import RewardType

class ReferralLink(Base):
    """Model for storing referral links"""
    __tablename__ = "referral_links"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True, unique=True)
    code = Column(String(16), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    referrals = relationship("Referral", back_populates="link")

class Referral(Base):
    """Model for tracking referrals"""
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, nullable=False, index=True)
    referred_id = Column(Integer, nullable=False, unique=True)
    link_id = Column(Integer, ForeignKey('referral_links.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    link = relationship("ReferralLink", back_populates="referrals")
    reward = relationship("ReferralReward", back_populates="referral", uselist=False)

class PendingReferral(Base):
    """Model for storing pending referrals until subscription"""
    __tablename__ = "pending_referrals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    ref_code = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_pending_referrals_user_created', 'user_id', 'created_at'),
    )

class ReferralReward(Base):
    """Model for tracking referral rewards"""
    __tablename__ = 'referral_rewards'

    id = Column(Integer, primary_key=True)
    referral_id = Column(Integer, ForeignKey('referrals.id'), unique=True)
    user_id = Column(Integer, nullable=False, index=True)
    reward_type = Column(String(32), nullable=False)
    reward_data = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referral = relationship("Referral", back_populates="reward")

    def get_reward_type(self) -> RewardType:
        return RewardType(self.reward_type)

    __table_args__ = (
        Index('ix_referral_rewards_user_id_type', 'user_id', 'reward_type'),
    )