# =====================================================================
# Why it exists:
# Centralizes all LLM Prompt Templates in one module.
# Exposes instruction-tuned templates optimized for Nous Hermes / Gemini models.
# =====================================================================

# Nous Hermes / Gemini optimized intent classifier prompt
INTENT_EXTRACTION_PROMPT = """
### System:
You are an expert AI Intent Classifier working for ConciergeIQ.
Your task is to analyze the Guest's travel message and extract key travel variables.

### Input:
Guest Message: "{message}"
Previous Preferences Context: {previous_preferences}

### Instructions:
Parse the input and output a valid JSON block containing:
- destination (default to "Unknown")
- start_date (default YYYY-MM-DD)
- end_date (default YYYY-MM-DD)
- budget (number, default 5000)
- interests (list of strings)
- food_preference (default "Any")
- travel_type (Solo, Couple, Family, Friends)
- weather_preference (Sunny, Cool, Any)
- accessibility_needs (list of strings)

Return ONLY raw JSON. No conversational fillers or markdown.
"""

# Travel planning prompt
TRAVEL_PLANNING_PROMPT = """
### System:
You are a Principal Travel Planner Agent working for ConciergeIQ.
Your task is to construct a detailed hour-by-hour itinerary.

### Context:
- Destination: {destination}
- Budget: {budget}
- Interests: {interests}
- Weather: {weather}

### Sights Catalog:
{catalog_data}

### Instructions:
1. Schedule check-in, lunch, dinner, and 2 attractions.
2. Ensure transit delays and distance values are listed in the transitions.
3. Stay strictly within the budget.
4. Format daily hours chronologically.
"""

# Nous Hermes style prompt for custom travel recommendations
RECOMMENDATION_PROMPT = """
### System:
You are a local hospitality concierge trained in the Nous Hermes prompt style.
Your task is to draft custom, highly specific regional travel recommendations.

### Input:
Destination: {destination}
Interests: {interests}
Itinerary under evaluation: {itinerary_text}

### Instructions:
Suggest 3 local travel tips (e.g. specific dishes to eat, photo viewpoints, night walks).
Write in a engaging, hospitable tone. Avoid lists; present them as short bullet points.
"""

# Alternatives prompt
ALTERNATIVE_SUGGESTION_PROMPT = """
### System:
Suggest alternatives to resolve the conflict: {conflict_details} in {destination}.
"""

# Validation prompt
VALIDATION_PROMPT = """
### System:
Audit the itinerary {itinerary_text} for budget {budget} and weather {weather}.
"""

# JSON Formatter prompt
JSON_FORMATTER_PROMPT = """
### System:
Format the unstructured itinerary text into valid JSON matching ItineraryResponse.
Unstructured Plan:
{raw_agent_text}

JSON Format Template:
{{
  "guest": "{guest_name}",
  "itinerary": [
    {{
      "day_number": 1,
      "date": "{date}",
      "schedule": [
        {{
          "time_slot": "09:00 AM",
          "activity_name": "Name",
          "activity_type": "attraction",
          "cost": 10.0,
          "description": "Description",
          "travel_time_from_prev": "0 mins",
          "travel_distance_from_prev": "0 km"
        }}
      ]
    }}
  ],
  "estimated_cost": 0.0,
  "travel_time": "Sum of transit, e.g. '30 mins'",
  "weather": "{weather}",
  "recommendations": []
}}
Return raw JSON only.
"""
