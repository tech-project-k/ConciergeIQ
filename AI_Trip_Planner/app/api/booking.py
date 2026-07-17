from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
import uuid
from app.database.connection import get_db
from app.models.itinerary import Activity
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/bookings", tags=["bookings"])

class BookingConfirmRequest(BaseModel):
    activity_id: UUID
    approve: bool

@router.post("")
def confirm_booking(payload: BookingConfirmRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.id == payload.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    if payload.approve:
        conf_code = f"CLAW-AUTO-{uuid.uuid4().hex[:6].upper()}"
        activity.booking_confirmation_code = conf_code
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return {
            "status": "CONFIRMED",
            "confirmation_code": conf_code,
            "message": f"Successfully secured and paid reservation for '{activity.name}'!"
        }
    
    return {"status": "PENDING"}
