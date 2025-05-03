from sqlalchemy.orm import Session
from app.db import models
from app.core import security # Import security utils
from app.schemas import UserCreate # Import UserCreate schema
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional

# === User CRUD Functions ===

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Gets a user by their ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Gets a user by their username."""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: UserCreate) -> models.User:
    """Creates a new user in the database."""
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# === Updated Conversation/Message CRUD ===

def get_or_create_conversation(db: Session, user_id: int, conversation_id: Optional[int] = None) -> models.Conversation:
    """
    Gets an existing conversation for a user, or creates a new one if ID is None or doesn't exist/belong to user.
    """
    if conversation_id:
        # Ensure the conversation exists AND belongs to the current user
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == conversation_id, models.Conversation.user_id == user_id)\
            .first()
        if conversation:
            return conversation
    # If no ID provided, or conversation not found for this user, create a new one
    new_conversation = models.Conversation(user_id=user_id) # Associate with the user
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

def add_message(db: Session, conversation_id: int, sender: str, text: str) -> models.Message:
    """Adds a message to a conversation. (No change needed here unless adding user_id to messages)"""
    db_message = models.Message(
        conversation_id=conversation_id,
        sender=sender,
        text=text
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_for_conversation(db: Session, user_id: int, conversation_id: int, limit: int = 50) -> List[BaseMessage]:
    """
    Gets the last N messages for a specific conversation owned by the user.
    """
    # Verify the conversation belongs to the user first (important!)
    conversation = db.query(models.Conversation)\
        .filter(models.Conversation.id == conversation_id, models.Conversation.user_id == user_id)\
        .first()

    if not conversation:
        return [] # Or raise an exception if preferred

    db_messages = db.query(models.Message)\
        .filter(models.Message.conversation_id == conversation_id)\
        .order_by(models.Message.timestamp.desc())\
        .limit(limit)\
        .all()

    # Convert to LangChain message format
    langchain_messages = []
    for msg in reversed(db_messages):
        if msg.sender.lower() == 'user':
            langchain_messages.append(HumanMessage(content=msg.text))
        elif msg.sender.lower() == 'ai':
            langchain_messages.append(AIMessage(content=msg.text))
    return langchain_messages

def get_user_conversations(db: Session, user_id: int) -> List[models.Conversation]:
     """Gets all conversations for a user."""
     return db.query(models.Conversation).filter(models.Conversation.user_id == user_id).order_by(models.Conversation.created_at.desc()).all()