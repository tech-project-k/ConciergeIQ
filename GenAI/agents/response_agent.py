# =====================================================================
# Why it exists:
# Parses raw text plans into JSON responses.
# =====================================================================

import json
import re
from typing import Dict, Any, List
from config.settings import settings
from prompts.templates import JSON_FORMATTER_PROMPT
from models.schemas import DailyItinerary, ItineraryItem
from utils.logger import get_logger
from utils.llm import invoke_with_timeout
from langchain_google_genai import ChatGoogleGenerativeAI

logger = get_logger("response_agent")

class ResponseAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.llm = None
        if self.api_key and "YOUR_GEMINI" not in self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.api_key,
                    timeout=5.0
                )
            except Exception as e:
                logger.error(f"Gemini err: {e}")

    def format_response(self, raw_text: str, guest_name: str, date: str, weather_status: str) -> List[DailyItinerary]:
        if self.llm:
            try:
                prompt = JSON_FORMATTER_PROMPT.format(
                    raw_agent_text=raw_text,
                    guest_name=guest_name,
                    date=date,
                    weather=weather_status
                )
                response = invoke_with_timeout(
                    self.llm,
                    prompt,
                    timeout=2.0,
                    fallback=lambda p: None,
                )
                if response is None:
                    raise RuntimeError("LLM timeout")
                text = response.content.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                parsed = json.loads(text)
                
                itinerary_list = []
                for day_data in parsed.get("itinerary", []):
                    items = [ItineraryItem(**item) for item in day_data.get("schedule", [])]
                    itinerary_list.append(DailyItinerary(
                        day_number=day_data.get("day_number", 1),
                        date=day_data.get("date", date),
                        schedule=items
                    ))
                return itinerary_list
            except Exception as e:
                logger.error(f"Response LLM fail: {e}")

        # Fallback text parsing
        schedule_items = []
        current = {}
        for line in raw_text.split("\n"):
            line_strip = line.strip()
            if not line_strip:
                if current and "time_slot" in current and "activity_name" in current:
                    schedule_items.append(ItineraryItem(**current))
                    current = {}
                continue
            if line_strip.startswith("Time:"):
                current["time_slot"] = line_strip.replace("Time:", "").strip()
            elif line_strip.startswith("Activity:"):
                current["activity_name"] = line_strip.replace("Activity:", "").strip()
            elif line_strip.startswith("Type:"):
                current["activity_type"] = line_strip.replace("Type:", "").strip()
            elif line_strip.startswith("Cost:"):
                cost_str = line_strip.replace("Cost:", "").strip()
                try:
                    current["cost"] = float(re.findall(r"[-+]?\d*\.\d+|\d+", cost_str)[0])
                except:
                    current["cost"] = 0.0
            elif line_strip.startswith("Description:"):
                current["description"] = line_strip.replace("Description:", "").strip()
            elif line_strip.startswith("Transit:"):
                transit_str = line_strip.replace("Transit:", "").strip()
                match_time = re.search(r"(\d+\s*mins?)", transit_str)
                match_dist = re.search(r"(\d+\.?\d*\s*km)", transit_str)
                current["travel_time_from_prev"] = match_time.group(1) if match_time else "0 mins"
                current["travel_distance_from_prev"] = match_dist.group(1) if match_dist else "0 km"

        if current and "time_slot" in current and "activity_name" in current:
            schedule_items.append(ItineraryItem(**current))
        if not schedule_items:
            schedule_items = [
                ItineraryItem(
                    time_slot="09:00 AM",
                    activity_name="Hotel Check-in",
                    activity_type="hotel",
                    cost=1500.0,
                    description="Drop off luggage.",
                    travel_time_from_prev="0 mins",
                    travel_distance_from_prev="0 km"
                )
            ]
        return [DailyItinerary(day_number=1, date=date, schedule=schedule_items)]

response_agent = ResponseAgent()
