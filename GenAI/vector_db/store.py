# =====================================================================
# Why it exists:
# Acts as the regional travel catalog database.
# =====================================================================

import math
import re
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger("vector_store")

def tokenize(text: str) -> List[str]:
    return re.findall(r'[a-z0-9]+', text.lower())

class SimpleTFIDF:
    def __init__(self, corpus_docs: List[str]):
        self.corpus = [tokenize(doc) for doc in corpus_docs]
        self.num_docs = len(self.corpus)
        
        self.df: Dict[str, int] = {}
        for doc in self.corpus:
            for word in set(doc):
                self.df[word] = self.df.get(word, 0) + 1
                
        self.idf: Dict[str, float] = {}
        for word, count in self.df.items():
            self.idf[word] = math.log((1 + self.num_docs) / (1 + count)) + 1

    def get_tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, int] = {}
        for word in tokens:
            tf[word] = tf.get(word, 0) + 1
            
        vector: Dict[str, float] = {}
        for word, freq in tf.items():
            if word in self.idf:
                vector[word] = freq * self.idf[word]
        return vector

    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[word] * vec2[word] for word in intersection)
        
        sum1 = sum(val**2 for val in vec1.values())
        sum2 = sum(val**2 for val in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return numerator / denominator

class VectorStore:
    def __init__(self):
        logger.info("Initializing pre-seeded Travel Catalog Store...")
        self.documents: List[Dict[str, Any]] = []
        self._seed_catalog()
        
        texts = [doc["description"] for doc in self.documents]
        self.tfidf = SimpleTFIDF(texts)
        self.doc_vectors = [self.tfidf.get_tfidf_vector(tokenize(text)) for text in texts]

    def _seed_catalog(self):
        raw_catalog = [
            {"city": "Vizag", "type": "attraction", "name": "RK Beach Sunrise Walk & Submarine Museum", "address": "Beach Road, Visakhapatnam", "cost": 50.0, "lat": 17.6868, "lon": 83.2185, "category": "Beach/Museum"},
            {"city": "Vizag", "type": "attraction", "name": "Kailasagiri Hilltop Ropeway Adventure Tour", "address": "Kailasagiri, Visakhapatnam", "cost": 150.0, "lat": 17.7492, "lon": 83.3421, "category": "Adventure/Scenic"},
            {"city": "Vizag", "type": "attraction", "name": "Sri Varaha Lakshmi Narasimha Temple (Simhachalam)", "address": "Simhachalam Hill, Visakhapatnam", "cost": 100.0, "lat": 17.7664, "lon": 83.2505, "category": "Culture/Temple"},
            {"city": "Vizag", "type": "lunch", "name": "Sea Inn Raju Gari Dhaba (Seafood)", "address": "Beach Road, Visakhapatnam", "cost": 300.0, "lat": 17.6890, "lon": 83.2210, "category": "Food/Local"},
            {"city": "Vizag", "type": "dinner", "name": "The Gateway Hotel Premium Dine", "address": "Beach Road, Pandurangapuram, Vizag", "cost": 1500.0, "lat": 17.6850, "lon": 83.2160, "category": "Food/Luxury"},
            {"city": "Vizag", "type": "hotel", "name": "Vizag Grand Plaza Heights Hotel", "address": "1 Luxury Road, Vizag", "cost": 3000.0, "lat": 17.6868, "lon": 83.2185, "category": "Accommodation/Hotel"},
            {"city": "Vizag", "type": "event", "name": "Inox Gajuwaka Movie Screens", "address": "Gajuwaka Main Road, Vizag", "cost": 250.0, "lat": 17.6801, "lon": 83.2012, "category": "Entertainment/Movie"},

            {"city": "Hyderabad", "type": "attraction", "name": "Charminar Heritage Tour & Laad Bazaar", "address": "Old City, Hyderabad", "cost": 40.0, "lat": 17.3616, "lon": 78.4747, "category": "Culture/Historical"},
            {"city": "Hyderabad", "type": "attraction", "name": "Golconda Fort Sound & Light Show", "address": "Golconda Fort, Hyderabad", "cost": 150.0, "lat": 17.3833, "lon": 78.4011, "category": "Adventure/Scenic"},
            {"city": "Hyderabad", "type": "lunch", "name": "Paradise Biryani House (Secunderabad)", "address": "Old City, Hyderabad", "cost": 400.0, "lat": 17.3620, "lon": 78.4750, "category": "Food/Local"},
            {"city": "Hyderabad", "type": "dinner", "name": "Jewel of Nizam - Minar Fine Dining", "address": "Gandipet, Hyderabad", "cost": 2500.0, "lat": 17.3670, "lon": 78.3260, "category": "Food/Luxury"},
            {"city": "Hyderabad", "type": "hotel", "name": "Hyderabad Comfort Stay Plaza", "address": "1 Luxury Road, Hyderabad", "cost": 3500.0, "lat": 17.3850, "lon": 78.4867, "category": "Accommodation/Hotel"},
            {"city": "Hyderabad", "type": "event", "name": "Prasads IMAX Movie Multiplex", "address": "NTR Marg, Hyderabad", "cost": 300.0, "lat": 17.4112, "lon": 78.4682, "category": "Entertainment/Movie"},

            {"city": "Rajahmundry", "type": "attraction", "name": "Godavari Gautami Ghat Riverfront & Pushkar Temple", "address": "Gautami Ghat, Rajahmundry", "cost": 50.0, "lat": 17.0005, "lon": 81.7835, "category": "Culture/Scenic"},
            {"city": "Rajahmundry", "type": "attraction", "name": "Annavaram Sri Satyanarayana Swami Temple Visit", "address": "Annavaram Road, Rajahmundry", "cost": 150.0, "lat": 17.2790, "lon": 82.4042, "category": "Culture/Temple"},
            {"city": "Rajahmundry", "type": "lunch", "name": "Sri Kanya Andhra Mess (Bamboo Chicken)", "address": "Kotipalli Bus Stand Road, Rajahmundry", "cost": 300.0, "lat": 16.9950, "lon": 81.7850, "category": "Food/Local"},
            {"city": "Rajahmundry", "type": "dinner", "name": "Hotel Shelton Rajamahendri Fine Dining", "address": "Hariharachandra Prasad Road, Rajahmundry", "cost": 1000.0, "lat": 17.0050, "lon": 81.7890, "category": "Food/Luxury"},
            {"city": "Rajahmundry", "type": "hotel", "name": "Rajahmundry Grand Royal Palace Resort", "address": "1 Luxury Road, Rajahmundry", "cost": 2800.0, "lat": 17.0005, "lon": 81.7835, "category": "Accommodation/Hotel"},
            {"city": "Rajahmundry", "type": "event", "name": "Surya Multiplex Movie Theater", "address": "Danavaipeta, Rajahmundry", "cost": 200.0, "lat": 17.0120, "lon": 81.7940, "category": "Entertainment/Movie"},

            {"city": "Ravulapalem", "type": "attraction", "name": "Gautami Bridge View Point & Coconut Groves", "address": "Gautami Bridge Road, Ravulapalem", "cost": 0.0, "lat": 16.7410, "lon": 81.8497, "category": "Nature/Scenic"},
            {"city": "Ravulapalem", "type": "event", "name": "Ravulapalem Local Clay Crafts & Nursery Bazaar", "address": "Main Market Area, Ravulapalem", "cost": 100.0, "lat": 16.7420, "lon": 81.8510, "category": "Culture/Shopping"},
            {"city": "Ravulapalem", "type": "lunch", "name": "Sri Rama Vilas Traditional Meals", "address": "National Highway 16, Ravulapalem", "cost": 150.0, "lat": 16.7400, "lon": 81.8480, "category": "Food/Local"},
            {"city": "Ravulapalem", "type": "dinner", "name": "Sri Sai Swagath Premium AC Restaurant", "address": "NH-16 Bypass, Ravulapalem", "cost": 400.0, "lat": 16.7430, "lon": 81.8520, "category": "Food/Standard"},
            {"city": "Ravulapalem", "type": "hotel", "name": "Ravulapalem Backpacker Cozy Lodge", "address": "1 Luxury Road, Ravulapalem", "cost": 1200.0, "lat": 16.7410, "lon": 81.8497, "category": "Accommodation/Hotel"}

        ]
        for entry in raw_catalog:
            desc = f"{entry['name']} located in {entry['city']} is a {entry['type']} ({entry['category']}) with price {entry['cost']} and address: {entry['address']}."
            entry["description"] = desc
            self.documents.append(entry)

    def search_catalog(self, query: str, city: str, limit: int = 8) -> List[Dict[str, Any]]:
        city_lower = city.lower().strip()
        indices = [i for i, doc in enumerate(self.documents) if city_lower in doc["city"].lower()]
        
        # If target city is not pre-seeded, dynamically generate catalog entries for this city
        if not indices and city_lower != "unknown":
            self._generate_dynamic_city_catalog(city)
            indices = [i for i, doc in enumerate(self.documents) if city_lower in doc["city"].lower()]
            
        if not indices:
            indices = list(range(len(self.documents)))

        filtered_vectors = [self.doc_vectors[i] for i in indices]
        filtered_docs = [self.documents[i] for i in indices]
        
        query_vector = self.tfidf.get_tfidf_vector(tokenize(query))
        similarities = []
        for vec in filtered_vectors:
            score = self.tfidf.cosine_similarity(query_vector, vec)
            similarities.append(score)
            
        sorted_indices = [idx for _, idx in sorted(zip(similarities, range(len(similarities))), reverse=True)]
        results = []
        for idx in sorted_indices[:limit]:
            results.append(filtered_docs[idx])
        return results

    def _generate_dynamic_city_catalog(self, city: str):
        from services.location import location_service
        coords = location_service.get_destination_coordinates(city)
        lat = coords[0] if coords else 17.6868
        lon = coords[1] if coords else 83.2185
        
        city_title = city.capitalize()
        dynamic_spots = [
            {"city": city_title, "type": "attraction", "name": f"{city_title} Heritage & Landmark Tour", "address": f"Center Area, {city_title}", "cost": 100.0, "lat": lat + 0.005, "lon": lon + 0.005, "category": "Culture/Historical"},
            {"city": city_title, "type": "attraction", "name": f"{city_title} Scenic View Point & Park", "address": f"Hill View, {city_title}", "cost": 50.0, "lat": lat - 0.004, "lon": lon + 0.003, "category": "Nature/Scenic"},
            {"city": city_title, "type": "attraction", "name": f"{city_title} Regional Temple / Cathedral", "address": f"Main Road, {city_title}", "cost": 0.0, "lat": lat + 0.002, "lon": lon - 0.004, "category": "Culture/Religious"},
            {"city": city_title, "type": "lunch", "name": f"{city_title} Traditional Flavors Restaurant", "address": f"Market Square, {city_title}", "cost": 350.0, "lat": lat - 0.002, "lon": lon - 0.002, "category": "Food/Local"},
            {"city": city_title, "type": "dinner", "name": f"{city_title} Premium Rooftop Dining", "address": f"High Street, {city_title}", "cost": 1200.0, "lat": lat + 0.003, "lon": lon + 0.001, "category": "Food/Luxury"},
            {"city": city_title, "type": "hotel", "name": f"{city_title} Grand Comfort Stay Hotel", "address": f"Station Road, {city_title}", "cost": 2500.0, "lat": lat, "lon": lon, "category": "Accommodation/Hotel"},
            {"city": "city_title", "type": "event", "name": f"{city_title} Cultural Show & Shopping Market", "address": f"Mall Road, {city_title}", "cost": 200.0, "lat": lat - 0.005, "lon": lon + 0.006, "category": "Entertainment/Shopping"}
        ]
        
        for entry in dynamic_spots:
            desc = f"{entry['name']} located in {entry['city']} is a {entry['type']} ({entry['category']}) with price {entry['cost']} and address: {entry['address']}."
            entry["description"] = desc
            self.documents.append(entry)
            
        # Re-index TF-IDF
        texts = [doc["description"] for doc in self.documents]
        self.tfidf = SimpleTFIDF(texts)
        self.doc_vectors = [self.tfidf.get_tfidf_vector(tokenize(text)) for text in texts]

vector_store = VectorStore()
