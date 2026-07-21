import sys
import os
import json
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from agents.intent_agent import intent_agent
from agents.weather_agent import weather_agent
from agents.retriever_agent import retriever_agent
from agents.planner_agent import planner_agent
from agents.validator_agent import validator_agent
from agents.recommendation_agent import recommendation_agent
from agents.travel_agent import travel_agent
from services.location import location_service
from services.weather import weather_service
from services.maps import maps_service
from vector_db.store import vector_store
from memory.manager import memory_manager
from models.schemas import ChatRequest, ItineraryRequest, Guest, UserLocation

class TestGenAIBackend(unittest.TestCase):
    def test_01_settings_and_keys(self):
        print("\n--- Test 1: Configuration & API Keys ---")
        self.assertTrue(len(settings.GEMINI_API_KEY) > 0, "Gemini API key is configured")
        self.assertTrue(len(settings.GOOGLE_MAPS_API_KEY) > 0, "Google Maps API key is configured")
        self.assertTrue(len(settings.OPENWEATHER_API_KEY) > 0, "OpenWeather API key is configured")
        print("[OK] API keys loaded successfully")

    def test_02_intent_agent_extraction(self):
        print("\n--- Test 2: Intent Agent ---")
        res1 = intent_agent.extract_intent("I want to visit Vizag tomorrow under 6000", {})
        self.assertEqual(res1["destination"], "Vizag")
        self.assertEqual(res1["budget"], 6000.0)

        res2 = intent_agent.extract_intent("Plan a 2 day trip to Goa with beach and food under 8000", {})
        self.assertEqual(res2["destination"], "Goa")
        self.assertEqual(res2["budget"], 8000.0)
        print("[OK] Intent agent extracted pre-seeded & dynamic destinations successfully")

    def test_03_weather_service(self):
        print("\n--- Test 3: Weather Service ---")
        w_vizag = weather_service.get_weather_forecast("Vizag")
        self.assertIn("temperature", w_vizag)

        w_goa = weather_service.get_weather_forecast("Goa")
        self.assertIn("temperature", w_goa)
        print(f"[OK] Weather fetched: Vizag ({w_vizag['temperature']}), Goa ({w_goa['temperature']})")

    def test_04_location_geocoding_and_distance(self):
        print("\n--- Test 4: Location Service ---")
        coords_vizag = location_service.get_destination_coordinates("Vizag")
        self.assertIsNotNone(coords_vizag)

        coords_goa = location_service.get_destination_coordinates("Goa")
        self.assertIsNotNone(coords_goa)

        dist = location_service.calculate_distance_to_destination(17.6868, 83.2185, "Hyderabad")
        self.assertIn("distance", dist)
        print(f"[OK] Geocoding & Distance works: Vizag {coords_vizag}, Goa {coords_goa}")

    def test_05_vector_store_catalog(self):
        print("\n--- Test 5: Vector Store & Retriever ---")
        spots_vizag = retriever_agent.retrieve_context("Vizag", ["Beach"])
        self.assertTrue(len(spots_vizag) > 0)

        spots_goa = retriever_agent.retrieve_context("Goa", ["Beach"])
        self.assertTrue(len(spots_goa) > 0)
        print(f"[OK] Spots retrieved: Vizag ({len(spots_vizag)}), Goa ({len(spots_goa)})")

    def test_06_travel_agent_workflow(self):
        print("\n--- Test 6: Travel Agent Full LangGraph Execution ---")
        session_id = "TEST-SESSION-001"
        res = travel_agent.process_chat_message(
            session_id=session_id,
            message="Plan a trip to Vizag under Rs. 5000 with beach activities",
            user_location={"latitude": 17.6868, "longitude": 83.2185}
        )
        self.assertTrue(res.success)
        self.assertIsNotNone(res.itinerary)
        self.assertTrue(len(res.itinerary) > 0)
        self.assertIsNotNone(res.route_map)
        self.assertTrue(len(res.route_map) > 0)
        print(f"[OK] Travel agent generated plan with {len(res.itinerary[0].schedule)} activities and {len(res.route_map)} map waypoints!")

    def test_07_dynamic_city_travel_agent_workflow(self):
        print("\n--- Test 7: Travel Agent Dynamic Global City Execution ---")
        session_id = "TEST-SESSION-002"
        res = travel_agent.process_chat_message(
            session_id=session_id,
            message="Plan a trip to Goa under Rs. 7000",
            user_location={"latitude": 15.2993, "longitude": 74.1240}
        )
        self.assertTrue(res.success)
        self.assertIsNotNone(res.itinerary)
        self.assertTrue(len(res.itinerary) > 0)
        print("[OK] Dynamic city travel plan executed successfully!")

if __name__ == "__main__":
    unittest.main()
