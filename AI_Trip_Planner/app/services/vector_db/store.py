import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger

logger = get_logger("vector_store")

class VectorStore:
    def __init__(self):
        # Load lightweight embeddings model (120MB)
        logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # In-memory document storage
        self.documents = []
        self.embeddings = []
        
        # Populate initial database catalog
        self._seed_catalog()

    def _seed_catalog(self):
        # We host regional catalog data for Vizag, Hyderabad, Rajahmundry, and Ravulapalem
        raw_catalog = [
            # 1. Vizag
            {"city": "Vizag", "type": "attraction", "name": "RK Beach Sunrise Walk & Submarine Museum", "address": "Beach Road, Visakhapatnam", "cost": 8.0, "lat": 17.6868, "lon": 83.2185},
            {"city": "Vizag", "type": "attraction", "name": "Kailasagiri Hilltop Ropeway Adventure Tour", "address": "Kailasagiri, Visakhapatnam", "cost": 15.0, "lat": 17.7492, "lon": 83.3421},
            {"city": "Vizag", "type": "attraction", "name": "Sri Varaha Lakshmi Narasimha Temple (Simhachalam)", "address": "Simhachalam Hill, Visakhapatnam", "cost": 10.0, "lat": 17.7664, "lon": 83.2505},
            {"city": "Vizag", "type": "lunch", "name": "Sea Inn Raju Gari Dhaba (Seafood)", "address": "Beach Road, Visakhapatnam", "cost": 10.0, "lat": 17.6890, "lon": 83.2210},
            {"city": "Vizag", "type": "dinner", "name": "The Gateway Hotel Premium Dine", "address": "Beach Road, Pandurangapuram, Vizag", "cost": 45.0, "lat": 17.6850, "lon": 83.2160},
            {"city": "Vizag", "type": "hotel", "name": "Vizag Grand Plaza Heights Hotel", "address": "1 Luxury Road, Vizag", "cost": 80.0, "lat": 17.6868, "lon": 83.2185},
            {"city": "Vizag", "type": "event", "name": "Inox Gajuwaka Movie Screens", "address": "Gajuwaka Main Road, Vizag", "cost": 5.0, "lat": 17.6801, "lon": 83.2012},

            # 2. Hyderabad
            {"city": "Hyderabad", "type": "attraction", "name": "Charminar Heritage Tour & Laad Bazaar", "address": "Old City, Hyderabad", "cost": 10.0, "lat": 17.3616, "lon": 78.4747},
            {"city": "Hyderabad", "type": "attraction", "name": "Golconda Fort Sound & Light Show", "address": "Golconda Fort, Hyderabad", "cost": 12.0, "lat": 17.3833, "lon": 78.4011},
            {"city": "Hyderabad", "type": "lunch", "name": "Paradise Biryani House (Secunderabad)", "address": "Old City, Hyderabad", "cost": 15.0, "lat": 17.3620, "lon": 78.4750},
            {"city": "Hyderabad", "type": "dinner", "name": "Jewel of Nizam - Minar Fine Dining", "address": "Gandipet, Hyderabad", "cost": 75.0, "lat": 17.3670, "lon": 78.3260},
            {"city": "Hyderabad", "type": "hotel", "name": "Hyderabad Comfort Stay Plaza", "address": "1 Luxury Road, Hyderabad", "cost": 110.0, "lat": 17.3850, "lon": 78.4867},
            {"city": "Hyderabad", "type": "event", "name": "Prasads IMAX Movie Multiplex", "address": "NTR Marg, Hyderabad", "cost": 6.0, "lat": 17.4112, "lon": 78.4682},

            # 3. Rajahmundry
            {"city": "Rajahmundry", "type": "attraction", "name": "Godavari Gautami Ghat Riverfront & Pushkar Temple", "address": "Gautami Ghat, Rajahmundry", "cost": 5.0, "lat": 17.0005, "lon": 81.7835},
            {"city": "Rajahmundry", "type": "attraction", "name": "Annavaram Sri Satyanarayana Swami Temple Visit", "address": "Annavaram Road, Rajahmundry", "cost": 12.0, "lat": 17.2790, "lon": 82.4042},
            {"city": "Rajahmundry", "type": "event", "name": "Godavari River Sunset AC Boat Cruise to Papikondalu", "address": "Rajahmundry Boat Launching Point", "cost": 25.0, "lat": 17.0010, "lon": 81.7820},
            {"city": "Rajahmundry", "type": "lunch", "name": "Sri Kanya Andhra Mess (Bamboo Chicken)", "address": "Kotipalli Bus Stand Road, Rajahmundry", "cost": 10.0, "lat": 16.9950, "lon": 81.7850},
            {"city": "Rajahmundry", "type": "dinner", "name": "Hotel Shelton Rajamahendri Fine Dining", "address": "Hariharachandra Prasad Road, Rajahmundry", "cost": 18.0, "lat": 17.0050, "lon": 81.7890},
            {"city": "Rajahmundry", "type": "hotel", "name": "Rajahmundry Grand Royal Palace Resort", "address": "1 Luxury Road, Rajahmundry", "cost": 90.0, "lat": 17.0005, "lon": 81.7835},
            {"city": "Rajahmundry", "type": "event", "name": "Surya Multiplex Movie Theater", "address": "Danavaipeta, Rajahmundry", "cost": 4.5, "lat": 17.0120, "lon": 81.7940},

            # 4. Ravulapalem
            {"city": "Ravulapalem", "type": "attraction", "name": "Gautami Bridge View Point & Coconut Groves", "address": "Gautami Bridge Road, Ravulapalem", "cost": 0.0, "lat": 16.7410, "lon": 81.8497},
            {"city": "Ravulapalem", "type": "event", "name": "Ravulapalem Local Clay Crafts & Nursery Bazaar", "address": "Main Market Area, Ravulapalem", "cost": 10.0, "lat": 16.7420, "lon": 81.8510},
            {"city": "Ravulapalem", "type": "lunch", "name": "Sri Rama Vilas Traditional Meals", "address": "National Highway 16, Ravulapalem", "cost": 6.0, "lat": 16.7400, "lon": 81.8480},
            {"city": "Ravulapalem", "type": "dinner", "name": "Sri Sai Swagath Premium AC Restaurant", "address": "NH-16 Bypass, Ravulapalem", "cost": 12.0, "lat": 16.7430, "lon": 81.8520},
            {"city": "Ravulapalem", "type": "hotel", "name": "Ravulapalem Backpacker Cozy Lodge", "address": "1 Luxury Road, Ravulapalem", "cost": 40.0, "lat": 16.7410, "lon": 81.8497},
            {"city": "Ravulapalem", "type": "event", "name": "Local Theater Cinema Screens", "address": "Main Road, Ravulapalem", "cost": 4.0, "lat": 16.7380, "lon": 81.8462}
        ]
        
        # Generate text description for embeddings
        for entry in raw_catalog:
            desc = f"{entry['name']} in {entry['city']} is a {entry['type']} located at {entry['address']} with cost {entry['cost']} dollars."
            entry["description"] = desc
            self.documents.append(entry)
            
        texts = [doc["description"] for doc in self.documents]
        self.embeddings = self.model.encode(texts, show_progress_bar=False)

    def search(self, query: str, city: str, limit: int = 5) -> list:
        # Filter documents by city first
        city_lower = city.lower()
        indices = [i for i, doc in enumerate(self.documents) if city_lower in doc["city"].lower()]
        
        if not indices:
            # Fallback to general search if city not explicitly found
            indices = list(range(len(self.documents)))
            
        filtered_embeddings = [self.embeddings[i] for i in indices]
        filtered_docs = [self.documents[i] for i in indices]
        
        # Calculate cosine similarity
        query_vector = self.model.encode([query], show_progress_bar=False)[0]
        
        similarities = []
        for vec in filtered_embeddings:
            dot_product = np.dot(query_vector, vec)
            norm_q = np.linalg.norm(query_vector)
            norm_v = np.linalg.norm(vec)
            score = dot_product / (norm_q * norm_v) if norm_q > 0 and norm_v > 0 else 0.0
            similarities.append(score)
            
        # Sort and return closest matches
        sorted_indices = np.argsort(similarities)[::-1]
        results = []
        for idx in sorted_indices[:limit]:
            results.append(filtered_docs[idx])
            
        return results

# Initialize a global singleton
vector_store = VectorStore()
