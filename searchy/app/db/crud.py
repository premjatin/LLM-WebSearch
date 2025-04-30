from sqlalchemy.orm import Session
from app.db import models
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional

def get_or_create_conversation(db: Session, conversation_id: Optional[int] = None) -> models.Conversation:
    """Gets an existing conversation or creates a new one."""
    if conversation_id:
        conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        if conversation:
            return conversation
    # If no ID provided or conversation not found, create a new one
    new_conversation = models.Conversation()
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

def add_message(db: Session, conversation_id: int, sender: str, text: str) -> models.Message:
    """Adds a message to a conversation."""
    db_message = models.Message(
        conversation_id=conversation_id,
        sender=sender,
        text=text
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_for_conversation(db: Session, conversation_id: int, limit: int = 50) -> List[BaseMessage]:
    """Gets the last N messages for a conversation, formatted for LangChain."""
    db_messages = db.query(models.Message)\
        .filter(models.Message.conversation_id == conversation_id)\
        .order_by(models.Message.timestamp.desc())\
        .limit(limit)\
        .all()

    # Convert to LangChain message format, maintaining order (oldest first)
    langchain_messages = []
    for msg in reversed(db_messages): # Reverse to get oldest first
        if msg.sender.lower() == 'user':
            langchain_messages.append(HumanMessage(content=msg.text))
        elif msg.sender.lower() == 'ai':
            langchain_messages.append(AIMessage(content=msg.text))
        # Can add SystemMessage or ToolMessage handling here if needed

    return langchain_messages