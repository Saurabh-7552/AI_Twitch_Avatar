from pydantic import BaseModel, Field
from enum import Enum
import time
import uuid6

class EventType(Enum):
    CHAT = "CHAT"
    SUB = "SUB"
    RAID = "RAID"
    DEAD_AIR = "DEAD_AIR"
    STREAM_START = "START"

class StandardEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid6.uuid7()))
    session_id: str
    source: str
    type: EventType
    content: str
    priority: int = Field(default=2, ge=1, le=3)
    timestamp: float = Field(default_factory=time.time)