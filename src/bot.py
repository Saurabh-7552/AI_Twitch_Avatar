import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from twitchio import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


BOT_USERNAME = os.getenv('TWITCH_BOT_USERNAME')
OAUTH_TOKEN = os.getenv('TWITCH_OAUTH_TOKEN')
CHANNEL_NAME = os.getenv('TWITCH_CHANNEL')
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET', '')

# Validate required environment variables
if not all([BOT_USERNAME, OAUTH_TOKEN, CHANNEL_NAME]):
    logger.error("Missing required environment variables. Please check your .env file.")
    logger.error("Required: TWITCH_BOT_USERNAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL")
    sys.exit(1)


class TwitchChatReader(Client):

    
    def __init__(self):

        # Use Client for IRC chat support (TwitchIO 2.x)
        # In TwitchIO 2.x, Client only needs token and initial_channels for IRC
        super().__init__(
            token=OAUTH_TOKEN,
            initial_channels=[CHANNEL_NAME]
        )
        self.channel_name = CHANNEL_NAME
        logger.info(f"Bot initialized for channel: {CHANNEL_NAME}")
    
    async def event_ready(self):
        """
        Called when the bot is ready and connected to Twitch IRC.
        This is where we log the startup message.
        """
        logger.info(f"Bot '{BOT_USERNAME}' is now connected to Twitch!")
        logger.info(f"Monitoring channel: #{CHANNEL_NAME}")
        
        # Verify we're in the channel
        try:
            if hasattr(self, 'connected_channels'):
                channels = list(self.connected_channels)
                if channels:
                    logger.info(f"Successfully joined {len(channels)} channel(s): {[ch.name for ch in channels]}")
                else:
                    logger.warning(f"No channels found in connected_channels")
            else:
                logger.info(f"Monitoring channel: #{CHANNEL_NAME}")
        except Exception as e:
            logger.warning(f"Could not verify channel join: {e}")
        
        logger.info("Ready to read chat messages. Press Ctrl+C to stop.")
    
    async def event_message(self, message):

        # Ignore messages from the bot itself
        if message.echo:
            return
        
        # Check if message has required attributes
        try:
            username = message.author.name if message.author else "Unknown"
            content = message.content if hasattr(message, 'content') else str(message)
            
            # Log the message
            logger.info(f"[{username}]: {content}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)


# shutdown gracefully
bot = None


async def main():
    """
    Main async function that runs the bot.
    """
    global bot
    
    # Create and run the bot
    bot = TwitchChatReader()
    
    try:
        # Start the bot
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\nReceived shutdown signal (Ctrl+C). Shutting down gracefully...")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if bot:
            try:
                await bot.close()
            except Exception as e:
                logger.error(f"Error closing bot: {e}")
        logger.info("Bot disconnected.")


if __name__ == "__main__":

    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
