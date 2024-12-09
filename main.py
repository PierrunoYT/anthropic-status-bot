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
from embed_utils import create_status_embed

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
        intents.guild_messages = True
        
        # Set up required permissions
        permissions = discord.Permissions(
            view_channel=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            read_message_history=True,
            manage_channels=True
        )

        # Files to store persistent data
        self.message_id_file = "status_message_id.txt"
        self.last_status_file = "last_status.txt"
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.status_checker = StatusChecker()
        self.status_message_id: Optional[int] = None
        self.last_status: Optional[dict] = None
        self.scheduler = AsyncIOScheduler()
        self.required_permissions = [
            'view_channel',
            'send_messages',
            'manage_messages',
            'embed_links',
            'read_message_history'
        ]
        
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

    def _load_message_id(self) -> Optional[int]:
        """Load message ID from file."""
        try:
            with open(self.message_id_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return None

    def _save_last_status(self, status: dict):
        """Save last status to file."""
        try:
            import json
            with open(self.last_status_file, 'w') as f:
                json.dump(status, f)
        except Exception as e:
            logger.error(f"Error saving last status: {str(e)}")

    def _load_last_status(self) -> Optional[dict]:
        """Load last status from file."""
        try:
            import json
            with open(self.last_status_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            return None

    def _save_message_id(self, message_id: int):
        """Save message ID to file."""
        try:
            with open(self.message_id_file, 'w') as f:
                f.write(str(message_id))
        except Exception as e:
            logger.error(f"Error saving message ID: {str(e)}")

    async def update_status_message(self, channel: discord.TextChannel, current_state: dict):
        """Update or create status message and send notifications for changes."""
        status_embed = create_status_embed(current_state)
        
        # Check bot permissions in the channel
        bot_member = channel.guild.get_member(self.user.id)
        if not bot_member:
            logger.error(f"Could not find bot member in guild for channel {channel.name}")
            return

        # Load message ID and last status from file if not in memory
        if not self.status_message_id:
            self.status_message_id = self._load_message_id()
        if not self.last_status:
            self.last_status = self._load_last_status()
            
        channel_permissions = channel.permissions_for(bot_member)
        missing_permissions = []
        
        for perm in self.required_permissions:
            if not getattr(channel_permissions, perm, False):
                missing_permissions.append(perm)
        
        if missing_permissions:
            logger.error(f"Missing required permissions in channel {channel.name}: {', '.join(missing_permissions)}")
            return

        # Check for significant status changes
        should_notify = False
        if self.last_status is not None:
            # Check if overall status changed
            if current_state['overall']['level'] != self.last_status['overall']['level']:
                should_notify = True
            
            # Check if any component status changed
            for name, data in current_state['components'].items():
                if (name not in self.last_status['components'] or 
                    data['status'] != self.last_status['components'][name]['status']):
                    should_notify = True
                    break

        # Update the pinned status message
        try:
            if self.status_message_id:
                try:
                    status_message = await channel.fetch_message(self.status_message_id)
                    await status_message.edit(embed=status_embed)
                    if not status_message.pinned:
                        await status_message.pin()
                    logger.info("Status monitor message updated")
                except discord.NotFound:
                    logger.warning("Could not find status message, creating new one")
                    new_message = await channel.send(embed=status_embed)
                    await new_message.pin()
                    self.status_message_id = new_message.id
                    self._save_message_id(new_message.id)
            else:
                new_message = await channel.send(embed=status_embed)
                await new_message.pin()
                self.status_message_id = new_message.id
                self._save_message_id(new_message.id)
                logger.info(f"Created status monitor message: {self.status_message_id}")

            # Send notification only for status changes
            if should_notify:
                notification_embed = create_status_embed(current_state, is_alert=True)
                await channel.send(embed=notification_embed)
                logger.info("Sent status change notification")

            # Update last known status
            self.last_status = current_state
            self._save_last_status(current_state)
        except Exception as e:
            logger.error(f"Error updating status message: {str(e)}")
            new_message = await channel.send(embed=status_embed)
            self.status_message_id = new_message.id
            self._save_message_id(new_message.id)

    async def handle_status_update(self, current_state: Optional[dict], updates: Optional[list]):
        """Handle status updates."""
        try:
            logger.info("Handling status update")
            
            if not current_state:
                logger.error("Cannot handle status update: current_state is None")
                return
                
            try:
                channel = await self.fetch_channel(int(config.discord.channel_id))
            except discord.Forbidden:
                logger.error("Bot does not have permission to access the channel")
                return
            except discord.NotFound:
                logger.error(f"Could not find channel: {config.discord.channel_id}")
                return
            
            if not channel:
                logger.error(f"Could not find channel: {config.discord.channel_id}")
                return
                
            # Verify channel type
            if not isinstance(channel, discord.TextChannel):
                logger.error(f"Channel {config.discord.channel_id} is not a text channel")
                return

            # Update the status message without cleaning up other pins
            await self.update_status_message(channel, current_state)
            
        except Exception as e:
            logger.error(f"Error handling status update: {str(e)}")

    def setup_status_checking(self):
        """Setup periodic status checking."""
        async def check_status():
            try:
                # Get the async generator from check_for_updates
                updates_generator = self.status_checker.check_for_updates()
                current_state = self.status_checker.get_current_state()
                
                if not current_state:
                    logger.error("Failed to fetch current state")
                    return
                    
                # Pass the collected updates to handle_status_update
                await self.handle_status_update(current_state, updates_generator)
            except Exception as e:
                logger.error(f"Error checking status: {str(e)}", exc_info=True)

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
        if self.status_message_id:
            self._save_message_id(self.status_message_id)
        if self.last_status:
            self._save_last_status(self.last_status)
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