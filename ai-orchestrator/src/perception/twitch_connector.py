import asyncio
from twitchio.ext import commands
from src.config import settings
from src.perception.contracts import IIngestionService

class TwitchConnector(commands.Bot):
    def __init__(self, queue: asyncio.Queue, ingestor: IIngestionService, logger):
        super().__init__(
            token=settings.TWITCH_TOKEN,
            prefix="!",
            initial_channels=[settings.TWITCH_CHANNEL]
        )
        self.internal_queue = queue
        self.ingestor = ingestor
        self.logger = logger

    async def event_ready(self):
        self.logger.log("INFO", f"Connected to Twitch as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return
        raw_packet = {
            "type": "PRIVMSG",
            "id": message.id,
            "message": message.content,
            "author": message.author.name,
            "timestamp": message.timestamp.timestamp()
        }

        event = self.ingestor.normalize_packet(raw_packet)
        if event:
            await self.internal_queue.put(event)