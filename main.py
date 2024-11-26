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
from embed_utils import create_status_embed, create_incident_embed

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

    async def update_status_message(self, channel: discord.TextChannel, current_state: dict):
        """Update or create status message and send notifications for changes."""
        status_embed = create_status_embed(current_state)
        
        # Check bot permissions in the channel
        bot_member = channel.guild.get_member(self.user.id)
        if not bot_member:
            logger.error(f"Could not find bot member in guild for channel {channel.name}")
            return
            
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
            else:
                new_message = await channel.send(embed=status_embed)
                await new_message.pin()
                self.status_message_id = new_message.id
                logger.info(f"Created status monitor message: {self.status_message_id}")

            # Send notification for significant changes
            if should_notify:
                notification_embed = status_embed.copy()
                notification_embed.title = "🔔 Status Change Alert"
                await channel.send(embed=notification_embed)
                logger.info("Sent status change notification")

            # Update last known status
            self.last_status = current_state
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

    async def handle_status_update(self, current_state: Optional[dict], updates: Optional[list]):
        """Handle status updates and send notifications."""
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

            # Clean up old pinned messages except the most recent status message
            try:
                pins = await channel.pins()
                for pin in pins:
                    if pin.id != self.status_message_id:
                        await pin.unpin()
            except Exception as e:
                logger.error(f"Error cleaning up pins: {str(e)}")

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
                
                if not current_state:
                    logger.error("Failed to fetch current state")
                    return
                    
                await self.handle_status_update(current_state, updates)
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