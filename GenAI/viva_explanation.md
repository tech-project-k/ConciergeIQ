# Project Viva Explanation Document

This document is prepared to help you present this project for your college technical viva examinations. It explains the core concepts, execution flow, design decisions, and system integrations.

---

## 1. Project Overview & Core Concept
**ConciergeIQ GenAI Travel Concierge Engine** is an intelligent travel planning microservice. Unlike traditional travel websites that only search list items, this system acts as a smart consultant:
1. It parses conversational statements to understand user requirements.
2. It fetches weather and coordinates.
3. It validates itineraries to ensure no travel time overlaps and that spending stays inside the budget.
4. It integrates **OpenClaw style booking tracker** to reserve/pay monument tickets automatically.

---

## 2. System Architecture & loose Coupling
We follow **Clean Architecture** and **SOLID Principles**:
- **Single Responsibility**: Each AI agent (Intent, Retriever, Weather, Budget, Planner, Validator, Response) handles exactly one logical check.
- **Dependency Inversion**: Services like Maps and Weather do not depend on the AI agents; they are injected singletons.
- **Liskov Substitution**: The SQLite memory manager can be swapped for an AWS RDS database, or local JSON database storage can be migrated to OpenSearch, with zero impact on the route controllers.

---

## 3. Detailed Step-by-Step Execution Flow
When a guest enters: *"I want to visit Vizag tomorrow under Rs. 5000"*

```
User Prompt (React UI)
  │
  ▼  (HTTP POST /api/chat)
Spring Boot Backend (Orchestrator)
  │
  ▼  (HTTP POST /api/chat)
FastAPI app.py (GenAI Microservice)
  │
  ├── 1. MemoryAgent loads past message turns from SQLite db.
  ├── 2. IntentAgent queries Gemini to extract:
  │      - Destination: "Vizag"
  │      - Budget: 5000.0
  ├── 3. WeatherAgent checks OpenWeather/OpenMeteo for rain forecasts.
  ├── 4. RetrieverAgent pulls regional spots from Vector database.
  ├── 5. PlannerAgent maps out Day 1 hourly travel time slots.
  ├── 6. ValidatorAgent checks for overlaps, rain constraints, & budget limits.
  ├── 7. RecommendationAgent drafts custom Nous Hermes-styled tips.
  └── 8. ResponseAgent converts the plan into structured JSON.
  │
  ▼  (Returns consistent JSON Response)
Spring Boot Backend -> React UI -> Renders itinerary timeline on Screen!
```

---

## 4. Key Java/Python Integrations (React -> Spring Boot -> FastAPI)
1. **React UI**: Captures chat inputs and posts them to `Spring Boot` on port `8080/api/chat`.
2. **Spring Boot Backend**: Serves as the central security and guest profile gateway. It intercepts the call, verifies user credentials, and forwards the chat payload to the `FastAPI GenAI Engine` on port `8085/api/chat`.
3. **FastAPI GenAI Engine**: Uses LangGraph to orchestrate agents, queries Gemini LLM for reasoning, fetches Google Maps transit, and returns a structured JSON itinerary back to Spring Boot, which returns it to the React UI.

---

## 5. Potential AWS Deployment Architecture
For production, the microservice is deployed as:
- **FastAPI container** running on **AWS ECS Fargate** (Serverless container cluster).
- **Postgres/SQLite** migrated to **AWS RDS Aurora**.
- **Vector search** hosted on **AWS OpenSearch Serverless** (highly scalable vector database).
- **React Frontend** hosted on **AWS S3** and distributed globally via **CloudFront CDN**.
