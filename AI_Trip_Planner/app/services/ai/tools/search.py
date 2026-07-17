from typing import List, Dict, Any
from app.services.vector_db.store import vector_store

class SearchTools:
    @staticmethod
    def search_hotels(city: str, query: str = "hotel") -> List[Dict[str, Any]]:
        return vector_store.search(query, city, limit=3)

    @staticmethod
    def search_restaurants(city: str, query: str = "food") -> List[Dict[str, Any]]:
        return vector_store.search(query, city, limit=5)

    @staticmethod
    def search_events(city: str, query: str = "event temple movie") -> List[Dict[str, Any]]:
        return vector_store.search(query, city, limit=5)

search_tools = SearchTools()
