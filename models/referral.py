from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class ReferralLink(Base):
    __tablename__ = 'referral_links'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # ID пользователя, создавшего ссылку
    code = Column(String, unique=True, nullable=False)  # Уникальный код для ссылки
    created_at = Column(DateTime, server_default=func.now())
    referrals = relationship("Referral", back_populates="link")

class Referral(Base):
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey('referral_links.user_id'))  # Кто пригласил
    referred_id = Column(Integer, nullable=False)  # Кого пригласили
    link_id = Column(Integer, ForeignKey('referral_links.id'))
    created_at = Column(DateTime, server_default=func.now())
    reward_claimed = Column(Boolean, default=False)  # Получена ли награда
    link = relationship("ReferralLink", back_populates="referrals") 