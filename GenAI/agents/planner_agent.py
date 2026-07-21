# =====================================================================
# Why it exists:
# Generates hour-by-hour itineraries.
# =====================================================================

import json
from typing import List, Dict, Any
from config.settings import settings
from prompts.templates import TRAVEL_PLANNING_PROMPT
from services.maps import maps_service
from utils.logger import get_logger
from utils.llm import invoke_with_timeout
from langchain_google_genai import ChatGoogleGenerativeAI

logger = get_logger("planner_agent")

class PlannerAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.llm = None
        if self.api_key and "YOUR_GEMINI" not in self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=self.api_key,
                    timeout=30.0
                )
            except Exception as e:
                logger.error(f"Gemini err: {e}")

    def generate_plan(self, preferences: Dict[str, Any], catalog_spots: List[Dict[str, Any]], weather_summary: str) -> str:
        destination = preferences.get("destination", "Unknown")
        budget = preferences.get("budget", 5000.0)
        
        if self.llm:
            try:
                catalog_text = ""
                for spot in catalog_spots:
                    catalog_text += f"- {spot['name']} ({spot['type']}): Cost Rs. {spot['cost']}, Address: {spot['address']}\n"
                    
                prompt = TRAVEL_PLANNING_PROMPT.format(
                    destination=destination,
                    budget=budget,
                    interests=", ".join(preferences.get("interests", ["Sightseeing"])),
                    food_preference=preferences.get("food_preference", "Any"),
                    travel_type=preferences.get("travel_type", "Solo"),
                    catalog_data=catalog_text,
                    weather=weather_summary
                )
                
                response = invoke_with_timeout(
                    self.llm,
                    prompt,
                    timeout=8.0,
                    fallback=lambda p: None,
                )
                if response is None:
                    raise RuntimeError("LLM timeout")
                return response.content.strip()
            except Exception as e:
                logger.error(f"Gemini planner fail: {e}")

        # Local simulation
        return self._generate_simulated_plan(preferences, catalog_spots, weather_summary)

    def _generate_simulated_plan(self, preferences: Dict[str, Any], catalog_spots: List[Dict[str, Any]], weather_summary: str) -> str:
        destination = preferences.get("destination", "Unknown")
        
        hotels = [s for s in catalog_spots if s["type"] == "hotel"]
        lunches = [s for s in catalog_spots if s["type"] == "lunch"]
        dinners = [s for s in catalog_spots if s["type"] == "dinner"]
        events = [s for s in catalog_spots if s["type"] == "event"]
        attractions = [s for s in catalog_spots if s["type"] == "attraction"]

        hotel_name = hotels[0]["name"] if hotels else f"{destination} Comfort Stay Hotel"
        hotel_cost = hotels[0]["cost"] if hotels else 2000.0
        
        lunch_name = lunches[0]["name"] if lunches else "Local Traditional Restaurant"
        lunch_cost = lunches[0]["cost"] if lunches else 250.0
        
        dinner_name = dinners[0]["name"] if dinners else "Premium Dine Restaurant"
        dinner_cost = dinners[0]["cost"] if dinners else 800.0

        plan_lines = []
        plan_lines.append(f"Itinerary for {destination} - Day 1:")
        plan_lines.append("")
        
        plan_lines.append("Time: 09:00 AM")
        plan_lines.append(f"Activity: Hotel Check-in at {hotel_name}")
        plan_lines.append("Type: hotel")
        plan_lines.append(f"Cost: {hotel_cost}")
        plan_lines.append("Description: Check-in and drop off luggage.")
        plan_lines.append("Transit: 0 mins (0 km)")
        plan_lines.append("")

        att1_name = attractions[0]["name"] if attractions else "Regional Beach Sunrise Walk"
        att1_cost = attractions[0]["cost"] if attractions else 50.0
        plan_lines.append("Time: 10:30 AM")
        plan_lines.append(f"Activity: {att1_name}")
        plan_lines.append("Type: attraction")
        plan_lines.append(f"Cost: {att1_cost}")
        plan_lines.append("Description: Explore scenic views and click photos.")
        plan_lines.append("Transit: 15 mins (2 km)")
        plan_lines.append("")

        plan_lines.append("Time: 01:00 PM")
        plan_lines.append(f"Activity: Lunch at {lunch_name}")
        plan_lines.append("Type: restaurant")
        plan_lines.append(f"Cost: {lunch_cost}")
        plan_lines.append("Description: Relish regional delicacies.")
        plan_lines.append("Transit: 10 mins (1.5 km)")
        plan_lines.append("")

        att2_name = attractions[1]["name"] if len(attractions) > 1 else (events[0]["name"] if events else "Local Museum Tour")
        att2_cost = attractions[1]["cost"] if len(attractions) > 1 else (events[0]["cost"] if events else 100.0)
        plan_lines.append("Time: 03:00 PM")
        plan_lines.append(f"Activity: {att2_name}")
        plan_lines.append("Type: attraction")
        plan_lines.append(f"Cost: {att2_cost}")
        plan_lines.append("Description: Visit popular spot.")
        plan_lines.append("Transit: 20 mins (3.5 km)")
        plan_lines.append("")

        plan_lines.append("Time: 07:00 PM")
        plan_lines.append(f"Activity: Dinner at {dinner_name}")
        plan_lines.append("Type: restaurant")
        plan_lines.append(f"Cost: {dinner_cost}")
        plan_lines.append("Description: Premium dining experience.")
        plan_lines.append("Transit: 12 mins (2.2 km)")
        plan_lines.append("")

        return "\n".join(plan_lines)

planner_agent = PlannerAgent()
