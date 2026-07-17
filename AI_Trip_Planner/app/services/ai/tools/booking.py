import uuid
from typing import Dict, Any, List

class BookingTool:
    @staticmethod
    def process_booking(activity_name: str, cost: float, is_user_permitted: bool) -> Dict[str, Any]:
        """
        Securely book temple, movie, or event tickets.
        If is_user_permitted is True, it will issue a final confirmation code.
        Otherwise, it registers as PENDING and requests explicit confirmation in the chat.
        """
        if cost <= 0:
            return {"status": "NO_TICKET_REQUIRED", "confirmation_code": None, "warning": None}
            
        if is_user_permitted:
            conf_code = f"CLAW-AUTO-{uuid.uuid4().hex[:6].upper()}"
            return {
                "status": "CONFIRMED",
                "confirmation_code": conf_code,
                "warning": None,
                "detail": f"Successfully secured tickets for '{activity_name}'! Conf Code: {conf_code}."
            }
        else:
            return {
                "status": "PENDING_CONFIRMATION",
                "confirmation_code": "CLAW-PENDING",
                "warning": f"Payment of ${cost:.2f} for '{activity_name}' requires your permission. Say 'Approve booking' or click Approve to finalize payment.",
                "detail": f"Reservation locked. Awaiting user payment permission for '{activity_name}'."
            }

booking_tool = BookingTool()
