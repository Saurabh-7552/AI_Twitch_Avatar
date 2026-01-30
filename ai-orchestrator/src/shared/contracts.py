from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

class ErrorSeverity(Enum):
    MINOR = "MINOR"
    RETRY = "RETRY"
    CRITICAL = "CRITICAL"

class ILogger(ABC):
    @abstractmethod
    def log(self, level: str, message: str, event_id: Optional[str] = None):
        pass

class IErrorHandler(ABC):
    @abstractmethod
    def handle(self, error: Exception, context: str) -> ErrorSeverity:
        pass