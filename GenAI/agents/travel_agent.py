# =====================================================================
# Why it exists:
# Main travel agent coordinator for ConciergeIQ.
# Uses LangGraph to orchestrate state transitions between sub-agents.
# =====================================================================

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.memory_agent import memory_agent
from agents.intent_agent import intent_agent
from agents.weather_agent import weather_agent
from agents.retriever_agent import retriever_agent
from agents.planner_agent import planner_agent
from agents.validator_agent import validator_agent
from agents.recommendation_agent import recommendation_agent
from agents.response_agent import response_agent
from models.schemas import ChatResponse, DailyItinerary, UserLocation
from services.booking import booking_service
from services.location import location_service
from utils.logger import get_logger

logger = get_logger("travel_agent")

# Define AgentState for LangGraph
class AgentState(TypedDict):
    session_id: str
    message: str
    user_location: Optional[Dict[str, float]]
    location_to_destination: Optional[Dict[str, Any]]
    preferences: Dict[str, Any]
    catalog_spots: List[Dict[str, Any]]
    weather: Dict[str, Any]
    raw_plan_text: str
    itinerary: List[DailyItinerary]
    estimated_cost: float
    warnings: List[str]
    recommendations: List[str]
    response_text: str
    route_map: List[Dict[str, Any]]
    is_approved: bool

# Define nodes for our StateGraph workflow
def extract_intent_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Extracting Intent")
    prev = memory_agent.load_preferences(state["session_id"])
    prefs = intent_agent.extract_intent(state["message"], prev)
    memory_agent.persist_preferences(state["session_id"], prefs)
    return {**state, "preferences": prefs}

def weather_check_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Checking Weather")
    dest = state["preferences"].get("destination", "Unknown")
    weather = weather_agent.evaluate_weather(dest)
    return {**state, "weather": weather}

def location_distance_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Calculating Distance from Current Location")
    dest = state["preferences"].get("destination", "Unknown")
    location_to_dest = None
    
    if state["user_location"] and dest != "Unknown":
        try:
            user_lat = state["user_location"].get("latitude")
            user_lon = state["user_location"].get("longitude")
            if user_lat and user_lon:
                location_to_dest = location_service.calculate_distance_to_destination(
                    user_lat, user_lon, dest
                )
                logger.info(f"Distance from user location to {dest}: {location_to_dest.get('distance', 'N/A')}")
        except Exception as e:
            logger.error(f"Location distance calculation failed: {e}")
    
    return {**state, "location_to_destination": location_to_dest}

def retrieve_sights_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Retrieving Sights Catalog")
    dest = state["preferences"].get("destination", "Unknown")
    interests = state["preferences"].get("interests", [])
    spots = retriever_agent.retrieve_context(dest, interests)
    return {**state, "catalog_spots": spots}

def planner_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Generating Daily Schedule")
    raw_text = planner_agent.generate_plan(
        state["preferences"], 
        state["catalog_spots"], 
        state["weather"]["status"]
    )
    return {**state, "raw_plan_text": raw_text}

def format_and_validate_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Formatting JSON & Auditing Conflicts")
    date = state["preferences"].get("start_date", "2026-07-18")
    itinerary = response_agent.format_response(
        state["raw_plan_text"], "Guest", date, state["weather"]["status"]
    )
    
    budget_limit = state["preferences"].get("budget", 5000.0)
    is_rainy = state["weather"]["is_rainy"]
    audit = validator_agent.validate_itinerary(itinerary, budget_limit, is_rainy)
    
    return {
        **state,
        "itinerary": itinerary,
        "estimated_cost": audit["estimated_cost"],
        "warnings": audit["warnings"]
    }

def build_route_map(state: AgentState) -> List[Dict[str, Any]]:
    route_points: List[Dict[str, Any]] = []

    if state.get("user_location"):
        route_points.append({
            "name": "Current Location",
            "latitude": state["user_location"].get("latitude"),
            "longitude": state["user_location"].get("longitude"),
            "type": "start"
        })

    destination = state["preferences"].get("destination", "Unknown")
    if destination != "Unknown":
        destination_coords = location_service.get_destination_coordinates(destination)
        if destination_coords:
            dest_lat, dest_lon = destination_coords
            route_points.append({
                "name": f"Destination: {destination}",
                "latitude": dest_lat,
                "longitude": dest_lon,
                "type": "destination"
            })

    for day in state.get("itinerary", []):
        for idx, item in enumerate(day.schedule):
            found_spot = False
            for spot in state.get("catalog_spots", []):
                spot_name = str(spot.get("name", "")).lower()
                item_name = item.activity_name.lower()
                if spot_name and (spot_name in item_name or item_name in spot_name):
                    if "lat" in spot and "lon" in spot:
                        route_points.append({
                            "name": item.activity_name,
                            "latitude": spot.get("lat"),
                            "longitude": spot.get("lon"),
                            "type": item.activity_type
                        })
                        found_spot = True
                        break
            if not found_spot and destination != "Unknown":
                dest_coords = location_service.get_destination_coordinates(destination)
                if dest_coords:
                    # Provide offset coords for route display
                    offset_lat = dest_coords[0] + (0.003 * (idx + 1))
                    offset_lon = dest_coords[1] + (0.003 * (idx + 1))
                    route_points.append({
                        "name": item.activity_name,
                        "latitude": offset_lat,
                        "longitude": offset_lon,
                        "type": item.activity_type
                    })

    return route_points


def recommend_and_booking_node(state: AgentState) -> AgentState:
    logger.info("LangGraph Node: Drafting Recommendations & Booking Confirmations")
    dest = state["preferences"].get("destination", "Unknown")
    interests = state["preferences"].get("interests", [])
    
    itinerary_places = []
    for day in state["itinerary"]:
        for item in day.schedule:
            itinerary_places.append(item.activity_name)
            # Run OpenClaw ticket pre-reservations
            ticket_keywords = ["temple", "museum", "imax", "multiplex", "event", "show", "concert"]
            if any(kw in item.activity_name.lower() for kw in ticket_keywords):
                # Check for approval intent in message
                msg_lower = state["message"].lower()
                is_approved = any(word in msg_lower for word in ["approve", "confirm", "yes", "pay"])
                booking = booking_service.pre_reserve_ticket(
                    item.activity_name, "ticket", item.cost, is_approved
                )
                item.booking_confirmation_code = booking["confirmation_code"]
                
    recs = recommendation_agent.generate_recommendations(
        destination=dest,
        interests=interests,
        current_itinerary_places=itinerary_places,
        itinerary_text=state["raw_plan_text"]
    )
    
    # Format text response statement
    warning_msg = ""
    if state["warnings"]:
        warning_msg = f"\n\n⚠️ Warnings: " + " | ".join(state["warnings"])
        
    resp_text = (
        f"Here is your personalized itinerary for {dest}! "
        f"Estimated cost is Rs. {state['estimated_cost']:.2f}. "
        f"Weather is currently {state['weather']['description']}.{warning_msg}"
    )
    if recs:
        resp_text += "\n\n💡 Recommendations:\n" + "\n".join(f"- {r}" for r in recs)
        
    memory_agent.save_chat_turn(state["session_id"], state["message"], resp_text)
    route_map = build_route_map(state)
    
    return {**state, "recommendations": recs, "response_text": resp_text, "route_map": route_map}

# Compile StateGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("intent", extract_intent_node)
workflow.add_node("check_weather", weather_check_node)
workflow.add_node("location_distance", location_distance_node)
workflow.add_node("retrieve", retrieve_sights_node)
workflow.add_node("planner", planner_node)
workflow.add_node("validate", format_and_validate_node)
workflow.add_node("recommend_book", recommend_and_booking_node)

workflow.set_entry_point("intent")
workflow.add_edge("intent", "check_weather")
workflow.add_edge("check_weather", "location_distance")
workflow.add_edge("location_distance", "retrieve")
workflow.add_edge("retrieve", "planner")
workflow.add_edge("planner", "validate")
workflow.add_edge("validate", "recommend_book")
workflow.add_edge("recommend_book", END)

# Compiled graph runnable
graph_runnable = workflow.compile()

class TravelAgent:
    def process_chat_message(self, session_id: str, message: str, user_location: Optional[Dict[str, float]] = None) -> ChatResponse:
        logger.info(f"Triggering LangGraph Travel Agent workflow for session: {session_id}")
        
        try:
            initial_state = {
                "session_id": session_id,
                "message": message,
                "user_location": user_location,
                "location_to_destination": None,
                "preferences": {},
                "catalog_spots": [],
                "weather": {},
                "raw_plan_text": "",
                "itinerary": [],
                "estimated_cost": 0.0,
                "warnings": [],
                "recommendations": [],
                "response_text": "",
                "route_map": [],
                "is_approved": False
            }
            
            # Execute workflow
            final_state = graph_runnable.invoke(initial_state)
            
            # Check if destination is unknown to ask follow-up questions
            destination = final_state["preferences"].get("destination", "Unknown")
            if destination == "Unknown":
                resp_msg = final_state["response_text"] if final_state["response_text"] else "Which city are you planning to visit? (e.g. Vizag, Hyderabad, Goa, Tirupati, or any city worldwide, please specify)"
                return ChatResponse(
                    success=True,
                    session_id=session_id,
                    response=resp_msg,
                    message=resp_msg
                )
            
            # Build location context string
            location_context = ""
            if final_state["location_to_destination"]:
                loc_data = final_state["location_to_destination"]
                location_context = f"\n📍 **Travel Distance:** {loc_data.get('distance', 'N/A')} | **Estimated Time:** {loc_data.get('duration', 'N/A')}"
                
            full_response_text = final_state["response_text"] + location_context
            weather_str = f"{final_state['weather'].get('status', 'Sunny')} ({final_state['weather'].get('temperature', '28°C')})"
            
            history_turns = memory_agent.load_chat_history(session_id)
            
            return ChatResponse(
                success=True,
                session_id=session_id,
                response=full_response_text,
                message=full_response_text,
                itinerary=final_state["itinerary"],
                estimated_cost=final_state["estimated_cost"],
                travel_time="45 mins",
                weather_summary=weather_str,
                weather=final_state["weather"],
                budget={
                    "estimated_cost": final_state["estimated_cost"],
                    "limit": final_state["preferences"].get("budget", 5000.0)
                },
                booking_alerts=final_state["warnings"],
                recommendations=final_state.get("recommendations", []),
                route_map=final_state.get("route_map", []),
                route={"waypoints": final_state.get("route_map", [])},
                history=history_turns
            )
        except Exception as e:
            logger.error(f"Travel Agent workflow failed: {str(e)}", exc_info=True)
            err_msg = f"Sorry, I encountered an error processing your request. Error: {str(e)}"
            return ChatResponse(
                success=False,
                session_id=session_id,
                response=err_msg,
                message=err_msg,
                booking_alerts=[f"Workflow Error: {str(e)}"]
            )

travel_agent = TravelAgent()
