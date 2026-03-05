from pydantic import BaseModel
from typing import Optional


class NormalizedEvent(BaseModel):
    event_id: str
    event_type: str
    message: Optional[str]
    username: Optional[str]
    timestamp: str

