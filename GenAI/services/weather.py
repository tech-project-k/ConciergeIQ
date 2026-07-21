# =====================================================================
# Why it exists:
# Checks weather updates.
#
# What it does:
# Fetches forecast details using OpenWeather or free OpenMeteo.
# =====================================================================

import requests
from typing import Dict, Any
from config.settings import settings
from services.cache import cache_service
from utils.logger import get_logger

logger = get_logger("weather_service")

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY

    def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        cache_key = f"weather_{city.lower()}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        if self.api_key and "YOUR_OPENWEATHER" not in self.api_key:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    d = res.json()
                    desc = d["weather"][0]["description"]
                    temp = d["main"]["temp"]
                    is_rainy = "rain" in desc.lower() or "drizzle" in desc.lower()
                    result = {
                        "city": city,
                        "temperature": f"{temp}°C",
                        "status": "Rainy" if is_rainy else "Sunny/Clear",
                        "description": desc.capitalize(),
                        "is_rainy": is_rainy
                    }
                    cache_service.set(cache_key, result)
                    return result
            except Exception as e:
                logger.error(f"OpenWeather fail: {e}")

        # OpenMeteo fallback via dynamic coordinates
        try:
            from services.location import location_service
            coords_tuple = location_service.get_destination_coordinates(city)
            if coords_tuple:
                lat, lon = coords_tuple
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    curr = res.json().get("current_weather", {})
                    temp = curr.get("temperature", 28)
                    code = curr.get("weathercode", 0)
                    is_rainy = code >= 50
                    result = {
                        "city": city,
                        "temperature": f"{temp}°C",
                        "status": "Rainy" if is_rainy else "Sunny/Clear",
                        "description": "Showers" if is_rainy else "Clear skies",
                        "is_rainy": is_rainy
                    }
                    cache_service.set(cache_key, result)
                    return result
        except Exception as e:
            logger.error(f"OpenMeteo fail: {e}")

        # Mock simulation
        import random
        rain = random.random() < 0.15
        result = {
            "city": city,
            "temperature": "29°C" if not rain else "24°C",
            "status": "Rainy" if rain else "Sunny/Clear",
            "description": "Light drizzle" if rain else "Sunny day",
            "is_rainy": rain
        }
        cache_service.set(cache_key, result)
        return result

weather_service = WeatherService()
