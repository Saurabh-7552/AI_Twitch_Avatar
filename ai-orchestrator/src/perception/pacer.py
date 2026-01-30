import time
from typing import Optional
from src.shared.event_types import StandardEvent, EventType
from .contracts import IPacer

class SystemPacer(IPacer):
    def __init__(self, threshold: float, session_id: str):
        self.threshold = threshold
        self.session_id = session_id
        self.last_event_time = time.time()

    def check_pulse(self) -> Optional[StandardEvent]:
        delta = time.time() - self.last_event_time
        if delta > self.threshold:
            self.last_event_time = time.time() 
            return StandardEvent(
                session_id=self.session_id,
                source="PACER",
                type=EventType.DEAD_AIR,
                content="Silence Detected",
                priority=2
            )
        return None
        
    def reset(self):
        self.last_event_time = time.time()