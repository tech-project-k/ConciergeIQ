from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.schemas.chat import ChatRequest, ChatResponse, MessageItem
from app.utils.security import get_current_user
from app.services.ai.langgraph.graph import graph_agent
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def process_chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Run the stateful LangGraph agent
    state_input = {
        "query": payload.query,
        "user_id": current_user.id,
        "trip_id": payload.trip_id,
        "intent": "chat",
        "destination": "Paris",
        "days": 2,
        "budget_tier": "moderate",
        "is_user_permitted": False,
        "warnings": [],
        "response_text": "",
        "activities": [],
        "messages": [],
        "trip": None
    }
    
    # Execute Graph
    result_state = graph_agent.invoke(state_input)
    
    actual_trip_id = result_state["trip_id"]
    if not actual_trip_id:
        actual_trip_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
    # Save User message to database
    user_msg = ChatHistory(
        trip_id=actual_trip_id,
        role="user",
        content=payload.query
    )
    db.add(user_msg)
    
    # Save Assistant response to database
    assistant_msg = ChatHistory(
        trip_id=actual_trip_id,
        role="assistant",
        content=result_state["response_text"]
    )
    db.add(assistant_msg)
    db.commit()
    
    # Load entire conversation history for this trip
    db_history = db.query(ChatHistory).filter(ChatHistory.trip_id == actual_trip_id).order_by(ChatHistory.created_at.asc()).all()
    
    messages = []
    for msg in db_history:
        messages.append(MessageItem(
            role=msg.role,
            content=msg.content,
            id=str(msg.id)
        ))
        
    return ChatResponse(
        response_text=result_state["response_text"],
        intent=result_state["intent"],
        warnings=result_state["warnings"],
        messages=messages,
        trip=result_state["trip"]
    )

@router.get("/history/{trip_id}", response_model=List[MessageItem])
def get_chat_history(trip_id: uuid.UUID, db: Session = Depends(get_db)):
    db_history = db.query(ChatHistory).filter(ChatHistory.trip_id == trip_id).order_by(ChatHistory.created_at.asc()).all()
    if not db_history:
        # Seed default welcome message
        welcome = ChatHistory(
            trip_id=trip_id,
            role="assistant",
            content="Welcome back! What afternoon changes would you like to make to your itinerary? I will utilize OpenClaw to book tickets and verify conflict reservations."
        )
        db.add(welcome)
        db.commit()
        db.refresh(welcome)
        db_history = [welcome]
        
    messages = []
    for msg in db_history:
        messages.append(MessageItem(
            role=msg.role,
            content=msg.content,
            id=str(msg.id)
        ))
    return messages
