# =====================================================================
# Why it exists:
# Calculates travel distance & time from user's current location to destination.
#
# What it does:
# Uses Google Maps API or Haversine formula for distance calculations.
# Provides travel suggestions based on current location vs destination.
#
# How it works:
# Accepts user's lat/lon and destination city, returns transit details.
#
# How it integrates:
# Imported by intent_agent to provide travel context in LangGraph workflow.
# =====================================================================

import math
from typing import Dict, Any, Optional, Tuple
from config.settings import settings
from services.cache import cache_service
from services.maps import maps_service
from utils.logger import get_logger

logger = get_logger("location_service")

# Destination city center coordinates
DESTINATION_COORDS = {
    "vizag": (17.6868, 83.2185),
    "visakhapatnam": (17.6868, 83.2185),
    "hyderabad": (17.3850, 78.4867),
    "rajahmundry": (17.0005, 81.7835),
    "ravulapalem": (16.7410, 81.8497),
    "kakinada": (16.9891, 82.2475),
    "tirupati": (13.6288, 79.4192),
    "vijayawada": (16.5062, 80.6480),
    "guntur": (16.3067, 80.4365),
    "anantapur": (14.6810, 77.6000),
    "nellore": (14.4426, 79.9865),
    "chittoor": (13.2172, 79.1000),
    "kadapa": (14.4670, 78.8242),
    "ongole": (15.5057, 80.0499),
    "srikakulam": (18.2964, 83.8938),
    "eluru": (16.7107, 81.0952),
    "tenali": (16.2390, 80.6400),
    "proddatur": (14.7500, 78.5500),
    "tiruvuru": (16.9000, 80.0000),
    "bapatla": (15.9000, 80.4700),
    "nandyal": (15.5000, 78.4833),
    "srikalahasti": (13.7500, 79.7000),
    "pithapuram": (17.1167, 82.2667),
    "mandapeta": (16.8000, 81.9000),
    "sattenapalle": (16.4000, 80.2000),
    "tenkasi": (8.9600, 77.3200),
    "tiruchendur": (8.5000, 78.1000),
    "tirunelveli": (8.7000, 77.7000),
    "madurai": (9.9252, 78.1198),
    "coimbatore": (11.0168, 76.9558),
    "salem": (11.6643, 78.1460),
    "erode": (11.3410, 77.7172),
    "tiruppur": (11.1085, 77.3411),
    "karur": (10.9601, 78.0766),
    "dindigul": (10.3670, 77.9800),
    "namakkal": (11.2200, 78.1700),
    "vellore": (12.9165, 79.1325),
    "thanjavur": (10.7867, 79.1378),
    "kumbakonam": (10.9600, 79.4000),
    "tiruvannamalai": (12.2253, 79.0747),
    "pondicherry": (11.9416, 79.8083),
    "chennai": (13.0827, 80.2707),
    "bangalore": (12.9716, 77.5946),
    "mysore": (12.2958, 76.6394),
    "coorg": (12.3375, 75.8069),
    "mangalore": (12.9141, 74.8560),
    "udupi": (13.3409, 74.7421),
    "manipal": (13.3560, 74.7860),
    "shimoga": (13.9299, 75.5681),
    "hassan": (13.0050, 76.1025),
    "chikmagalur": (13.3167, 75.7740),
    "gulbarga": (17.3297, 76.8343),
    "bellary": (15.1394, 76.9214),
    "bijapur": (16.8300, 75.7100),
    "bimavaram": (16.9000, 82.2500),
    "palakollu": (16.5167, 81.7333),
    "narasapur": (16.4333, 81.7000),
    "bhimavaram": (16.5333, 81.5333),
    "eluru": (16.7000, 81.1000),
    "tenali": (16.2390, 80.6400),
    "proddatur": (14.7500, 78.5500),
    "himacala": (30.0000, 78.0000),
    "kolkata": (22.5726, 88.3639),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "pune": (18.5204, 73.8567),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "amritsar": (31.6340, 74.8723),
    "chandigarh": (30.7333, 76.7794),
    
}

class LocationService:
    def get_destination_coordinates(self, destination: str) -> Optional[Tuple[float, float]]:
        normalized = destination.lower()
        return DESTINATION_COORDS.get(normalized)

    def calculate_distance_to_destination(
        self, 
        user_lat: float, 
        user_lon: float, 
        destination: str
    ) -> Dict[str, Any]:
        """Calculate distance and estimated travel time from user's location to destination city."""
        
        cache_key = f"loc_{user_lat:.4f}_{user_lon:.4f}_{destination.lower()}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        dest_coords = DESTINATION_COORDS.get(destination.lower())
        if not dest_coords:
            return {
                "error": f"Unknown destination: {destination}",
                "distance": "Unknown",
                "duration": "Unknown",
                "distance_km": 0
            }

        dest_lat, dest_lon = dest_coords
        
        # Try Google Maps first
        try:
            route_data = maps_service.get_distance_matrix(
                user_lat, user_lon, dest_lat, dest_lon, mode="driving"
            )
            result = {
                "user_location": {"latitude": user_lat, "longitude": user_lon},
                "destination": destination,
                "destination_coords": {"latitude": dest_lat, "longitude": dest_lon},
                "distance": route_data["distance"],
                "distance_km": route_data["distance_value_meters"] / 1000,
                "duration": route_data["duration"],
                "duration_minutes": route_data["duration_value_seconds"] / 60,
                "source": "google_maps"
            }
            cache_service.set(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"Google Maps calculation failed: {e}. Using Haversine.")

        # Fallback: Haversine formula
        R = 6371.0  # Earth's radius in km
        lat1, lon1 = math.radians(user_lat), math.radians(user_lon)
        lat2, lon2 = math.radians(dest_lat), math.radians(dest_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c

        # Estimate time (avg 60 km/h for driving)
        hours = distance_km / 60
        minutes = int(hours * 60)

        result = {
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "destination": destination,
            "destination_coords": {"latitude": dest_lat, "longitude": dest_lon},
            "distance": f"{distance_km:.1f} km",
            "distance_km": distance_km,
            "duration": f"{minutes} mins",
            "duration_minutes": minutes,
            "source": "haversine_formula"
        }
        cache_service.set(cache_key, result)
        return result

    def get_nearest_destination(self, user_lat: float, user_lon: float) -> Dict[str, Any]:
        """Find nearest destination city from user's current location."""
        
        min_distance = float('inf')
        nearest_dest = None
        
        for dest_name, (dest_lat, dest_lon) in DESTINATION_COORDS.items():
            # Haversine calculation
            R = 6371.0
            lat1, lon1 = math.radians(user_lat), math.radians(user_lon)
            lat2, lon2 = math.radians(dest_lat), math.radians(dest_lon)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c
            
            if distance < min_distance:
                min_distance = distance
                nearest_dest = dest_name
        
        return {
            "nearest_destination": nearest_dest,
            "distance_km": min_distance,
            "user_location": {"latitude": user_lat, "longitude": user_lon}
        }

location_service = LocationService()
