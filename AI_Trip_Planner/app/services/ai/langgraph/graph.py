import uuid
import re
from datetime import datetime, date, timedelta
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.trip import Trip
from app.models.preferences import Preference
from app.models.itinerary import Activity
from app.models.catalog import Hotel, Restaurant, Event
from app.services.vector_db.store import vector_store
from app.services.ai.tools.booking import booking_tool
from app.services.ai.tools.external import external_tools
from app.utils.logger import get_logger

logger = get_logger("langgraph_agent")

class AgentState(TypedDict):
    query: str
    user_id: uuid.UUID
    trip_id: Optional[uuid.UUID]
    intent: str
    destination: str
    days: int
    budget_tier: str
    is_user_permitted: bool
    warnings: List[str]
    response_text: str
    activities: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    trip: Optional[Dict[str, Any]]

def resolve_coordinates(city: str) -> tuple:
    clean = city.strip().lower()
    if "paris" in clean: return 48.8566, 2.3522
    if "tokyo" in clean: return 35.6762, 139.6503
    if "hyderabad" in clean or "hyd" in clean: return 17.3850, 78.4867
    if "vizag" in clean or "visakhapatnam" in clean: return 17.6868, 83.2185
    if "rajahmundry" in clean: return 17.0005, 81.7835
    if "ravulapalem" in clean: return 16.7410, 81.8497
    
    # Stable generator based on name hash
    hash_val = abs(hash(clean))
    lat = 16.0 + (hash_val % 1000) / 200.0
    lon = 79.0 + ((hash_val // 1000) % 1000) / 200.0
    return lat, lon

# LangGraph Nodes
def intent_classifier(state: AgentState) -> AgentState:
    logger.info("Running Node: intent_classifier")
    query_lower = state["query"].lower()
    
    # 1. Detect Booking Permission Approval intent
    is_permitted = state.get("is_user_permitted", False)
    if any(word in query_lower for word in ["approve", "confirm", "pay", "yes", "ok"]):
        is_permitted = True
        intent = "approve_payment"
    elif any(word in query_lower for word in ["plan", "trip", "visit", "travel"]):
        intent = "plan"
    elif any(word in query_lower for word in ["change", "move", "replace", "avoid", "budget", "cheap", "luxury"]):
        intent = "modify"
    else:
        intent = "chat"
        
    # Parse days dynamically
    days = 2
    match = re.search(r"(\d+)\s*day", query_lower)
    if match:
        try:
            days = int(match.group(1))
            days = max(1, min(7, days)) # Limit 1-7 days
        except ValueError:
            pass
            
    # Parse budget tier changes
    budget_tier = state.get("budget_tier", "moderate")
    if any(word in query_lower for word in ["cheap", "budget", "economical", "cheaper"]):
        budget_tier = "budget"
    elif any(word in query_lower for word in ["luxury", "premium", "5 star", "expensive"]):
        budget_tier = "luxury"
    elif any(word in query_lower for word in ["moderate", "midrange", "standard"]):
        budget_tier = "moderate"

    # Extract destination
    destination = state.get("destination", "Paris")
    cities = ["tokyo", "paris", "hyderabad", "vizag", "rajahmundry", "ravulapalem"]
    for city in cities:
        if city in query_lower:
            destination = city.capitalize()
            break
            
    return {
        **state,
        "intent": intent,
        "days": days,
        "budget_tier": budget_tier,
        "destination": destination,
        "is_user_permitted": is_permitted
    }

def memory_loader(state: AgentState) -> AgentState:
    logger.info("Running Node: memory_loader")
    db: Session = SessionLocal()
    try:
        pref = db.query(Preference).filter(Preference.user_id == state["user_id"]).first()
        if not pref:
            # Seed default preference
            pref = Preference(
                user_id=state["user_id"],
                travel_style='{"adventure":3,"nature":3,"luxury":3}',
                dietary_restrictions="",
                accessibility_needs="",
                budget_tier="moderate"
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
            
        # If user did not specify new budget in query, read from preference
        budget = state["budget_tier"]
        if budget == "moderate" and pref.budget_tier != "moderate":
            budget = pref.budget_tier
            
        # Update preference budget tier if changed in this query
        if pref.budget_tier != state["budget_tier"]:
            pref.budget_tier = state["budget_tier"]
            db.add(pref)
            db.commit()
            
        return {
            **state,
            "budget_tier": budget
        }
    finally:
        db.close()

def rag_retriever(state: AgentState) -> AgentState:
    logger.info("Running Node: rag_retriever")
    # Search our SentenceTransformer vector store for relevant city catalog items
    results = vector_store.search(state["query"], state["destination"], limit=5)
    
    # Inject search context to help itinerary generation
    warnings = state.get("warnings", [])
    if not results:
        warnings.append(f"No direct events found for {state['destination']} in Vector DB. Using general fallback.")
        
    return {
        **state,
        "warnings": warnings,
        "activities": results # Save found catalog options in state
    }

def itinerary_generator(state: AgentState) -> AgentState:
    logger.info("Running Node: itinerary_generator")
    db: Session = SessionLocal()
    try:
        intent = state["intent"]
        trip_id = state["trip_id"]
        user_id = state["user_id"]
        destination = state["destination"]
        budget_tier = state["budget_tier"]
        days = state["days"]
        is_user_permitted = state["is_user_permitted"]
        warnings = list(state.get("warnings", []))
        
        # Load active trip
        active_trip = None
        if trip_id:
            active_trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not active_trip:
            active_trip = db.query(Trip).filter(Trip.user_id == user_id, Trip.status == "planning").first()
            
        # 1. PROCESS PAYMENT PERMISSION APPROVALS
        if intent == "approve_payment" and active_trip:
            # User confirmed payment! Find all PENDING bookings and confirm them
            pending_activities = db.query(Activity).filter(Activity.trip_id == active_trip.id, Activity.booking_confirmation_code == "CLAW-PENDING").all()
            if pending_activities:
                for act in pending_activities:
                    res = booking_tool.process_booking(act.name, act.cost, is_user_permitted=True)
                    act.booking_confirmation_code = res["confirmation_code"]
                    db.add(act)
                db.commit()
                db.refresh(active_trip)
                
                # Format response
                resp_text = f"Payment permission granted! I've successfully completed the transactions for your pending movie/temple tickets."
                return {
                    **state,
                    "response_text": resp_text,
                    "trip_id": active_trip.id
                }
            else:
                resp_text = "You don't have any pending bookings waiting for payment permission."
                return {
                    **state,
                    "response_text": resp_text,
                    "trip_id": active_trip.id
                }

        # 2. STANDARD PLAN OR MODIFY INTENT
        if intent == "plan" or not active_trip:
            start_dt = date.today()
            end_dt = start_dt + timedelta(days=days - 1)
            
            if active_trip:
                # Delete activities using clear() to satisfy orphanRemoval
                active_trip.activities.clear()
                active_trip.destination = destination
                active_trip.start_date = start_dt
                active_trip.end_date = end_dt
                db.add(active_trip)
                db.commit()
            else:
                active_trip = Trip(
                    user_id=user_id,
                    destination=destination,
                    start_date=start_dt,
                    end_date=end_dt,
                    status="planning"
                )
                db.add(active_trip)
                db.commit()
                db.refresh(active_trip)
                
            # Build day by day hourly activities
            catalog_options = state["activities"]
            hotel_coords = resolve_coordinates(destination)
            hotel_name = f"{destination} Grand Plaza Hotel"
            if budget_tier == "budget":
                hotel_name = f"{destination} Backpackers Cozy Lodge"
            elif budget_tier == "luxury":
                hotel_name = f"{destination} Grand Royal Palace & Spa Resort"
                
            for d in range(1, days + 1):
                # Day Activities Sequence
                # 1. Hotel Departure (08:30)
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=f"Hotel Departure: {hotel_name}",
                    type="hotel",
                    start_time="08:30",
                    end_time="09:00",
                    latitude=hotel_coords[0],
                    longitude=hotel_coords[1],
                    address=f"1 Luxury Road, {destination}",
                    cost=0.0
                ))
                
                # Filter catalog items for this day
                day_attraction = next((item for item in catalog_options if item["type"] == "attraction"), {"name": f"{destination} Heritage Site", "address": "Central Square", "cost": 10.0, "lat": hotel_coords[0]+0.005, "lon": hotel_coords[1]+0.005})
                day_lunch = next((item for item in catalog_options if item["type"] == "lunch"), {"name": f"{destination} Local Spice Diner", "address": "Food Street", "cost": 15.0, "lat": hotel_coords[0]-0.002, "lon": hotel_coords[1]+0.004})
                day_event = next((item for item in catalog_options if item["type"] == "event"), {"name": f"{destination} Cinema Multiplex Screen", "address": "Mall Area", "cost": 6.0, "lat": hotel_coords[0]-0.006, "lon": hotel_coords[1]-0.004})
                day_dinner = next((item for item in catalog_options if item["type"] == "dinner"), {"name": f"{destination} Executive Bistro", "address": "Highway Junction", "cost": 25.0, "lat": hotel_coords[0]+0.001, "lon": hotel_coords[1]-0.002})
                
                # Apply budget multipliers
                mult = 0.5 if budget_tier == "budget" else (2.0 if budget_tier == "luxury" else 1.0)
                
                # 2. Attraction (09:30 - 12:00)
                att_cost = round(day_attraction["cost"] * mult, 2)
                att_res = booking_tool.process_booking(day_attraction["name"], att_cost, is_permitted)
                if att_res["warning"]:
                    warnings.append(att_res["warning"])
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=day_attraction["name"],
                    type="attraction",
                    start_time="09:30",
                    end_time="12:00",
                    latitude=day_attraction["lat"],
                    longitude=day_attraction["lon"],
                    address=day_attraction["address"],
                    cost=att_cost,
                    booking_confirmation_code=att_res["confirmation_code"]
                ))
                
                # 3. Lunch (12:30 - 14:00)
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=day_lunch["name"],
                    type="lunch",
                    start_time="12:30",
                    end_time="14:00",
                    latitude=day_lunch["lat"],
                    longitude=day_lunch["lon"],
                    address=day_lunch["address"],
                    cost=round(day_lunch["cost"] * mult, 2)
                ))
                
                # 4. Afternoon Event (14:30 - 17:00)
                evt_cost = round(day_event["cost"] * mult, 2)
                evt_res = booking_tool.process_booking(day_event["name"], evt_cost, is_permitted)
                if evt_res["warning"]:
                    warnings.append(evt_res["warning"])
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=day_event["name"],
                    type="event",
                    start_time="14:30",
                    end_time="17:00",
                    latitude=day_event["lat"],
                    longitude=day_event["lon"],
                    address=day_event["address"],
                    cost=evt_cost,
                    booking_confirmation_code=evt_res["confirmation_code"]
                ))
                
                # 5. Dinner (19:00 - 21:00)
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=day_dinner["name"],
                    type="dinner",
                    start_time="19:00",
                    end_time="21:00",
                    latitude=day_dinner["lat"],
                    longitude=day_dinner["lon"],
                    address=day_dinner["address"],
                    cost=round(day_dinner["cost"] * mult, 2),
                    booking_confirmation_code=f"CLAW-AUTO-{uuid.uuid4().hex[:6].upper()}" # Table reservations auto confirm
                ))
                
                # 6. Return Hotel (21:30)
                db.add(Activity(
                    trip_id=active_trip.id,
                    day_number=d,
                    name=f"Return to {hotel_name}",
                    type="hotel",
                    start_time="21:30",
                    end_time="22:00",
                    latitude=hotel_coords[0],
                    longitude=hotel_coords[1],
                    address=f"1 Luxury Road, {destination}",
                    cost=0.0
                ))
                
            db.commit()
            db.refresh(active_trip)
            
            # Run transit routing optimizations
            activities_list = active_trip.activities
            for idx, act in enumerate(activities_list):
                if idx == 0 or act.day_number != activities_list[idx - 1].day_number:
                    act.travel_distance_km = 0.0
                    act.travel_duration_min = 0.0
                    act.travel_mode = "walking"
                else:
                    prev = activities_list[idx - 1]
                    dist = external_tools.haversine_distance(prev.latitude, prev.longitude, act.latitude, act.longitude)
                    transit = external_tools.resolve_transit(dist)
                    act.travel_distance_km = transit["distance_km"]
                    act.travel_duration_min = transit["duration_min"]
                    act.travel_mode = transit["mode"]
                    if transit["duration_min"] > 30.0:
                        warnings.append(f"Day {act.day_number}: Transit between '{prev.name}' and '{act.name}' is long ({transit['duration_min']} mins).")
            db.commit()
            db.refresh(active_trip)
            
            resp_text = f"I've drafted a personalized {days}-day {budget_tier.upper()} budget itinerary for your trip to {destination}! I searched local attractions in OpenSearch and automatically pre-reserved your temple and movie tickets via OpenClaw."
            
        elif intent == "modify" and active_trip:
            # Handle direct modify requests (like budget changes)
            active_trip.activities.clear()
            db.commit()
            db.refresh(active_trip)
            
            # Recalculate trip with new budget
            state_intent_plan = {**state, "intent": "plan"}
            return itinerary_generator(state_intent_plan)
            
        else:
            resp_text = "I am your Concierge AI Assistant. I can update your itinerary, book tickets, check conflicts, or suggest local activities. What would you like to plan?"
            
        return {
            **state,
            "response_text": resp_text,
            "trip_id": active_trip.id,
            "warnings": list(set(warnings))
        }
    finally:
        db.close()

def save_trip(state: AgentState) -> AgentState:
    logger.info("Running Node: save_trip")
    db: Session = SessionLocal()
    try:
        trip_data = None
        if state["trip_id"]:
            trip = db.query(Trip).filter(Trip.id == state["trip_id"]).first()
            if trip:
                # Format to JSON payload
                activities = []
                for act in trip.activities:
                    activities.append({
                        "id": str(act.id),
                        "day_number": act.day_number,
                        "name": act.name,
                        "type": act.type,
                        "start_time": act.start_time,
                        "end_time": act.end_time,
                        "latitude": act.latitude,
                        "longitude": act.longitude,
                        "address": act.address,
                        "cost": act.cost,
                        "booking_confirmation_code": act.booking_confirmation_code,
                        "travel_distance_km": act.travel_distance_km,
                        "travel_duration_min": act.travel_duration_min,
                        "travel_mode": act.travel_mode
                    })
                trip_data = {
                    "id": str(trip.id),
                    "destination": trip.destination,
                    "start_date": trip.start_date.isoformat(),
                    "end_date": trip.end_date.isoformat(),
                    "status": trip.status,
                    "activities": activities
                }
        return {
            **state,
            "trip": trip_data
        }
    finally:
        db.close()

# Assemble the StateGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("intent_classifier", intent_classifier)
workflow.add_node("memory_loader", memory_loader)
workflow.add_node("rag_retriever", rag_retriever)
workflow.add_node("itinerary_generator", itinerary_generator)
workflow.add_node("save_trip", save_trip)

# Set Entry Point
workflow.set_entry_point("intent_classifier")

# Add Sequential Edges
workflow.add_edge("intent_classifier", "memory_loader")
workflow.add_edge("memory_loader", "rag_retriever")
workflow.add_edge("rag_retriever", "itinerary_generator")
workflow.add_edge("itinerary_generator", "save_trip")
workflow.add_edge("save_trip", END)

# Compile Graph
graph_agent = workflow.compile()
