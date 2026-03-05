import asyncio
import logging
import time

from ListenerManager import ListenerCoordinator, TimeListener, SizeListener


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def fake_message_producer(coordinator: ListenerCoordinator) -> None:
    """Produce 40 fake messages, 0.25 seconds apart."""
    for i in range(40):
        msg = {
            "user": "test_user",
            "content": f"msg-{i}",
            "timestamp": time.time(),
        }
        logger.info("[TEST] Produced %s", msg["content"])
        logger.info("[COORDINATOR] Dispatching %s", msg["content"])
        await coordinator.publish(msg)
        await asyncio.sleep(0.25)


async def main() -> None:
    time_listener = TimeListener(flush_interval_seconds=5)
    size_listener = SizeListener(batch_size=10)

    async def time_on_flush(messages: list) -> None:
        logger.info("[TimeListener] Flushed %d messages", len(messages))

    async def size_on_flush(messages: list) -> None:
        logger.info("[SizeListener] Flushed %d messages", len(messages))

    # Override on_flush hooks to log counts only
    time_listener.on_flush = time_on_flush  # type: ignore[assignment]
    size_listener.on_flush = size_on_flush  # type: ignore[assignment]

    coordinator = ListenerCoordinator(time_listener, size_listener)
    await coordinator.start()

    await fake_message_producer(coordinator)

    # Allow time-based flush to trigger after producer finishes
    await asyncio.sleep(6)


if __name__ == "__main__":
    asyncio.run(main())

