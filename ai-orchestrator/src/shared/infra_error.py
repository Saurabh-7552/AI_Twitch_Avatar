from .contracts import IErrorHandler, ErrorSeverity, ILogger
from typing import Optional

class BasicErrorHandler(IErrorHandler):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def handle(self, error: Exception, context: str, event_id: Optional[str] = None) -> ErrorSeverity:
        self.logger.log("ERROR", f"Exception in {context}: {str(error)}", event_id=event_id)
        if isinstance(error, ValueError):
            return ErrorSeverity.MINOR
        return ErrorSeverity.CRITICAL