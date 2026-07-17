from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PreferenceUpdate(BaseModel):
    travel_style: Optional[str] = None # JSON string
    dietary_restrictions: Optional[str] = None # JSON string
    accessibility_needs: Optional[str] = None # JSON string
    budget_tier: Optional[str] = None # budget, moderate, luxury

class PreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    travel_style: str
    dietary_restrictions: str
    accessibility_needs: str
    budget_tier: str

    class Config:
        from_attributes = True
