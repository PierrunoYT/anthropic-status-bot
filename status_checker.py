import aiohttp
import asyncio
from typing import Dict, Any, Optional, Set, AsyncGenerator
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from config import config
from html_parser import HtmlParser
from state_manager import StateManager
from state_comparator import StateComparator
from date_utils import get_current_timestamp

logger = logging.getLogger(__name__)

class StatusChecker:
    def __init__(self):
        self._components: Set[str] = set(config.status.components)
        self._state_file = "checker_state.txt"
        self._parser = HtmlParser()
        self._state_manager = StateManager(self._state_file)
        self._state_comparator = StateComparator()

    async def fetch_status(self) -> Optional[Dict[str, Any]]:
        """Fetch and parse status page."""
        async with aiohttp.ClientSession() as session:
            try:
                start_time = datetime.now()
                headers = {
                    'Accept': 'text/html',
                    'User-Agent': config.status.user_agent
                }

                async with session.get(
                    config.status.url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=config.status.timeout)
                ) as response:
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    logging.info(f"GET {config.status.url} - {response.status} - {duration:.0f}ms")

                    if response.status != 200:
                        logging.error(f"Failed to fetch status page. Status code: {response.status}")
                        return None

                    html = await response.text()

                    if not html.strip():
                        logging.error("Received empty response from status page")
                        return None

                    try:
                        soup = BeautifulSoup(html, 'html.parser')
                        components = self._parser.parse_components(soup, list(self._components))
                        overall = self._parser.parse_overall_status(soup, components)
                        incidents = self._parser.parse_incidents(soup)

                        status_data = {
                            'overall': overall,
                            'components': components,
                            'incidents': incidents,
                            'timestamp': get_current_timestamp()
                        }

                        # Validate parsed data
                        if not status_data['overall'] or not status_data['components']:
                            logging.error("Failed to parse critical status information")
                            return None

                        return status_data

                    except Exception as parse_error:
                        logging.error(f"Error parsing status page: {str(parse_error)}")
                        return None

            except asyncio.TimeoutError:
                logging.error(f"Timeout while fetching status page (timeout: {config.status.timeout}s)")
                return None
            except aiohttp.ClientError as e:
                logging.error(f"Network error while fetching status page: {str(e)}")
                return None
            except Exception as e:
                logging.error(f"Unexpected error fetching status: {str(e)}", exc_info=True)
                return None

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current state."""
        return self._state_manager.get_current_state()

    async def check_for_updates(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Check for status updates."""
        current_state = await self.fetch_status()
        
        if not current_state:
            logging.warning("Failed to fetch status update")
            return

        current, previous = self._state_manager.get_states()

        if not previous:
            self._state_manager.save_state(current_state)
            logging.info(
                "Status monitoring initialized",
                extra={
                    'status': current_state['overall']['description'],
                    'components': self._state_comparator.format_component_statuses(current_state['components'])
                }
            )
            yield {
                'type': 'initial',
                'message': (
                    f"Status monitoring initialized.\n"
                    f"Current Status: {current_state['overall']['description']}\n"
                    f"{self._state_comparator.format_component_statuses(current_state['components'])}"
                ),
                'timestamp': current_state['timestamp']
            }
            return

        # Compare states and yield updates
        updates = self._state_comparator.compare_states(previous, current_state)
        for update in updates:
            yield update

        self._state_manager.save_state(current_state)