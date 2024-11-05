from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from models.base import Base

class NovelState(Base):
    """Model for storing novel state"""
    __tablename__ = "novel_states"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    thread_id = Column(String(255), nullable=False)
    current_scene = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)  # Флаг завершения новеллы
    completions_count = Column(Integer, default=0)  # Счетчик завершений
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связь с сообщениями
    messages = relationship("NovelMessage", back_populates="novel_state", cascade="all, delete-orphan")

class NovelMessage(Base):
    """Model for storing novel messages"""
    __tablename__ = "novel_messages"
    
    id = Column(Integer, primary_key=True)
    novel_state_id = Column(Integer, ForeignKey('novel_states.id'), nullable=False)
    is_user = Column(Boolean, default=False)  # True если сообщение от пользователя
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с состоянием новеллы
    novel_state = relationship("NovelState", back_populates="messages") 