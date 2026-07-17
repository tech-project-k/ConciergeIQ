from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.models.preferences import Preference
from app.schemas.preferences import PreferenceUpdate, PreferenceResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth/preferences", tags=["preferences"])

@router.get("", response_model=PreferenceResponse)
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.query(Preference).filter(Preference.user_id == current_user.id).first()
    if not pref:
        pref = Preference(
            user_id=current_user.id,
            travel_style="{}",
            dietary_restrictions="",
            accessibility_needs="",
            budget_tier="moderate"
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

@router.put("", response_model=PreferenceResponse)
def update_preferences(payload: PreferenceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.query(Preference).filter(Preference.user_id == current_user.id).first()
    if not pref:
        pref = Preference(user_id=current_user.id)
        db.add(pref)
        
    if payload.travel_style is not None:
        pref.travel_style = payload.travel_style
    if payload.dietary_restrictions is not None:
        pref.dietary_restrictions = payload.dietary_restrictions
    if payload.accessibility_needs is not None:
        pref.accessibility_needs = payload.accessibility_needs
    if payload.budget_tier is not None:
        pref.budget_tier = payload.budget_tier
        
    db.commit()
    db.refresh(pref)
    return pref
