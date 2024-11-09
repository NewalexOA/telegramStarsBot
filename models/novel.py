from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class NovelState(Base):
    """Model for storing novel state"""
    __tablename__ = "novel_states"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    thread_id: Mapped[str] = mapped_column(String)
    current_scene: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с сообщениями
    messages = relationship("NovelMessage", back_populates="novel_state", cascade="all, delete-orphan")

class NovelMessage(Base):
    """Model for storing novel messages"""
    __tablename__ = "novel_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    novel_state_id: Mapped[int] = mapped_column(ForeignKey("novel_states.id"))
    content: Mapped[str] = mapped_column(String)
    is_user: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь с состоянием новеллы
    novel_state = relationship("NovelState", back_populates="messages")