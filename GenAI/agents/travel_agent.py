# =====================================================================
# Why it exists:
# Main travel agent coordinator for ConciergeIQ.
# Uses LangGraph to orchestrate state transitions between sub-agents.
# =====================================================================

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from agents.memory_agent import memory_agent
from agents.intent_agent import intent_agent
from agents.weather_agent import weather_agent
from agents.retriever_agent import retriever_agent
from agents.planner_agent import planner_agent
from agents.validator_agent import validator_agent
from agents.recommendation_agent import recommendation_agent
from agents.response_agent import response_agent
from models.schemas import ChatResponse, DailyItinerary
from services.booking import booking_service
from utils.logger import get_logger

logger = get_logger("travel_agent")

# Define AgentState for LangGraph
class AgentState(TypedDict):
    session_id: str
    message: str
    preferences: Dict[str, Any]
    catalog_spots: List[Dict[str, Any]]
    weather: Dict[str, Any]
    raw_plan_text: str
    itinerary: List[DailyItinerary]
    estimated_cost: float
    warnings: List[str]
    recommendations: List[str]
    response_text: str
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
    
    return {**state, "recommendations": recs, "response_text": resp_text}

# Compile StateGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("intent", extract_intent_node)
workflow.add_node("weather", weather_check_node)
workflow.add_node("retrieve", retrieve_sights_node)
workflow.add_node("planner", planner_node)
workflow.add_node("validate", format_and_validate_node)
workflow.add_node("recommend_book", recommend_and_booking_node)

workflow.set_entry_point("intent")
workflow.add_edge("intent", "weather")
workflow.add_edge("weather", "retrieve")
workflow.add_edge("retrieve", "planner")
workflow.add_edge("planner", "validate")
workflow.add_edge("validate", "recommend_book")
workflow.add_edge("recommend_book", END)

# Compiled graph runnable
graph_runnable = workflow.compile()

class TravelAgent:
    def process_chat_message(self, session_id: str, message: str) -> ChatResponse:
        logger.info(f"Triggering LangGraph Travel Agent workflow for session: {session_id}")
        
        initial_state = {
            "session_id": session_id,
            "message": message,
            "preferences": {},
            "catalog_spots": [],
            "weather": {},
            "raw_plan_text": "",
            "itinerary": [],
            "estimated_cost": 0.0,
            "warnings": [],
            "recommendations": [],
            "response_text": "",
            "is_approved": False
        }
        
        # Execute workflow
        final_state = graph_runnable.invoke(initial_state)
        
        # Check if destination is unknown to ask follow-up questions
        destination = final_state["preferences"].get("destination", "Unknown")
        if destination == "Unknown":
            return ChatResponse(
                session_id=session_id,
                response=final_state["response_text"] if final_state["response_text"] else "Which city are you planning to visit? (e.g. Vizag, Hyderabad, Rajahmundry, or Ravulapalem)"
            )
            
        return ChatResponse(
            session_id=session_id,
            response=final_state["response_text"],
            itinerary=final_state["itinerary"],
            estimated_cost=final_state["estimated_cost"],
            travel_time="45 mins",
            weather_summary=f"{final_state['weather']['status']} ({final_state['weather']['temperature']})",
            booking_alerts=final_state["warnings"]
        )

travel_agent = TravelAgent()
