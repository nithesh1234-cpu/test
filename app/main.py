from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os

app = FastAPI(title="Chat API", version="0.1.0")


class Message(BaseModel):
    role: str = Field(..., description="Message role: system, user, assistant")
    content: str = Field(..., description="Message content text")


class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="Conversation messages in order")
    model: Optional[str] = Field(default=None, description="Upstream model name (optional)")
    stream: bool = Field(default=False, description="Whether to stream responses (not implemented)")


class ChatResponse(BaseModel):
    content: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    # Simple echo behavior: respond to last user message, or generic if none
    last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
    reply_text = f"You said: {last_user.content}" if last_user else "Hello!"

    # Placeholder for future OpenAI integration via OPENAI_API_KEY
    _ = os.getenv("OPENAI_API_KEY")

    return ChatResponse(content=reply_text)