# =====================================================================
# Why it exists:
# Automates monument entry tickets or hotel room booking simulations.
# Tracks OpenClaw ticket reservation transaction states.
# =====================================================================

import uuid
from datetime import datetime
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger("booking_service")

class BookingService:
    """
    Simulates ticket and table reservations. Tracks OpenClaw approval flow.
    """
    def __init__(self):
        logger.info("Local Booking engine online.")

    def pre_reserve_ticket(self, place_name: str, booking_type: str, cost: float, is_approved: bool) -> Dict[str, Any]:
        """
        Creates a reservation transaction. Tracks OpenClaw states.
        
        Args:
            place_name (str): Sights or hotel name.
            booking_type (str): hotel, ticket, table.
            cost (float): Booking fee.
            is_approved (bool): If user authorized payment.
            
        Returns:
            Dict[str, Any]: Booking transaction record.
        """
        booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
        
        # OpenClaw Tracker logic
        if is_approved:
            # Shift status from pending to auto-confirmed
            status = f"CLAW-AUTO-{uuid.uuid4().hex[:6].upper()}"
            message = "Booking confirmed and payment processed automatically via OpenClaw."
        else:
            status = "CLAW-PENDING"
            message = "Reservation locked. Waiting for user payment permission/approval."
            
        logger.info(f"Booking registered: {booking_id} for '{place_name}' | Status: {status}")
        
        return {
            "booking_id": booking_id,
            "place_name": place_name,
            "booking_type": booking_type,
            "cost": cost,
            "confirmation_code": status,
            "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        }

booking_service = BookingService()
