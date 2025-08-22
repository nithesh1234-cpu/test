from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

from .database import get_db, engine
from .models import Base, User, Message, ChatRoom
from .schemas import UserCreate, UserLogin, MessageCreate, ChatRoomCreate
from .auth import create_access_token, get_current_user, verify_password, get_password_hash
from .crud import create_user, get_user_by_email, create_message, get_messages, create_chat_room

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chat API",
    description="A modern real-time chat API with WebSocket support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logging.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logging.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    self.active_connections[user_id].remove(connection)
    
    async def broadcast(self, message: str, exclude_user: Optional[int] = None):
        for user_id, connections in self.active_connections.items():
            if user_id != exclude_user:
                for connection in connections:
                    try:
                        await connection.send_text(message)
                    except:
                        # Remove broken connections
                        self.active_connections[user_id].remove(connection)

manager = ConnectionManager()

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "Chat API is running! 🚀"}

@app.post("/register", response_model=dict)
async def register(user: UserCreate, db=Depends(get_db)):
    """Register a new user"""
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = create_user(db, user)
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/login", response_model=dict)
async def login(user_credentials: UserLogin, db=Depends(get_db)):
    """Login user and return access token"""
    user = get_user_by_email(db, email=user_credentials.email)
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }

@app.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at
    }

@app.post("/chat-rooms", response_model=dict)
async def create_room(
    room: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """Create a new chat room"""
    room_id = create_chat_room(db, room, current_user.id)
    return {"message": "Chat room created", "room_id": room_id}

@app.get("/chat-rooms/{room_id}/messages", response_model=List[dict])
async def get_room_messages(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get messages from a specific chat room"""
    messages = get_messages(db, room_id)
    return [
        {
            "id": msg.id,
            "content": msg.content,
            "user_id": msg.user_id,
            "username": msg.user.username,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    """WebSocket endpoint for real-time chat"""
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="No token provided")
            return
        
        # Verify token and get user
        try:
            user = get_current_user(token)
        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect(websocket, user.id)
        
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "content": f"Welcome to room {room_id}, {user.username}!",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        # Broadcast user joined
        join_msg = {
            "type": "user_joined",
            "content": f"{user.username} joined the chat",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(join_msg), exclude_user=user.id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Create message in database
                message = MessageCreate(
                    content=message_data["content"],
                    room_id=room_id,
                    user_id=user.id
                )
                create_message(get_db().__next__(), message)
                
                # Broadcast message to all users in the room
                broadcast_msg = {
                    "type": "message",
                    "content": message_data["content"],
                    "user_id": user.id,
                    "username": user.username,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.broadcast(json.dumps(broadcast_msg))
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id)
            # Broadcast user left
            leave_msg = {
                "type": "user_left",
                "content": f"{user.username} left the chat",
                "user_id": user.id,
                "username": user.username,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(json.dumps(leave_msg))
            
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)