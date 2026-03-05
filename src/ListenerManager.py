import asyncio
import time
from abc import ABC, abstractmethod


class ListenerManager(ABC):
    """Async abstract base class for managing incoming messages with queue and eviction."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._eviction_task: asyncio.Task | None = None
        self._running = False

    async def add_message(self, message: dict) -> None:
        """Enqueue an incoming message."""
        await self._queue.put(message)

    async def start(self) -> None:
        """Launch the background eviction task."""
        if self._eviction_task is not None:
            return
        self._running = True
        self._eviction_task = asyncio.create_task(self._run_eviction_loop())

    async def _run_eviction_loop(self) -> None:
        """Background loop that repeatedly calls evict_message_bundle."""
        while self._running:
            try:
                await self.evict_message_bundle()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(0.05)

    @abstractmethod
    async def evict_message_bundle(self) -> None:
        """Decide when to drain the queue and flush a bundle. Implement in subclasses."""
        ...

    async def on_flush(self, messages: list) -> None:
        """Hook for AI orchestration after a bundle is evicted. Override as needed."""
        pass


class TimeListener(ListenerManager):
    """Flushes messages on a fixed time interval."""

    def __init__(self, flush_interval_seconds: float):
        super().__init__()
        self.flush_interval_seconds = flush_interval_seconds

    async def evict_message_bundle(self) -> None:
        await asyncio.sleep(self.flush_interval_seconds)
        messages: list = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if messages:
            await self.on_flush(messages)


class SizeListener(ListenerManager):
    """Flushes messages when buffer reaches batch_size."""

    def __init__(self, batch_size: int):
        super().__init__()
        self.batch_size = batch_size
        self._buffer: list = []

    async def evict_message_bundle(self) -> None:
        while True:
            try:
                self._buffer.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if len(self._buffer) >= self.batch_size:
            to_flush = self._buffer
            self._buffer = []
            
            await self.on_flush(to_flush)


class HybridListener(ListenerManager):
    """Flushes when buffer reaches batch_size or flush_interval_seconds elapses."""

    def __init__(self, batch_size: int, flush_interval_seconds: float):
        super().__init__()
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self._buffer: list = []
        self._last_flush_time: float = 0.0

    async def _drain_into_buffer(self) -> None:
        """Move all available messages from queue into buffer."""
        while True:
            try:
                self._buffer.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break

    def _should_flush(self) -> bool:
        """True if we should flush: buffer full or interval elapsed with non-empty buffer."""
        if len(self._buffer) >= self.batch_size:
            return True
        if not self._buffer:
            """if"""
            return False
        elapsed = time.monotonic() - self._last_flush_time
        return elapsed >= self.flush_interval_seconds

    async def _wait_for_batch(self) -> None:
        """Return when buffer size >= batch_size (drains queue while waiting)."""
        while len(self._buffer) < self.batch_size:
            await self._drain_into_buffer()
            if len(self._buffer) >= self.batch_size:
                return
            await asyncio.sleep(0.05)

    async def evict_message_bundle(self) -> None:
        await self._drain_into_buffer()

        if self._should_flush():
            to_flush = self._buffer
            self._buffer = []
            self._last_flush_time = time.monotonic()
            await self.on_flush(to_flush)
            return

        if not self._buffer:
            self._buffer.append(await self._queue.get())
            await self._drain_into_buffer()
            if self._should_flush():
                to_flush = self._buffer
                self._buffer = []
                self._last_flush_time = time.monotonic()
                await self.on_flush(to_flush)
            return

        remaining = self.flush_interval_seconds - (time.monotonic() - self._last_flush_time)
        wait_time = max(0.05, remaining)
        task_time = asyncio.create_task(asyncio.sleep(wait_time))
        task_size = asyncio.create_task(self._wait_for_batch())
        done, pending = await asyncio.wait(
            [task_time, task_size],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        for t in pending:
            try:
                await t
            except asyncio.CancelledError:
                pass


class ListenerCoordinator:
    """Starts multiple listeners and fan-outs published messages to all of them."""

    def __init__(self, *listeners: ListenerManager):
        self._listeners = list(listeners)

    async def start(self) -> None:
        """Start all listeners."""
        await asyncio.gather(*(lst.start() for lst in self._listeners))

    async def publish(self, message: dict) -> None:
        """Fan-out message to all listeners via add_message."""
        await asyncio.gather(*(lst.add_message(message) for lst in self._listeners))


if __name__ == "__main__":
    pass
