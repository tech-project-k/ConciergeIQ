# =====================================================================
# Why it exists:
# Streamlit Test Web Interface for the GenAI Travel Concierge Engine.
# Allows developers and examiners to test the workflow of your role.
#
# What it does:
# Connects to your running FastAPI backend on port 8085 and renders an 
# interactive chat UI, itinerary timeline renderer, and places search.
#
# How it works:
# Uses streamlit library to construct a frontend in pure Python, posting 
# inputs to FastAPI REST endpoints and displaying returned JSON.
#
# How it integrates:
# Binds directly to http://127.0.0.1:8085. Runs independently.
# =====================================================================

import streamlit as st
import requests
import uuid
import pandas as pd

# Set up Streamlit Page configurations
st.set_page_config(
    page_title="ConciergeIQ AI Concierge Panel",
    page_icon="✈️",
    layout="wide"
)

# Render Premium Page Styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .itinerary-card {
        background-color: #F3F4F6;
        padding: 1.2rem;
        border-radius: 0.8rem;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .time-badge {
        background-color: #3B82F6;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 0.4rem;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# App title header
st.markdown('<div class="main-header">ConciergeIQ Travel Concierge</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">GenAI Multi-Agent Travel Planner Interactive Test Panel</div>', unsafe_allow_html=True)

# Retrieve backend base URL
BACKEND_URL = "http://127.0.0.1:8085/api"

# Initialize Session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = f"STRML-{uuid.uuid4().hex[:6].upper()}"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_itinerary" not in st.session_state:
    st.session_state.last_itinerary = None
if "last_cost" not in st.session_state:
    st.session_state.last_cost = 0.0
if "last_weather" not in st.session_state:
    st.session_state.last_weather = "Unknown"
if "last_alerts" not in st.session_state:
    st.session_state.last_alerts = []
if "last_map_points" not in st.session_state:
    st.session_state.last_map_points = []

# Sidebar configurations
with st.sidebar:
    st.header("⚙️ Session Controls")
    st.info(f"**Session ID:** {st.session_state.session_id}")
    
    if st.button("🔄 Reset Chat Session"):
        st.session_state.session_id = f"STRML-{uuid.uuid4().hex[:6].upper()}"
        st.session_state.chat_history = []
        st.session_state.last_itinerary = None
        st.session_state.last_cost = 0.0
        st.session_state.last_weather = "Unknown"
        st.session_state.last_alerts = []
        st.session_state.last_map_points = []
        st.rerun()

    st.markdown("---")
    st.subheader("� Current Location")
    current_lat = st.number_input("Latitude", value=17.6868, format="%.6f")
    current_lon = st.number_input("Longitude", value=83.2185, format="%.6f")

    st.markdown("---")
    st.subheader("�� Catalog Explorer")
    explore_city = st.selectbox("Select City", ["Vizag", "Hyderabad", "Rajahmundry", "Ravulapalem"," Visakhapatnam","araku", "srisailam", "tirupati", "vijayawada", "warangal", "kurnool", "guntur", "nellore", "anantapur", "kadapa", "chittoor", "eluru", "tenali", "ongole", "proddatur", "bhimavaram", "machilipatnam", "tiruvuru", "nandyal", "sattenapalle", "bapatla", "narasaraopet", "gudivada", "tenali", "srikakulam", "vizianagaram", "kakinada", "rajahmundry", "srikalahasti", "tirupati", "chittoor", "kadapa", "anantapur", "kurnool", "nellore", "guntur", "vijayawada", "warangal", "khammam", "nalgonda", "mahbubnagar", "adoni", "tenali", "ongole","himachal pradesh", "uttarakhand", "rajasthan", "gujarat", "maharashtra", "karnataka", "tamil nadu", "kerala", "goa", "punjab", "haryana", "bihar", "jharkhand", "odisha", "west bengal", "assam", "manipur", "mizoram", "nagaland", "tripura","meghalaya", "sikkim", "arunachal pradesh", "chhattisgarh", "madhya pradesh", "uttar pradesh", "jammu and kashmir", "ladakh", "andaman and nicobar islands", "lakshadweep", "daman and diu", "dadra and nagar haveli", "puducherry", "chandigarh", "delhi", "jharkhand", "bihar", "west bengal", "assam", "meghalaya", "mizoram", "nagaland", "tripura", "sikkim", "arunachal pradesh","bengaluru", "mumbai", "delhi", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "pimpri-chinchwad", "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot", "kalyan-dombivli", "vasai-virar", "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar", "navi mumbai", "allahabad", "ranchi", "howrah", "coimbatore", "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai", "raipur", "kota", "guwahati", "chandigarh","india", "pakistan", "nepal", "bhutan", "bangladesh", "sri lanka", "maldives", "afghanistan", "iran", "iraq", "saudi arabia", "uae", "qatar", "kuwait", "bahrain", "oman", "yemen", "turkey", "egypt", "morocco", "tunisia", "algeria", "libya", "sudan", "ethiopia", "kenya", "tanzania", "uganda", "rwanda", "burundi", "zambia", "zimbabwe", "botswana", "namibia", "south africa", "lesotho", "swaziland"])
    explore_type = st.selectbox("Category", ["attraction", "hotel", "lunch", "dinner", "event", "shopping", "cultural", "nature", "adventure", "historical", "religious", "beach", "mountain", "desert", "forest", "wildlife", "spa", "nightlife", "sports", "festival", "art gallery", "museum", "theater", "concert", "zoo", "aquarium", "amusement park", "water park", "botanical garden", "national park", "hiking trail", "cycling route", "ski resort", "surfing spot", "diving site", "snorkeling site", "kayaking spot", "rafting spot", "paragliding site", "hot air balloon site", "camping site", "glamping site", "vineyard", "winery", "brewery", "distillery", "coffee shop", "tea house", "chocolate factory", "cheese factory", "farmers market", "street food market", "food festival", "wine festival", "beer festival", "music festival", "film festival", "literature festival", "fashion show", "cultural show"])
    
    if st.button("Explore Places"):
        try:
            res = requests.post(f"{BACKEND_URL}/explore", json={
                "city": explore_city,
                "place_type": explore_type
            })
            if res.status_code == 200:
                places = res.json().get("places", [])
                st.write(f"Found {len(places)} places:")
                for p in places:
                    st.markdown(f"**🏨 {p['name']}**")
                    st.caption(f"Address: {p['address']} | Cost: Rs. {p['cost']}")
            else:
                st.error("FastAPI backend is offline or returned error.")
        except Exception as e:
            st.error(f"Could not connect to FastAPI: {e}")

# Construct layout layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 AI Concierge Chatbox")
    
    # Render chat messaging log
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
            
    # Chat input box
    user_input = st.chat_input("Enter travel request (e.g. I want to visit Vizag tomorrow under Rs. 6000)")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        # Post request to FastAPI chat endpoint
        try:
            with st.spinner("GenAI LangGraph Agents thinking..."):
                response = requests.post(f"{BACKEND_URL}/chat", json={
                    "session_id": st.session_state.session_id,
                    "message": user_input,
                    "user_location": {
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "city": "Current Location",
                        "address": "User entered location"
                    }
                })
                
            if response.status_code == 200:
                data = response.json()
                assistant_text = data.get("response", "")
                
                # Save results to session state
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_text})
                st.session_state.last_itinerary = data.get("itinerary")
                st.session_state.last_cost = data.get("estimated_cost", 0.0)
                st.session_state.last_weather = data.get("weather_summary", "Unknown")
                st.session_state.last_alerts = data.get("booking_alerts", [])
                st.session_state.last_map_points = data.get("route_map", [])
                
                st.rerun()
            else:
                st.error("Error from GenAI backend.")
        except Exception as e:
            st.error(f"Failed to connect to FastAPI backend at {BACKEND_URL}/chat. Make sure uvicorn is running: {e}")

with col2:
    st.subheader("📅 Generated Itinerary Timeline")
    
    if st.session_state.last_itinerary:
        st.metric(label="Total Estimated Cost", value=f"Rs. {st.session_state.last_cost:.2f}")
        st.info(f"⛅ **Weather Forecast:** {st.session_state.last_weather}")
        
        # Display alerts
        if st.session_state.last_alerts:
            for alert in st.session_state.last_alerts:
                st.warning(alert)
                
        if st.session_state.last_map_points:
            map_df = pd.DataFrame([
                {"lat": point.get("latitude"), "lon": point.get("longitude"), "name": point.get("name", "Point")}
                for point in st.session_state.last_map_points
                if point.get("latitude") is not None and point.get("longitude") is not None
            ])
            if not map_df.empty:
                st.subheader("🗺️ Travel Map")
                st.map(map_df)
                for point in st.session_state.last_map_points:
                    st.caption(f"{point.get('name', 'Point')} — {point.get('type', 'stop')}")

        # Render timeline schedule items
        for day in st.session_state.last_itinerary:
            st.markdown(f"### 🗓️ Day {day['day_number']} - {day['date']}")
            for item in day["schedule"]:
                st.markdown(f"""
                <div class="itinerary-card">
                    <span class="time-badge">{item['time_slot']}</span>
                    <h4 style="margin: 0.5rem 0 0.2rem 0; color: #1F2937;">{item['activity_name']}</h4>
                    <p style="margin: 0; font-size: 0.9rem; color: #4B5563;">{item['description']}</p>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #6B7280;">
                        💰 Cost: Rs. {item['cost']} | 🚗 Transit: {item['travel_time_from_prev']} ({item['travel_distance_from_prev']})
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render OpenClaw booking badges
                if item.get("booking_confirmation_code"):
                    code = item["booking_confirmation_code"]
                    if "PENDING" in code:
                        st.error(f"🔴 OpenClaw Status: {code} (Waiting for Payment approval)")
                    else:
                        st.success(f"🟢 OpenClaw Status: {code} (Payment Secured)")
    else:
        st.info("Your generated hour-by-hour itinerary timeline, maps transit values, and budget tracker details will appear here after you type a travel request in the chatbox.")
