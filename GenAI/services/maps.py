# =====================================================================
# Why it exists:
# Calculates distances and transit ETAs between itinerary sights.
#
# What it does:
# Connects to Google Maps API or runs local math simulations when credentials are missing.
#
# How it works:
# Uses standard googlemaps client. Fallback computes Haversine formula based on lat/lon.
#
# How it integrates:
# Imported by agents to calculate route times and slots.
# =====================================================================

import math
import googlemaps
from typing import Dict, Any, List, Optional, Tuple
from config.settings import settings
from services.cache import cache_service
from utils.logger import get_logger

logger = get_logger("maps_service")

class MapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.gmaps = None
        if self.api_key and "YOUR_GOOGLE_MAPS" not in self.api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.api_key)
                logger.info("Google Maps client initialized.")
            except Exception as e:
                logger.error(f"Failed to start gmaps client: {e}")
        else:
            logger.info("No Maps Key. Running simulated spatial engine.")

    def get_distance_matrix(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, mode: str = "walking") -> Dict[str, Any]:
        cache_key = f"dist_{origin_lat}_{origin_lon}_{dest_lat}_{dest_lon}_{mode}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        if self.gmaps:
            try:
                matrix = self.gmaps.distance_matrix((origin_lat, origin_lon), (dest_lat, dest_lon), mode=mode)
                if matrix['status'] == 'OK':
                    row = matrix['rows'][0]['elements'][0]
                    if row['status'] == 'OK':
                        result = {
                            "distance": row['distance']['text'],
                            "distance_value_meters": row['distance']['value'],
                            "duration": row['duration']['text'],
                            "duration_value_seconds": row['duration']['value']
                        }
                        cache_service.set(cache_key, result)
                        return result
            except Exception as e:
                logger.error(f"Maps API fail: {e}")

        # Haversine math simulation
        R = 6371.0
        lat1, lon1 = math.radians(origin_lat), math.radians(origin_lon)
        lat2, lon2 = math.radians(dest_lat), math.radians(dest_lon)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c

        speed = 45.0 if mode == "driving" else (25.0 if mode == "transit" else 5.0)
        time_hours = distance_km / speed
        mins = int(time_hours * 60)
        mins = max(mins, 2)

        result = {
            "distance": f"{distance_km:.1f} km",
            "distance_value_meters": int(distance_km * 1000),
            "duration": f"{mins} mins",
            "duration_value_seconds": mins * 60,
            "mode": mode
        }
        cache_service.set(cache_key, result)
        return result

    def geocode(self, location_name: str) -> Optional[tuple[float, float]]:
        """Resolve any city or place name to (latitude, longitude) coordinates."""
        cache_key = f"geocode_{location_name.lower().strip()}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        if self.gmaps:
            try:
                res = self.gmaps.geocode(location_name)
                if res and len(res) > 0:
                    loc = res[0]['geometry']['location']
                    coords = (float(loc['lat']), float(loc['lng']))
                    cache_service.set(cache_key, coords)
                    return coords
            except Exception as e:
                logger.error(f"Google Geocode API fail for '{location_name}': {e}")

        # Fallback to OpenStreetMap Nominatim API
        try:
            import requests
            headers = {'User-Agent': 'ConciergeIQ-GenAI/1.0'}
            url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location_name)}&format=json&limit=1"
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    coords = (float(data[0]['lat']), float(data[0]['lon']))
                    cache_service.set(cache_key, coords)
                    return coords
        except Exception as e:
            logger.warning(f"Nominatim fallback failed for '{location_name}': {e}")

        return None

maps_service = MapsService()
