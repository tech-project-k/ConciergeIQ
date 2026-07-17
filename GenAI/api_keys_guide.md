# Free API Keys Setup Guide

This guide explains how to obtain developer access and API keys for the ConciergeIQ GenAI Travel Concierge Engine completely for free.

---

## 1. Google Gemini API Key (LLM)
Used by all AI agents for intent classification, travel planning, recommendations, and response formatting.

### How to get it free:
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Log in with your standard Google Gmail account.
3. Click the **"Get API key"** button in the top left sidebar.
4. Click **"Create API key"** and choose to create it in a new Google Cloud project or an existing one.
5. Copy the generated API key (starts with `AIzaSy...`).
6. Paste it into your `GenAI/.env` file:
   ```env
   GEMINI_API_KEY=your_copied_key_here
   ```

---

## 2. OpenWeather API Key (Weather Forecast)
Used by the Weather Agent to fetch real-time rain and climate alerts.

### How to get it free:
1. Go to [OpenWeatherMap Portal](https://openweathermap.org/).
2. Click **"Sign Up"** and create a free account.
3. After registration, go to your account dashboard and select the **"API keys"** tab.
4. A default API key is automatically generated for you.
5. Copy the key and paste it into your `GenAI/.env` file:
   ```env
   OPENWEATHER_API_KEY=your_copied_key_here
   ```
*Note: Free tier allows up to 60 calls per minute, which is more than enough for development.*

---

## 3. Google Maps API Key (Places & Directions)
Used by the Maps Service to find attractions and compute travel times.

### How to get it free:
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Log in with your Google account.
3. Click the **"Select a project"** dropdown in the top bar and click **"New Project"**.
4. Search for and enable the following APIs in the Library tab:
   - **Places API** (to find hotels/attractions)
   - **Directions API** (to compute routing times)
   - **Distance Matrix API** (to compute distances)
5. Go to **APIs & Services > Credentials**.
6. Click **"Create Credentials"** and select **"API Key"**.
7. Copy the key and configure it in your `GenAI/.env` file:
   ```env
   GOOGLE_MAPS_API_KEY=your_copied_key_here
   ```
*Note: Google offers $200 free credit monthly for API usage, which is far more than enough for testing.*

---

## 4. Foursquare Places API Key (Alternative Maps)
An alternative to Google Places.

### How to get it free:
1. Go to [Foursquare Developer Console](https://developer.foursquare.com/).
2. Create a free developer account.
3. Generate an API Key under the project settings.
4. Copy the key and configure it in your `GenAI/.env` file:
   ```env
   FOURSQUARE_API_KEY=your_copied_key_here
   ```
