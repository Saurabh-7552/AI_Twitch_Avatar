import asyncio
import uuid6
import sys

sys.path.append("./src")

from src.config import settings
from src.shared.infra_logger import ResponseLogger
from src.shared.infra_error import BasicErrorHandler
from src.perception.ingestion import TwitchIngestionService
from src.perception.pacer import SystemPacer
from src.perception.router import Switchboard
from src.perception.twitch_connector import TwitchConnector 


async def run_twitch_listener(queue: asyncio.Queue, ingestor, logger):
    try:
        bot = TwitchConnector(queue=queue, ingestor=ingestor, logger=logger)
        logger.log("INFO", "Connecting to Twitch WebSocket...")
        await bot.start() 
    except Exception as e:
        logger.log("CRITICAL", f"Twitch Connection Failed: {e}")


async def run_pacer_worker(queue: asyncio.Queue, pacer: SystemPacer):
    while True:
        await asyncio.sleep(1) 
        pulse = pacer.check_pulse()
        if pulse:
            await queue.put(pulse) 


async def run_router_worker(queue: asyncio.Queue, router: Switchboard, pacer: SystemPacer):
    while True:
        event = await queue.get()
        if event.source == "TWITCH":
            pacer.reset()
        router.route(event)
        queue.task_done()


async def main():
    CURRENT_SESSION_ID = str(uuid6.uuid7())

    logger = ResponseLogger(service_name="PROD-Gaffer")
    logger.log("INFO", "STARTING SYSTEM", meta={"session_id": CURRENT_SESSION_ID})
    error_handler = BasicErrorHandler(logger)
    
    ingestor = TwitchIngestionService(session_id=CURRENT_SESSION_ID)
    pacer = SystemPacer(threshold=settings.PACER_THRESHOLD, session_id=CURRENT_SESSION_ID)
    router = Switchboard(logger=logger, error_handler=error_handler)
    
    event_queue = asyncio.Queue()
    logger.log("INFO", "STARTING PRODUCTION SYSTEM")
    await asyncio.gather(
        run_twitch_listener(event_queue, ingestor, logger),
        run_pacer_worker(event_queue, pacer),
        run_router_worker(event_queue, router, pacer)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("System Shutting Down...")