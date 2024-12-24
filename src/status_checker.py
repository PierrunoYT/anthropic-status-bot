from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from config import config
import logging

logger = logging.getLogger(__name__)

class StatusChecker:
    def __init__(self):
        self._previous_state: Optional[Dict[str, Any]] = None
        self._current_state: Optional[Dict[str, Any]] = None
        self._components: Set[str] = set(config.status.components)
        self._recent_messages: Dict[str, float] = {}
        self._MESSAGE_EXPIRY = 60000  # 1 minute in milliseconds

        # HTML selectors for parsing
        self._selectors = {
            'overall': {
                'description': '.overall-status__description',
                'status': '.overall-status'
            },
            'component': {
                'container': '.component-container',
                'name': '.name',
                'status': '.component-status'
            },
            'incident': {
                'container': '.incident-container',
                'title': '.incident-title',
                'update': '.update',
                'message': '.whitespace-pre-wrap',
                'date': {
                    'day': 'var[data-var="date"]',
                    'time': 'var[data-var="time"]',
                    'year': 'var[data-var="year"]'
                }
            }
        }

        # Configure requests session
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'text/html',
            'User-Agent': config.status.user_agent,
            'Cache-Control': 'max-age=60'
        })

    @retry(
        stop=stop_after_attempt(config.status.retries),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None
    )
    def fetch_status(self) -> Optional[Dict[str, Any]]:
        """Fetch and parse the status page."""
        try:
            start_time = datetime.now()
            response = self._session.get(
                config.status.url,
                timeout=config.status.timeout / 1000  # Convert to seconds
            )
            duration = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"GET {config.status.url} - {response.status_code} - {duration}ms")
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            return {
                'overall': self._parse_overall_status(soup),
                'components': self._parse_components(soup),
                'incidents': self._parse_incidents(soup),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as error:
            logger.error(f"Error fetching status: {str(error)}", exc_info=True)
            return None

    def _parse_overall_status(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse overall system status."""
        status_elem = soup.select_one(self._selectors['overall']['status'])
        description_elem = soup.select_one(self._selectors['overall']['description'])
        
        return {
            'description': description_elem.text.strip() if description_elem else 'All Systems Operational',
            'level': self._determine_status_level(status_elem.get('class', []) if status_elem else [])
        }

    def _determine_status_level(self, status_classes: List[str]) -> str:
        """Determine status level from CSS classes."""
        status_map = {
            'degraded': 'degraded',
            'outage': 'outage',
            'maintenance': 'maintenance'
        }
        
        status_class = ' '.join(status_classes).lower()
        return next((level for key, level in status_map.items() 
                    if key in status_class), 'operational')

    def _parse_components(self, soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
        """Parse component statuses."""
        components = {}
        timestamp = datetime.utcnow().isoformat()
        
        for elem in soup.select(self._selectors['component']['container']):
            name = elem.select_one(self._selectors['component']['name'])
            if name:
                name_text = name.text.strip()
                if name_text in self._components:
                    status = elem.select_one(self._selectors['component']['status'])
                    components[name_text] = {
                        'status': status.text.strip() if status else 'unknown',
                        'timestamp': timestamp
                    }
        
        return components

    def _parse_incidents(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse incident information."""
        incidents = []
        
        for day_elem in soup.select('.status-day'):
            for incident_elem in day_elem.select(self._selectors['incident']['container']):
                incidents.append(self._parse_incident_element(incident_elem))
        
        return incidents

    def _parse_incident_element(self, incident_elem: BeautifulSoup) -> Dict[str, Any]:
        """Parse a single incident element."""
        title_elem = incident_elem.select_one(self._selectors['incident']['title'])
        link = title_elem.find('a') if title_elem else None
        
        return {
            'id': link['href'].split('/')[-1] if link and 'href' in link.attrs 
                 else str(int(datetime.now().timestamp() * 1000)),
            'name': link.text.strip() if link else 'Unknown Incident',
            'impact': self._determine_impact_level(title_elem.get('class', []) if title_elem else []),
            'status': self._parse_updates(incident_elem)[0]['status'] if self._parse_updates(incident_elem) else 'investigating',
            'updates': self._parse_updates(incident_elem)
        }

    def _determine_impact_level(self, title_classes: List[str]) -> str:
        """Determine incident impact level from CSS classes."""
        impact_map = {
            'impact-minor': 'minor',
            'impact-major': 'major',
            'impact-critical': 'critical'
        }
        
        title_class = ' '.join(title_classes).lower()
        return next((level for key, level in impact_map.items() 
                    if key in title_class), 'none')

    def _parse_updates(self, incident_elem: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse incident updates."""
        updates = []
        
        for update_elem in incident_elem.select(self._selectors['incident']['update']):
            strong = update_elem.find('strong')
            message = update_elem.select_one(self._selectors['incident']['message'])
            small = update_elem.find('small')
            
            if strong and message and small:
                updates.append({
                    'status': strong.text.strip().lower(),
                    'message': message.text.strip(),
                    'timestamp': self._parse_timestamp(self._extract_date_info(small))
                })
        
        return updates

    def _extract_date_info(self, small_elem: BeautifulSoup) -> str:
        """Extract and format date information."""
        date_selectors = self._selectors['incident']['date']
        month = small_elem.text.strip().split()[0]
        day = small_elem.select_one(date_selectors['day'])
        time = small_elem.select_one(date_selectors['time'])
        year = small_elem.select_one(date_selectors['year'])
        
        return (f"{month} {day.text.strip() if day else ''}, "
                f"{year.text.strip() if year else datetime.now().year} "
                f"{time.text.strip() if time else ''}")

    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse timestamp string to ISO format."""
        try:
            # Assuming PST timezone for consistency with original
            dt = datetime.strptime(f"{timestamp_str} PST", "%B %d, %Y %I:%M %p %Z")
            return dt.isoformat()
        except Exception:
            return datetime.utcnow().isoformat()

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the current state."""
        return self._current_state

    def _is_duplicate(self, message: str, timestamp: str) -> bool:
        """Check if a message is a duplicate within the expiry window."""
        key = f"{message}-{timestamp}"
        now = datetime.now().timestamp() * 1000
        
        # Clean up old messages
        if len(self._recent_messages) > 0 and len(self._recent_messages) % 100 == 0:
            expired_time = now - self._MESSAGE_EXPIRY
            self._recent_messages = {
                k: v for k, v in self._recent_messages.items()
                if v >= expired_time
            }
        
        # Limit dictionary size
        if len(self._recent_messages) > 1000:
            oldest_key = min(self._recent_messages, key=self._recent_messages.get)
            del self._recent_messages[oldest_key]
        
        if key in self._recent_messages:
            return True
        
        self._recent_messages[key] = now
        return False

    async def check_for_updates(self) -> Optional[List[Dict[str, Any]]]:
        """Check for status updates and return changes."""
        current_state = self.fetch_status()
        
        if not current_state:
            logger.warning("Failed to fetch status update")
            return None

        self._current_state = current_state

        if not self._previous_state:
            self._previous_state = current_state
            status_msg = (
                f"Status monitoring initialized.\n"
                f"Current Status: {current_state['overall']['description']}\n"
                f"{self._format_component_statuses(current_state['components'])}"
            )
            logger.info(status_msg)
            return [{
                'type': 'initial',
                'message': status_msg,
                'timestamp': current_state['timestamp']
            }]

        updates = self._compare_states(self._previous_state, current_state)
        self._previous_state = current_state

        return updates if updates else None

    def _format_component_statuses(self, components: Dict[str, Dict[str, str]]) -> str:
        """Format component statuses for display."""
        return '\n'.join(f"{name}: {data['status']}" 
                        for name, data in components.items())

    def _compare_states(self, previous: Dict[str, Any], 
                       current: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare previous and current states to detect changes."""
        updates = []

        # Check overall status changes
        if previous['overall']['description'] != current['overall']['description']:
            message = f"System status changed to: {current['overall']['description']}"
            if not self._is_duplicate(message, current['timestamp']):
                updates.append({
                    'type': 'status_change',
                    'message': message,
                    'timestamp': current['timestamp'],
                    'level': current['overall']['level']
                })

        # Check component changes
        for component, current_status in current['components'].items():
            prev_status = previous['components'].get(component)
            if not prev_status or prev_status['status'] != current_status['status']:
                message = f"{component} status changed to: {current_status['status']}"
                if not self._is_duplicate(message, current_status['timestamp']):
                    updates.append({
                        'type': 'component_update',
                        'message': message,
                        'timestamp': current_status['timestamp'],
                        'component': component
                    })

        # Check incident changes
        if current['incidents']:
            current_ids = {i['id'] for i in current['incidents']}
            previous_ids = {i['id'] for i in previous['incidents']}

            # New and updated incidents
            for incident in current['incidents']:
                prev_incident = next((i for i in previous['incidents'] 
                                    if i['id'] == incident['id']), None)
                
                if incident['id'] not in previous_ids:
                    updates.append({'type': 'new_incident', 'incident': incident})
                elif prev_incident and (
                    prev_incident['status'] != incident['status'] or
                    len(prev_incident['updates']) != len(incident['updates'])
                ):
                    updates.append({'type': 'incident_update', 'incident': incident})

            # Resolved incidents
            for prev_id in previous_ids - current_ids:
                resolved_incident = next(i for i in previous['incidents'] 
                                      if i['id'] == prev_id)
                if resolved_incident:
                    updates.append({
                        'type': 'incident_resolved',
                        'incident': {
                            **resolved_incident,
                            'status': 'resolved',
                            'updates': [
                                {
                                    'status': 'resolved',
                                    'message': 'Incident resolved',
                                    'timestamp': datetime.utcnow().isoformat()
                                },
                                *resolved_incident['updates']
                            ]
                        }
                    })

        return updates