from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_tag = Column(String(255), nullable=True)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    status = Column(String(32), default="open")  # open | needs_agent | assigned | closed
    needs_agent = Column(Boolean, default=False)

    messages_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    support_count = Column(Integer, default=0)
    general_count = Column(Integer, default=0)
    low_conf_count = Column(Integer, default=0)

    last_category = Column(String(32), nullable=True)  # ventas | soporte | general | none

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" | "bot"
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
