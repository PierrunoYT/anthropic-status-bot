import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import logging
from config import config

class StatusChecker:
    def __init__(self):
        self._previous_state = None
        self._current_state = None
        self._components: Set[str] = set(config.status.components)
        
        # Cache selectors
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
                    timeout=aiohttp.ClientTimeout(total=config.status.timeout / 1000)
                ) as response:
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    logging.info(f"GET {config.status.url} - {response.status} - {duration:.0f}ms")
                    
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    return {
                        'overall': self._parse_overall_status(soup),
                        'components': self._parse_components(soup),
                        'incidents': self._parse_incidents(soup),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                logging.error(f"Error fetching status: {str(e)}")
                return None

    def _parse_overall_status(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse overall system status."""
        selectors = self._selectors['overall']
        status_elem = soup.select_one(selectors['status'])
        
        return {
            'description': soup.select_one(selectors['description']).text.strip() or 'All Systems Operational',
            'level': self._determine_status_level(status_elem.get('class', []) if status_elem else [])
        }

    def _determine_status_level(self, status_classes: List[str]) -> str:
        """Determine status level from CSS classes."""
        status_map = {
            'degraded': 'degraded',
            'outage': 'outage',
            'maintenance': 'maintenance'
        }
        
        status_class = ' '.join(status_classes)
        return next((level for key, level in status_map.items() if key in status_class), 'operational')

    def _parse_components(self, soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
        """Parse component statuses."""
        selectors = self._selectors['component']
        components = {}
        timestamp = datetime.utcnow().isoformat()

        for element in soup.select(selectors['container']):
            name = element.select_one(selectors['name']).text.strip()
            if name in self._components:
                components[name] = {
                    'status': element.select_one(selectors['status']).text.strip(),
                    'timestamp': timestamp
                }

        return components

    def _parse_incidents(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse incidents."""
        incidents = []
        selectors = self._selectors['incident']

        for day_elem in soup.select('.status-day'):
            for incident_elem in day_elem.select(selectors['container']):
                incidents.append(self._parse_incident_element(soup, incident_elem))

        return incidents

    def _parse_incident_element(self, soup: BeautifulSoup, incident_elem) -> Dict[str, Any]:
        """Parse single incident element."""
        selectors = self._selectors['incident']
        title_elem = incident_elem.select_one(selectors['title'])
        link_elem = title_elem.find('a')
        
        updates = self._parse_updates(soup, incident_elem)
        
        return {
            'id': link_elem['href'].split('/')[-1] if link_elem else str(int(datetime.now().timestamp())),
            'name': link_elem.text.strip() if link_elem else '',
            'impact': self._determine_impact_level(title_elem.get('class', [])),
            'status': updates[0]['status'] if updates else 'investigating',
            'updates': updates
        }

    def _determine_impact_level(self, title_classes: List[str]) -> str:
        """Determine impact level from CSS classes."""
        impact_map = {
            'impact-minor': 'minor',
            'impact-major': 'major',
            'impact-critical': 'critical'
        }
        
        title_class = ' '.join(title_classes)
        return next((level for key, level in impact_map.items() if key in title_class), 'none')

    def _parse_updates(self, soup: BeautifulSoup, incident_elem) -> List[Dict[str, Any]]:
        """Parse incident updates."""
        selectors = self._selectors['incident']
        updates = []

        for update_elem in incident_elem.select(selectors['update']):
            small_elem = update_elem.find('small')
            if not small_elem:
                continue

            status = update_elem.find('strong').text.strip().lower() if update_elem.find('strong') else 'investigating'
            message = update_elem.select_one(selectors['message']).text.strip() if update_elem.select_one(selectors['message']) else ''
            
            timestamp = self._parse_timestamp(self._extract_date_info(soup, small_elem))
            
            updates.append({
                'status': status,
                'message': message,
                'timestamp': timestamp
            })

        return updates

    def _extract_date_info(self, soup: BeautifulSoup, small_elem) -> str:
        """Extract date information from update element."""
        selectors = self._selectors['incident']['date']
        month = small_elem.text.strip().split()[0]
        day = small_elem.select_one(selectors['day']).text.strip() if small_elem.select_one(selectors['day']) else ''
        time = small_elem.select_one(selectors['time']).text.strip() if small_elem.select_one(selectors['time']) else ''
        year = small_elem.select_one(selectors['year']).text.strip() if small_elem.select_one(selectors['year']) else str(datetime.now().year)
        
        return f"{month} {day}, {year} {time}"

    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse timestamp string to ISO format."""
        try:
            # Attempt to parse the timestamp with PST timezone
            dt = datetime.strptime(f"{timestamp_str} PST", "%B %d, %Y %I:%M %p %Z")
            return dt.isoformat()
        except:
            return datetime.utcnow().isoformat()

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current state."""
        return self._current_state

    async def check_for_updates(self) -> Optional[List[Dict[str, Any]]]:
        """Check for status updates."""
        current_state = await self.fetch_status()
        
        if not current_state:
            logging.warning("Failed to fetch status update")
            return None

        self._current_state = current_state

        if not self._previous_state:
            self._previous_state = current_state
            logging.info(
                "Status monitoring initialized",
                extra={
                    'status': current_state['overall']['description'],
                    'components': self._format_component_statuses(current_state['components'])
                }
            )
            return [{
                'type': 'initial',
                'message': (
                    f"Status monitoring initialized.\n"
                    f"Current Status: {current_state['overall']['description']}\n"
                    f"{self._format_component_statuses(current_state['components'])}"
                ),
                'timestamp': current_state['timestamp']
            }]

        updates = self._compare_states(self._previous_state, current_state)
        self._previous_state = current_state

        return updates if updates else None

    def _format_component_statuses(self, components: Dict[str, Dict[str, str]]) -> str:
        """Format component statuses for display."""
        return '\n'.join(f"{name}: {data['status']}" for name, data in components.items())

    def _compare_states(self, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare previous and current states for changes."""
        updates = []

        # Check overall status
        if previous['overall']['description'] != current['overall']['description']:
            updates.append({
                'type': 'status_change',
                'message': f"System status changed to: {current['overall']['description']}",
                'timestamp': current['timestamp'],
                'level': current['overall']['level']
            })

        # Check components
        for component, current_status in current['components'].items():
            previous_status = previous['components'].get(component)
            if not previous_status or previous_status['status'] != current_status['status']:
                updates.append({
                    'type': 'component_update',
                    'message': f"{component} status changed to: {current_status['status']}",
                    'timestamp': current_status['timestamp'],
                    'component': component
                })

        # Check incidents
        if current['incidents']:
            current_incident_ids = {i['id'] for i in current['incidents']}
            previous_incident_ids = {i['id'] for i in previous['incidents']}

            for incident in current['incidents']:
                if incident['id'] not in previous_incident_ids:
                    updates.append({
                        'type': 'new_incident',
                        'message': (
                            f"New incident reported:\n{incident['name']}\n"
                            f"Impact: {incident['impact']}\nStatus: {incident['status']}"
                        ),
                        'timestamp': incident['updates'][0]['timestamp'] if incident['updates'] else current['timestamp'],
                        'incident': incident
                    })
                    continue

                previous_incident = next(
                    (i for i in previous['incidents'] if i['id'] == incident['id']),
                    None
                )
                
                if (previous_incident and 
                    (previous_incident['status'] != incident['status'] or 
                     len(previous_incident['updates']) != len(incident['updates']))):
                    updates.append({
                        'type': 'incident_update',
                        'message': f"Incident \"{incident['name']}\" status updated to: {incident['status']}",
                        'timestamp': incident['updates'][0]['timestamp'] if incident['updates'] else current['timestamp'],
                        'incident': incident
                    })

        return updates