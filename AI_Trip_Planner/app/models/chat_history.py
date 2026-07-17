import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database.connection import Base, GUID

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    trip_id = Column(GUID, nullable=False, index=True)
    role = Column(String, nullable=False) # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
