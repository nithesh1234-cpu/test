from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatRoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoomResponse(ChatRoomBase):
    id: int
    creator_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(BaseModel):
    content: str
    room_id: int
    user_id: int

class MessageResponse(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    room_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None