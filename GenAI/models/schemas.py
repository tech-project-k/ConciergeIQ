# =====================================================================
# Why it exists:
# Declares all Pydantic schemas (data transfer objects) used in the project.
# Ensures data schemas are strictly validated, typed, and structured.
#
# What it does:
# Provides validation and auto-serialization classes for Guest profiles, 
# itinerary schedules, travel route directions, bookings, and API requests.
#
# How it works:
# Standard Pydantic BaseModel definitions containing type declarations,
# optional indicators, and defaults.
#
# How it integrates:
# Used by agents to parse parsed intent, by services to serialize weather/places data, 
# and by routes as input/output request models for FastAPI endpoints.
# =====================================================================

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==========================================================
# 1. Catalog Spot Schemas
# ==========================================================

class Hotel(BaseModel):
    name: str = Field(description="Name of the hotel")
    address: str = Field(description="Physical address of the hotel")
    cost_per_night: float = Field(description="Cost per night in currency unit")
    rating: float = Field(default=4.0, description="Customer review rating (out of 5)")
    latitude: float
    longitude: float
    amenities: List[str] = Field(default=[], description="List of amenities like WiFi, Pool")

class Restaurant(BaseModel):
    name: str = Field(description="Name of the restaurant")
    address: str = Field(description="Physical address of the restaurant")
    cuisine_type: str = Field(description="Cuisine style, e.g., Indian, Seafood, Chinese")
    average_cost_for_two: float = Field(description="Average cost for two people")
    rating: float = Field(default=4.0, description="Review score (out of 5)")
    latitude: float
    longitude: float

class Attraction(BaseModel):
    name: str = Field(description="Name of the attraction")
    address: str = Field(description="Physical address of the attraction")
    cost: float = Field(default=0.0, description="Entry ticket cost")
    rating: float = Field(default=4.0, description="User ratings")
    latitude: float
    longitude: float
    category: str = Field(description="E.g., Beach, Temple, Museum, Mall")

class Event(BaseModel):
    name: str = Field(description="Name of the local event, concert, or festival")
    address: str = Field(description="Venue address")
    ticket_cost: float = Field(default=0.0, description="Ticket booking cost")
    latitude: float
    longitude: float
    date_time: str = Field(description="Date and time of the event")

# ==========================================================
# 2. Guest Profile & Travel Preferences
# ==========================================================

class UserLocation(BaseModel):
    latitude: float = Field(description="User's current latitude coordinate")
    longitude: float = Field(description="User's current longitude coordinate")
    city: Optional[str] = Field(default=None, description="Nearest city name if available")
    address: Optional[str] = Field(default=None, description="Full address or landmark")

class Guest(BaseModel):
    name: str = Field(default="Guest", description="Name of the traveler")
    current_location: Optional[UserLocation] = Field(default=None, description="User's current live location (latitude/longitude)")
    destination: str = Field(description="Target destination city")
    start_date: str = Field(description="Start date of the trip (YYYY-MM-DD)")
    end_date: str = Field(description="End date of the trip (YYYY-MM-DD)")
    budget: float = Field(description="Maximum travel budget limit")
    interests: List[str] = Field(default=[], description="List of traveler hobbies (e.g., Photography, Culture)")
    food_preference: str = Field(default="Any", description="Food type preference (e.g., Seafood, Vegetarian)")
    travel_type: str = Field(default="Solo", description="Solo, Couple, Family, or Friends group")
    accessibility_needs: List[str] = Field(default=[], description="Any physical accessibility requirements")
    weather_preference: str = Field(default="Any", description="Weather preference, e.g., Sunny, Cool")

# ==========================================================
# 3. Itinerary Schemas
# ==========================================================

class ItineraryItem(BaseModel):
    time_slot: str = Field(description="E.g., '09:00 AM' or '03:00 PM'")
    activity_name: str = Field(description="Name of place or event")
    activity_type: str = Field(description="E.g., attraction, hotel, restaurant, transit")
    cost: float = Field(default=0.0, description="Cost of this activity/ticket")
    description: str = Field(description="Short description of what the guest will do here")
    travel_time_from_prev: str = Field(default="0 mins", description="Time to travel from previous location")
    travel_distance_from_prev: str = Field(default="0 km", description="Distance from previous location")
    booking_confirmation_code: Optional[str] = Field(default=None, description="Booking confirmation code if pre-reserved (e.g., CLAW-ABC123)")

class DailyItinerary(BaseModel):
    day_number: int = Field(description="Day number of the trip (e.g. Day 1, Day 2)")
    date: str = Field(description="Date of this itinerary day")
    schedule: List[ItineraryItem] = Field(default=[], description="Chronological hourly activities list")

# ==========================================================
# 4. Booking & Notifications
# ==========================================================

class Booking(BaseModel):
    booking_id: str = Field(description="Auto-generated transaction ID")
    place_name: str = Field(description="Name of hotel/restaurant/monument booked")
    booking_type: str = Field(description="E.g., hotel, ticket, table")
    cost: float = Field(description="Total price paid for booking")
    confirmation_code: str = Field(description="Confirmation status code (e.g. CLAW-PENDING, CLAW-CONFIRMED)")
    booking_date: str = Field(description="Date transaction occurred")

# ==========================================================
# 5. Core API Request/Response Interfaces
# ==========================================================

class ChatRequest(BaseModel):
    session_id: str = Field(description="Unique session ID to maintain chat memory", min_length=1)
    message: str = Field(description="Message typed by the guest", min_length=1)
    user_location: Optional[UserLocation] = Field(default=None, description="Optional user's current live location (lat/lon)")
    guest_preferences: Optional[Guest] = Field(default=None, description="Optional hardcoded user profile override")

class ChatResponse(BaseModel):
    success: bool = Field(default=True, description="Success status flag for API response")
    session_id: str
    response: str = Field(description="Chat response generated by the travel concierge")
    message: Optional[str] = Field(default=None, description="Alias for response for frontend envelope consistency")
    itinerary: Optional[List[DailyItinerary]] = Field(default=None, description="Active generated itinerary plan if updated")
    estimated_cost: float = Field(default=0.0)
    travel_time: str = Field(default="0 mins")
    weather_summary: str = Field(default="Unknown")
    weather: Optional[Dict[str, Any]] = Field(default=None, description="Detailed weather object")
    budget: Optional[Dict[str, Any]] = Field(default=None, description="Detailed budget breakdown object")
    booking_alerts: List[str] = Field(default=[])
    recommendations: List[str] = Field(default=[], description="List of recommendation strings or objects")
    route_map: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of map points for rendering a route map from the user's location to itinerary stops")
    route: Optional[Dict[str, Any]] = Field(default=None, description="Detailed route object for frontend map rendering")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Chat turn history list")

class ItineraryRequest(BaseModel):
    guest_profile: Guest = Field(description="Complete guest profile including budget and dates")

class ItineraryResponse(BaseModel):
    guest_name: str
    destination: str
    itinerary: List[DailyItinerary] = Field(default=[])
    estimated_cost: float = Field(description="Total cost of all activities, dining, and hotel bookings")
    travel_time: str = Field(description="Sum of all transit time intervals")
    weather: str = Field(description="Weather forecast summary")
    recommendations: List[str] = Field(default=[], description="Recommended tips and alternative sights")
    booking_status: bool = Field(default=False, description="Whether booking reservations are secured")

class ExploreRequest(BaseModel):
    city: str = Field(description="City to explore")
    place_type: str = Field(description="E.g. hotel, restaurant, attraction, event")
    budget_limit: Optional[float] = None
