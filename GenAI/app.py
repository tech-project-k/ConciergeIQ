# =====================================================================
# Why it exists:
# The entry point of the FastAPI application. Sets up middlewares and 
# aggregates routers.
#
# What it does:
# Boots the FastAPI app, configures CORS, and registers routes.
#
# How it works:
# Standard FastAPI setup, imports APIRouters from `routes/` and registers them.
#
# How it integrates:
# Serves incoming HTTP request calls from the React guest app or Spring Boot.
# =====================================================================

import sys
import os

# Set current path in sys.path to enable local imports to resolve from GenAI folder root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Monkeypatch ForwardRef._evaluate for Python 3.12 compatibility if using Pydantic v1
if sys.version_info >= (3, 12):
    try:
        from typing import ForwardRef
        if hasattr(ForwardRef, '_evaluate'):
            original_evaluate = ForwardRef._evaluate
            def patched_evaluate(self, globalns, localns, *args, **kwargs):
                if len(args) == 1 and isinstance(args[0], (set, frozenset)) and "recursive_guard" not in kwargs:
                    return original_evaluate(self, globalns, localns, None, recursive_guard=args[0])
                return original_evaluate(self, globalns, localns, *args, **kwargs)
            ForwardRef._evaluate = patched_evaluate
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, itinerary, explore, recommendations, health
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("app_entry")

app = FastAPI(
    title="ConciergeIQ GenAI Travel Concierge Engine",
    description="Production-grade AI Travel Planner microservice using Gemini and LangChain.",
    version="1.0.0"
)

# Enable CORS for local React/host execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api
app.include_router(chat.router, prefix="/api")
app.include_router(itinerary.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(health.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "ConciergeIQ GenAI Travel Concierge Engine",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}...")
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
