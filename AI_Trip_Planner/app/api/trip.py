from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.user import User
from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripResponse
from app.utils.security import get_current_user
from app.services.vector_db.store import vector_store
from app.services.ai.langgraph.graph import graph_agent
import uuid

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("", response_model=List[TripResponse])
def get_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trips = db.query(Trip).filter(Trip.user_id == current_user.id).order_by(Trip.created_at.desc()).all()
    return trips

@router.get("/saved-trips", response_model=List[TripResponse])
def get_saved_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trips = db.query(Trip).filter(Trip.user_id == current_user.id).order_by(Trip.created_at.desc()).all()
    return trips

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()
    return None

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: uuid.UUID, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/plan-trip", response_model=TripResponse)
def plan_trip(payload: TripCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Create trip model
    trip = Trip(
        user_id=current_user.id,
        destination=payload.destination,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="planning"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    # Run the graph workflow to generate itinerary activities for this trip
    days = (payload.end_date - payload.start_date).days + 1
    state_input = {
        "query": f"plan a new trip to {payload.destination} for {days} days",
        "user_id": current_user.id,
        "trip_id": trip.id,
        "intent": "plan",
        "destination": payload.destination,
        "days": days,
        "budget_tier": "moderate",
        "is_user_permitted": False,
        "warnings": [],
        "response_text": "",
        "activities": [],
        "messages": [],
        "trip": None
    }
    graph_agent.invoke(state_input)
    
    # Reload and return trip with populated activities
    db.refresh(trip)
    return trip

@router.get("/recommendations/{city}")
def get_recommendations(city: str):
    results = vector_store.search("popular hidden gems tourist places hotels", city, limit=6)
    return results
