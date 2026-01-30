import asyncio
import sys
import uuid6

sys.path.append("./src")

from src.shared.infra_logger import ResponseLogger
from src.shared.infra_error import BasicErrorHandler
from src.perception.ingestion import TwitchIngestionService
from src.perception.pacer import SystemPacer
from src.perception.router import Switchboard

class MockTwitchConnector:
    """
    Simulates the behavior of the real TwitchConnector.
    Instead of connecting to WebSocket, it just sleeps and yields fake data.
    """
    def __init__(self, queue: asyncio.Queue, ingestor, logger):
        self.queue = queue
        self.ingestor = ingestor
        self.logger = logger

    async def start(self):
        self.logger.log("INFO", "🔌 Connected to MOCK Twitch Server")
        
        # Scenario 1: Wait 2 seconds, then send a Chat
        await asyncio.sleep(2)
        await self._push_fake_event("msg_101", "PRIVMSG", "Why is the defense bad?")

        # Scenario 2: Wait 1 second, send a Sub (Reflex)
        await asyncio.sleep(1)
        await self._push_fake_event("msg_102", "USERNOTICE", "User123 Subscribed!")

        # Scenario 3: Do nothing (Let the Pacer trigger Silence)
        self.logger.log("INFO", "zzz... Twitch going silent (Testing Pacer)...")
        await asyncio.sleep(10) 

    async def _push_fake_event(self, msg_id, msg_type, content):
        raw_data = {"type": msg_type, "id": msg_id, "message": content}
        event = self.ingestor.normalize_packet(raw_data)
        if event:
            await self.queue.put(event)

async def run_pacer_worker(queue: asyncio.Queue, pacer: SystemPacer):
    """Checks for silence every 0.5 seconds."""
    while True:
        await asyncio.sleep(0.5) 
        pulse = pacer.check_pulse()
        if pulse:
            await queue.put(pulse)

async def run_router_worker(queue: asyncio.Queue, router: Switchboard, pacer: SystemPacer):
    """Consumes events from the queue."""
    while True:
        event = await queue.get()
        if event.source == "TWITCH":
            pacer.reset()
        router.route(event)
        queue.task_done()

async def run_demo():
    CURRENT_SESSION_ID = str(uuid6.uuid7())

    logger = ResponseLogger(service_name="DEMO-Gaffer")
    error_handler = BasicErrorHandler(logger)
    event_queue = asyncio.Queue()

    logger.log("INFO", "STARTING ASYNC DEMO", meta={"session_id": CURRENT_SESSION_ID})

    ingestor = TwitchIngestionService(session_id=CURRENT_SESSION_ID)
    pacer = SystemPacer(threshold=4.0, session_id=CURRENT_SESSION_ID) 
    router = Switchboard(logger=logger, error_handler=error_handler)

    logger.log("INFO", "STARTING ASYNC DEMO")

    mock_twitch = MockTwitchConnector(event_queue, ingestor, logger)
    try:
        await asyncio.gather(
            mock_twitch.start(),
            run_pacer_worker(event_queue, pacer),
            run_router_worker(event_queue, router, pacer)
        )
    except KeyboardInterrupt:
        logger.log("INFO", "Demo Stopped")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        pass