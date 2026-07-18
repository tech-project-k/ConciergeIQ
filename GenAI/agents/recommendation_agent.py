# =====================================================================
# Why it exists:
# Offers personalized regional suggestions.
# =====================================================================

from typing import List, Dict, Any
from config.settings import settings
from services.recommendations import recommendations_service
from prompts.templates import RECOMMENDATION_PROMPT
from utils.logger import get_logger
from utils.llm import invoke_with_timeout
from langchain_google_genai import ChatGoogleGenerativeAI

logger = get_logger("recommendation_agent")

class RecommendationAgent:
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

    def generate_recommendations(self, destination: str, interests: List[str], current_itinerary_places: List[str], itinerary_text: str) -> List[str]:
        if self.llm:
            try:
                prompt = RECOMMENDATION_PROMPT.format(
                    destination=destination,
                    interests=", ".join(interests),
                    itinerary_text=itinerary_text
                )
                response = invoke_with_timeout(
                    self.llm,
                    prompt,
                    timeout=2.0,
                    fallback=lambda p: None,
                )
                if response is None:
                    raise RuntimeError("LLM timeout")
                lines = [line.strip().replace("*", "").replace("-", "").strip() for line in response.content.strip().split("\n") if line.strip()]
                return [line for line in lines if len(line) > 10][:4]
            except Exception as e:
                logger.error(f"Gemini fail: {e}")

        # Fallback suggestions
        suggestions = recommendations_service.get_personalized_suggestions(destination, interests, current_itinerary_places)
        recs = [f"Recommended: Visit '{s['name']}' ({s['category']}) - Rated {s['rating']}/5." for s in suggestions]
        if not recs:
            recs = ["Tip: Try regional Andhra traditional meals or authentic biryani."]
        return recs

recommendation_agent = RecommendationAgent()
