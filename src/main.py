import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import signal
import sys
import logging
from typing import Optional
from datetime import datetime

from config import config
from status_checker import StatusChecker
from utils.embed_utils import create_status_embed, create_incident_embed

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatusBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.status_checker = StatusChecker()
        self.status_message_id: Optional[int] = None
        self.scheduler = AsyncIOScheduler()
        
        # Register event handlers
        self.setup_events()
        
    def setup_events(self):
        @self.event
        async def on_ready():
            logger.info(f"Bot is ready! Logged in as {self.user}")
            self.setup_status_checking()
            
        @self.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Error in {event}", exc_info=sys.exc_info())

    async def update_status_message(self, channel: discord.TextChannel, current_state: dict):
        """Update or create status message."""
        status_embed = create_status_embed(current_state)
        
        try:
            if self.status_message_id:
                try:
                    status_message = await channel.fetch_message(self.status_message_id)
                    await status_message.edit(embed=status_embed)
                    logger.info("Status monitor message updated")
                except discord.NotFound:
                    logger.warning("Could not find status message, creating new one")
                    new_message = await channel.send(embed=status_embed)
                    self.status_message_id = new_message.id
            else:
                new_message = await channel.send(embed=status_embed)
                self.status_message_id = new_message.id
                logger.info(f"Created status monitor message: {self.status_message_id}")
        except Exception as e:
            logger.error(f"Error updating status message: {str(e)}")
            new_message = await channel.send(embed=status_embed)
            self.status_message_id = new_message.id

    async def handle_new_incidents(self, channel: discord.TextChannel, updates: list):
        """Handle and send new incident notifications."""
        if not isinstance(updates, list):
            return
            
        for update in updates:
            if update['type'] == 'new_incident':
                await channel.send(embed=create_incident_embed(update['incident']))
                logger.info("Sent new incident notification")

    async def handle_status_update(self, current_state: dict, updates: Optional[list]):
        """Handle status updates and send notifications."""
        try:
            logger.info("Handling status update")
            channel = await self.fetch_channel(int(config.discord.channel_id))
            
            if not channel:
                logger.error(f"Could not find channel: {config.discord.channel_id}")
                return

            await self.update_status_message(channel, current_state)
            
            if updates and updates[0]['type'] != 'initial':
                await self.handle_new_incidents(channel, updates)
                
        except Exception as e:
            logger.error(f"Error handling status update: {str(e)}")

    def setup_status_checking(self):
        """Setup periodic status checking."""
        async def check_status():
            try:
                updates = await self.status_checker.check_for_updates()
                current_state = self.status_checker.get_current_state()
                await self.handle_status_update(current_state, updates)
            except Exception as e:
                logger.error(f"Error checking status: {str(e)}")

        logger.info(
            "Setting up status monitoring",
            extra={
                'interval': config.discord.check_interval,
                'channel_id': config.discord.channel_id
            }
        )

        # Schedule status checks
        self.scheduler.add_job(
            check_status,
            'interval',
            minutes=config.discord.check_interval,
            next_run_time=datetime.now()
        )
        self.scheduler.start()

    async def close(self):
        """Clean up resources on shutdown."""
        logger.info("Shutting down bot...")
        self.scheduler.shutdown()
        await super().close()

def setup_signal_handlers(bot: StatusBot):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}. Initiating graceful shutdown...")
        asyncio.create_task(bot.close())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for the bot."""
    try:
        # Create and setup bot
        bot = StatusBot()
        setup_signal_handlers(bot)
        
        # Start the bot
        logger.info("Starting bot...", extra={
            'channel_id': config.discord.channel_id,
            'check_interval': config.discord.check_interval
        })
        
        bot.run(config.discord.token)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()