# =====================================================================
# Why it exists:
# Extracts structured variables from guest statements.
# =====================================================================

import json
import re
from typing import Dict, Any
from config.settings import settings
from prompts.templates import INTENT_EXTRACTION_PROMPT
from utils.logger import get_logger
from utils.llm import invoke_with_timeout
from langchain_google_genai import ChatGoogleGenerativeAI

logger = get_logger("intent_agent")

class IntentAgent:
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
                logger.info("Intent Agent Gemini LLM initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini LLM in IntentAgent: {e}")

    def extract_intent(self, message: str, previous_preferences: Dict[str, Any]) -> Dict[str, Any]:
        if self.llm:
            try:
                prompt = INTENT_EXTRACTION_PROMPT.format(
                    message=message,
                    previous_preferences=json.dumps(previous_preferences)
                )
                response = invoke_with_timeout(
                    self.llm,
                    prompt,
                    timeout=8.0,
                    fallback=lambda p: None,
                )
                if response is None:
                    raise RuntimeError("LLM timeout")
                text = response.content.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except Exception as e:
                logger.error(f"Gemini intent extraction failed: {e}")

        # Rule-based fallback
        destination = "Unknown"
        msg_lower = message.lower()
        
        # Check explicit patterns for any location: "to Goa", "visit Tirupati", "in Delhi"
        dest_match = re.search(r'(?:to|visit|in|at|for)\s+([a-zA-Z\s]+?)(?:\s+for|\s+tomorrow|\s+under|\s+budget|\s+with|\s*\d+|\.|\,|$)', msg_lower)
        if dest_match:
            candidate = dest_match.group(1).strip()
            # Strip extra verbs if matched
            candidate = re.sub(r'^(visit|to|in|at|for)\s+', '', candidate, flags=re.I).strip().capitalize()
            ignored_words = ["a", "the", "my", "our", "this", "next", "trip", "vacation", "holiday", "places", "hotels"]
            if candidate.lower() not in ignored_words and len(candidate) > 2:
                destination = candidate

        if destination == "Unknown":
            if "vizag" in msg_lower or "visakhapatnam" in msg_lower:
                destination = "Vizag"
            elif "hyderabad" in msg_lower:
                destination = "Hyderabad"
            elif "rajahmundry" in msg_lower:
                destination = "Rajahmundry"
            elif "ravulapalem" in msg_lower:
                destination = "Ravulapalem"
            elif "goa" in msg_lower:
                destination = "Goa"
            elif "tirupati" in msg_lower:
                destination = "Tirupati"
            elif "delhi" in msg_lower:
                destination = "Delhi"
            elif "mumbai" in msg_lower:
                destination = "Mumbai"
            elif "bangalore" in msg_lower or "bengaluru" in msg_lower:
                destination = "Bangalore"
            else:
                destination = previous_preferences.get("destination", "Unknown")

        budget = previous_preferences.get("budget", 5000.0)
        digits = re.findall(r'\d+', msg_lower)
        if digits:
            try:
                val = float(max(int(d) for d in digits))
                if val > 100:
                    budget = val
            except:
                pass

        interests = previous_preferences.get("interests", [])
        interest_words = ["beach", "temple", "museum", "biryani", "food", "movie", "shopping", "ropeway", "nature", "fort", "resort", "heritage"]
        for word in interest_words:
            if word in msg_lower:
                interests.append(word.capitalize())
        interests = list(set(interests))

        return {
            "destination": destination,
            "start_date": previous_preferences.get("start_date", "2026-07-18"),
            "end_date": previous_preferences.get("end_date", "2026-07-19"),
            "budget": budget,
            "interests": interests if interests else ["Sightseeing"],
            "food_preference": previous_preferences.get("food_preference", "Any"),
            "travel_type": previous_preferences.get("travel_type", "Solo"),
            "weather_preference": previous_preferences.get("weather_preference", "Any"),
            "accessibility_needs": previous_preferences.get("accessibility_needs", [])
        }

intent_agent = IntentAgent()
