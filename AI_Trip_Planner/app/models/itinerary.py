import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # hotel, attraction, lunch, event, dinner
    start_time = Column(String, nullable=False)  # HH:MM
    end_time = Column(String, nullable=False)  # HH:MM
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    cost = Column(Float, default=0.0)
    
    # Booking confirmations (Auto-booking with user permission)
    booking_confirmation_code = Column(String, nullable=True) # status like CLAW-AUTO-XYZ, CLAW-PENDING, or NULL
    
    # Transit fields
    travel_distance_km = Column(Float, default=0.0)
    travel_duration_min = Column(Float, default=0.0)
    travel_mode = Column(String, default="walking") # walking, transit, driving

    trip = relationship("Trip", back_populates="activities")

class SavedPlace(Base):
    __tablename__ = "saved_places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    place_type = Column(String, nullable=True) # hotel, restaurant, landmark

class TravelHistory(Base):
    __tablename__ = "travel_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rating = Column(Float, default=5.0)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
