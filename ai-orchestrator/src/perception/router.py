from src.shared.contracts import ILogger, IErrorHandler, ErrorSeverity
from src.shared.event_types import StandardEvent, EventType
from .contracts import IRouter

class Switchboard(IRouter):
    def __init__(self, logger: ILogger, error_handler: IErrorHandler):
        self.logger = logger
        self.error_handler = error_handler

    def route(self, event: StandardEvent):
        try:
            self.logger.log("INFO", f"Routing Event: {event.type.name}", event_id=event.id)
            
            if event.type in [EventType.SUB, EventType.RAID]:
                self._dispatch_reflex(event)
            else:
                self._dispatch_deliberation(event)
                
        except Exception as e:
            severity = self.error_handler.handle(e, context="Switchboard.route", event_id=event.id)
            if severity == ErrorSeverity.CRITICAL:
                self.logger.log("ERROR", "!!! CRITICAL SYSTEM FAILURE !!!")

    def _dispatch_reflex(self, event):
        self.logger.log("DEBUG", "Dispatching to Fast Path (Teleprompter)", event_id=event.id)

    def _dispatch_deliberation(self, event):
        self.logger.log("DEBUG", "Dispatching to Slow Path (WritersRoom)", event_id=event.id)