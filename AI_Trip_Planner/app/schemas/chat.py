from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

class ChatRequest(BaseModel):
    query: str
    trip_id: Optional[UUID] = None

class MessageItem(BaseModel):
    role: str
    content: str
    id: str

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    warnings: List[str]
    messages: List[MessageItem]
    trip: Optional[Dict[str, Any]] = None
