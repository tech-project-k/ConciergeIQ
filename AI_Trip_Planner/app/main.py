from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import engine
from app.database.base import Base
from app.api import auth, chat, trip, preferences, booking
from app.utils.logger import get_logger

logger = get_logger("main")

# Auto-create all database tables on startup
logger.info("Initializing database schema...")
Base.metadata.create_all(bind=engine)
logger.info("Database schema initialized successfully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ConciergeIQ - Production-ready AI Travel Planning Backend Engine",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api path to match frontend paths
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(trip.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(booking.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "ConciergeIQ Generative AI Engine",
        "version": "1.0.0"
    }
