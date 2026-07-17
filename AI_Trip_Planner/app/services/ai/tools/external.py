import math
from typing import Dict, Any

class ExternalTools:
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0 # Earth radius in km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def resolve_transit(distance: float) -> Dict[str, Any]:
        """
        Determines transit mode and duration based on distance.
        """
        if distance > 2.0:
            mode = "driving"
            speed = 35.0 # km/h
            duration = (distance / speed) * 60.0
        elif distance > 0.5:
            mode = "transit"
            speed = 20.0
            duration = (distance / speed) * 60.0 + 5.0 # buffer wait
        else:
            mode = "walking"
            speed = 4.5
            duration = (distance / speed) * 60.0
            
        return {
            "mode": mode,
            "duration_min": round(duration, 1),
            "distance_km": round(distance, 2)
        }

    @staticmethod
    def check_weather(city: str) -> str:
        """
        Mock weather lookup. Returns sunny unless query triggered a stormy status.
        """
        # Can easily read live weather in production
        return "sunny"

external_tools = ExternalTools()
