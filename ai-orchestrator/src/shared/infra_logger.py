import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .contracts import ILogger

class ResponseLogger(ILogger):
    def __init__(self, service_name: str = "Gaffer"):
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def log(self, level: str, message: str, event_id: Optional[str] = None, meta: Dict[str, Any] = None):
        packet = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "correlation_id": event_id,
            "message": message,
            "context": meta or {}
        }
        self.logger.info(json.dumps(packet))