from pydantic import BaseModel, EmailStr # Added EmailStr
from typing import Optional

# === Existing Schemas ===
class ChatMessageInput(BaseModel):
    user_message: str
    conversation_id: Optional[int] = None

class ChatMessageOutput(BaseModel):
    ai_response: str
    conversation_id: int

# === New Auth Schemas ===
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None # Use EmailStr for validation

class UserCreate(UserBase):
    password: str # Password received plain text on creation

class UserLogin(BaseModel): # Not strictly needed if using form data, but good practice
    username: str
    password: str

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    # Do NOT include hashed_password by default in responses

    class Config:
        from_attributes = True # Replaces orm_mode=True

class User(UserInDBBase): # Schema for returning user info
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel): # Schema for data embedded in the token
    username: Optional[str] = None