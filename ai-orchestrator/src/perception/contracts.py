from abc import ABC, abstractmethod
from typing import Optional
from src.shared.event_types import StandardEvent

class IIngestionService(ABC):
    @abstractmethod
    def normalize_packet(self, raw_data: dict) -> Optional[StandardEvent]:
        pass

class IPacer(ABC):
    @abstractmethod
    def check_pulse(self) -> Optional[StandardEvent]:
        pass

class IRouter(ABC):
    @abstractmethod
    def route(self, event: StandardEvent):
        pass