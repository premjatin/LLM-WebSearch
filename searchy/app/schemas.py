from pydantic import BaseModel
from typing import Optional

class ChatMessageInput(BaseModel):
    user_message: str
    conversation_id: Optional[int] = None # Optional: will create new if None

class ChatMessageOutput(BaseModel):
    ai_response: str
    conversation_id: int