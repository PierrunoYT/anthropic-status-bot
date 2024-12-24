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
            'incident_messages': {},
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
                    return message_id
                except (discord.NotFound, discord.Forbidden) as error:
                    # If message not found or can't be edited, create new one
                    logger.warn(f"Failed to edit message: {error}")
                    message = await channel.send(embed=embed)
                    try:
                        await message.pin(reason="Status message pinned for visibility")
                    except discord.Forbidden:
                        logger.warn("Failed to pin message: Missing permissions")
                    return message.id
            
            # Send new message and pin it
            message = await channel.send(embed=embed)
            try:
                await message.pin(reason="Status message pinned for visibility")
            except discord.Forbidden:
                logger.warn("Failed to pin message: Missing permissions")
            return message.id
        except Exception as error:
            logger.log_error(error, {'operation': 'update_message'})
            # Last resort: try to send a new message
            try:
                message = await channel.send(embed=embed)
                try:
                    await message.pin(reason="Status message pinned for visibility")
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
            self.state['status_message_id'] = await self.update_message(
                channel,
                self.state['status_message_id'],
                create_status_embed(current_state)
            )

            # Handle incident updates
            if updates and updates.get('type') != 'initial' and isinstance(updates, list):
                for update in updates:
                    if update['type'] in ['new_incident', 'incident_update']:
                        message_id = await self.update_message(
                            channel,
                            self.state['incident_messages'].get(update['incident']['id']),
                            create_incident_embed(update['incident'])
                        )
                        if message_id:
                            self.state['incident_messages'][update['incident']['id']] = message_id

        except Exception as error:
            logger.log_error(error, {'operation': 'handle_status_update'})

    @tasks.loop(minutes=config.discord.check_interval)
    async def check_status(self):
        """Periodic status check task."""
        try:
            updates = await self.status_checker.check_for_updates()
            await self.handle_status_update(
                self.status_checker.get_current_state(),
                updates
            )
        except Exception as error:
            logger.log_error(error, {'operation': 'check_status'})

    async def close(self) -> None:
        """Clean up resources on shutdown."""
        self.check_status.cancel()
        await super().close()

    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"Bot ready as {self.user}")
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