import asyncio
from typing import Optional, Dict, Any
import discord
from discord.ext import tasks
from datetime import datetime, timedelta
import logger
from config import config
from status_checker import StatusChecker
from utils.embed_utils import create_status_embed, create_incident_embed

class AnthropicStatusBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.status_checker = StatusChecker()
        self.state = {
            'status_message_id': None,
            'last_message_time': 0
        }
        self.RATE_LIMIT_DELAY = 1.0  # 1 second between messages

    async def setup_hook(self) -> None:
        """Set up the bot and start the status check loop."""
        self.check_status.start()

    async def update_message(self, channel: discord.TextChannel, 
                           message_id: Optional[int], embed: discord.Embed) -> Optional[int]:
        """Update or send a message with rate limiting."""
        # Rate limiting
        now = datetime.now().timestamp()
        time_since_last = now - self.state['last_message_time']
        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.state['last_message_time'] = datetime.now().timestamp()

        try:
            if message_id:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed)
                    logger.info(f"Successfully edited message {message_id}")
                    return message_id
                except (discord.NotFound, discord.Forbidden) as error:
                    # If message not found or can't be edited, create new one
                    logger.warn(f"Failed to edit message: {error}")
                    message = await channel.send(embed=embed)
                    try:
                        await message.pin(reason="Status message pinned for visibility")
                        logger.info(f"Successfully pinned new message {message.id} (after failed edit)")
                    except discord.Forbidden:
                        logger.warn("Failed to pin message: Missing permissions")
                    return message.id
            
            # Send new message and pin it
            logger.info("Creating new status message...")
            message = await channel.send(embed=embed)
            try:
                # Unpin old status messages from the bot
                pins = await channel.pins()
                for pin in pins:
                    if pin.author == self.user and pin.embeds:
                        await pin.unpin()
                        logger.info(f"Unpinned old status message: {pin.id}")
                
                # Pin the new message
                await message.pin(reason="Status message pinned for visibility")
                logger.info(f"Successfully pinned new status message {message.id}")
            except discord.Forbidden:
                logger.warn("Failed to pin message: Missing permissions")
            return message.id
        except Exception as error:
            logger.log_error(error, {'operation': 'update_message'})
            # Last resort: try to send a new message
            try:
                message = await channel.send(embed=embed)
                try:
                    # Unpin old status messages from the bot (fallback case)
                    pins = await channel.pins()
                    for pin in pins:
                        if pin.author == self.user and pin.embeds:
                            await pin.unpin()
                            logger.info(f"Unpinned old status message in fallback: {pin.id}")
                    
                    # Pin the new message
                    await message.pin(reason="Status message pinned for visibility")
                    logger.info(f"Successfully pinned new message in fallback: {message.id}")
                except discord.Forbidden:
                    logger.warn("Failed to pin message: Missing permissions")
                return message.id
            except Exception as final_error:
                logger.log_error(final_error, {'operation': 'update_message_fallback'})
                return None

    async def handle_status_update(self, current_state: Dict[str, Any], 
                                 updates: Optional[Dict[str, Any]]) -> None:
        """Handle status updates and send/update Discord messages."""
        try:
            channel = await self.fetch_channel(int(config.discord.channel_id))
            if not channel:
                return

            # Update status message
            logger.info(f"Updating status message (current ID: {self.state['status_message_id']})")
            new_message_id = await self.update_message(
                channel,
                self.state['status_message_id'],
                create_status_embed(current_state)
            )
            if new_message_id != self.state['status_message_id']:
                logger.info(f"Status message ID changed: {self.state['status_message_id']} -> {new_message_id}")
            self.state['status_message_id'] = new_message_id

        except Exception as error:
            logger.log_error(error, {'operation': 'handle_status_update'})

    @tasks.loop(minutes=config.discord.check_interval)
    async def check_status(self):
        """Periodic status check task."""
        try:
            logger.info("Starting status check cycle...")
            updates = await self.status_checker.check_for_updates()
            
            if updates:
                logger.info(f"Received {len(updates)} updates")
                for update in updates:
                    logger.info(f"Processing update type: {update.get('type', 'unknown')}")
            
            await self.handle_status_update(
                self.status_checker.get_current_state(),
                updates
            )
            logger.info("Status check cycle completed")
        except Exception as error:
            logger.log_error(error, {'operation': 'check_status'})

    async def close(self) -> None:
        """Clean up resources on shutdown."""
        self.check_status.cancel()
        await super().close()

    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"Bot ready as {self.user}")
        
        # Find existing pinned status message
        try:
            channel = await self.fetch_channel(int(config.discord.channel_id))
            if channel:
                pins = await channel.pins()
                # Look for the most recent pinned message from the bot
                for pin in pins:
                    if pin.author == self.user and pin.embeds:
                        self.state['status_message_id'] = pin.id
                        logger.info(f"Found existing pinned status message: {pin.id}")
                        break
        except Exception as error:
            logger.log_error(error, {'operation': 'find_pinned_message'})
        
        await self.check_status()

    async def on_error(self, event: str, *args, **kwargs):
        """Handle Discord events errors."""
        logger.log_error(
            args[0] if args else Exception("Unknown error"),
            {'operation': f'discord_{event}'}
        )

def main():
    """Main entry point."""
    bot = AnthropicStatusBot()
    
    async def start():
        try:
            await bot.start(config.discord.token)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Starting graceful shutdown...")
        except Exception as error:
            logger.log_error(error, {'operation': 'startup'})
        finally:
            await bot.close()

    # Run the bot
    asyncio.run(start())