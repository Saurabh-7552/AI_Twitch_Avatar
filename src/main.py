import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from twitch_repo.websocket_client import start_websocket


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    logging.info(
        "Env loaded. TWITCH_CLIENT_ID present: %s, TWITCH_CLIENT_SECRET present: %s, TWITCH_CHANNEL: %s",
        bool(os.getenv("TWITCH_CLIENT_ID")),
        bool(os.getenv("TWITCH_CLIENT_SECRET")),
        os.getenv("TWITCH_CHANNEL"),
    )

    asyncio.run(start_websocket())

