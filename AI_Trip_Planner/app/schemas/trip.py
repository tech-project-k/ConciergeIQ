from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

class ActivityResponse(BaseModel):
    id: UUID
    day_number: int
    name: str
    type: str
    start_time: str
    end_time: str
    latitude: float
    longitude: float
    address: str
    cost: float
    booking_confirmation_code: Optional[str] = None
    travel_distance_km: float
    travel_duration_min: float
    travel_mode: str

    class Config:
        from_attributes = True

class TripCreate(BaseModel):
    destination: str
    start_date: date
    end_date: date

class TripResponse(BaseModel):
    id: UUID
    destination: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    activities: List[ActivityResponse] = []

    class Config:
        from_attributes = True

class SavedPlaceResponse(BaseModel):
    id: UUID
    name: str
    address: str
    latitude: float
    longitude: float
    place_type: Optional[str] = None

    class Config:
        from_attributes = True
