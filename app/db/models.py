import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Link to the User who owns this conversation
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Added user_id FK
    user = relationship("User", back_populates="conversations") # Added relationship back

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class User(Base): # New User Model
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True) # Optional email
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True) # Optional: for disabling users
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to conversations initiated by this user
    conversations = relationship("Conversation", back_populates="user")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'ai'
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")