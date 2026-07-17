import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    travel_style = Column(Text, default="{}")  # Stored as JSON string
    dietary_restrictions = Column(Text, default="[]")  # Stored as JSON string
    accessibility_needs = Column(Text, default="[]")  # Stored as JSON string
    budget_tier = Column(String, default="moderate")  # budget, moderate, luxury

    # Relationships
    user = relationship("User", back_populates="preferences")
