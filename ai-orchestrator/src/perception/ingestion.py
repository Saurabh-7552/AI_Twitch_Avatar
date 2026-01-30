from typing import Optional
from src.shared.event_types import StandardEvent, EventType
from .contracts import IIngestionService

class TwitchIngestionService(IIngestionService):

    def __init__(self, session_id: str):
        self.session_id = session_id  
    def normalize_packet(self, raw_data: dict) -> Optional[StandardEvent]:
        try:
            e_type = EventType.CHAT
            priority = 2
            
            if raw_data.get("type") == "USERNOTICE":
                e_type = EventType.SUB
                priority = 1
            
            return StandardEvent(
                id=raw_data.get("id"),
                session_id=self.session_id,
                source="TWITCH",
                type=e_type,
                content=raw_data.get("message", "").strip(),
                priority=priority
            )
        except Exception:
            raise ValueError("Malformed Twitch Packet")