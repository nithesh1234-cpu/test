from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from typing import List, Optional

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> int:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.id

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get list of users"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_chat_room(db: Session, room: schemas.ChatRoomCreate, creator_id: int) -> int:
    """Create a new chat room"""
    db_room = models.ChatRoom(
        name=room.name,
        description=room.description,
        is_private=room.is_private,
        creator_id=creator_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room.id

def get_chat_room(db: Session, room_id: int) -> Optional[models.ChatRoom]:
    """Get chat room by ID"""
    return db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()

def get_chat_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[models.ChatRoom]:
    """Get list of chat rooms"""
    return db.query(models.ChatRoom).offset(skip).limit(limit).all()

def create_message(db: Session, message: schemas.MessageCreate) -> models.Message:
    """Create a new message"""
    db_message = models.Message(
        content=message.content,
        user_id=message.user_id,
        room_id=message.room_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages(db: Session, room_id: int, skip: int = 0, limit: int = 100) -> List[models.Message]:
    """Get messages from a specific chat room"""
    return db.query(models.Message)\
        .filter(models.Message.room_id == room_id)\
        .order_by(models.Message.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_message(db: Session, message_id: int) -> Optional[models.Message]:
    """Get message by ID"""
    return db.query(models.Message).filter(models.Message.id == message_id).first()