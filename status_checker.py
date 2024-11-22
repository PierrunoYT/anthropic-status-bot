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
                        
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    try:
                        status_data = {
                            'overall': self._parse_overall_status(soup),
                            'components': self._parse_components(soup),
                            'incidents': self._parse_incidents(soup),
                            'timestamp': datetime.utcnow().isoformat()
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

    def _parse_overall_status(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse overall system status."""
        selectors = self._selectors['overall']
        status_elem = soup.select_one(selectors['status'])
        description_elem = soup.select_one(selectors['description'])
        
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
        
        status_class = ' '.join(status_classes)
        return next((level for key, level in status_map.items() if key in status_class), 'operational')

    def _parse_components(self, soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
        """Parse component statuses."""
        selectors = self._selectors['component']
        components = {}
        timestamp = datetime.utcnow().isoformat()

        for element in soup.select(selectors['container']):
            name_elem = element.select_one(selectors['name'])
            status_elem = element.select_one(selectors['status'])
            
            if not name_elem or not status_elem:
                continue
                
            name = name_elem.text.strip()
            if name in self._components:
                components[name] = {
                    'status': status_elem.text.strip(),
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
        if not title_elem:
            return {
                'id': str(int(datetime.now().timestamp())),
                'name': 'Unknown Incident',
                'impact': 'none',
                'status': 'investigating',
                'updates': []
            }
            
        link_elem = title_elem.find('a')
        updates = self._parse_updates(soup, incident_elem)
        
        return {
            'id': link_elem['href'].split('/')[-1] if link_elem and link_elem.get('href') else str(int(datetime.now().timestamp())),
            'name': link_elem.text.strip() if link_elem else title_elem.text.strip(),
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

        if not incident_elem:
            return updates

        for update_elem in incident_elem.select(selectors['update']):
            if not update_elem:
                continue

            small_elem = update_elem.find('small')
            if not small_elem:
                continue

            strong_elem = update_elem.find('strong')
            message_elem = update_elem.select_one(selectors['message'])

            try:
                status = strong_elem.text.strip().lower() if strong_elem else 'investigating'
                message = message_elem.text.strip() if message_elem else ''
                timestamp = self._parse_timestamp(self._extract_date_info(soup, small_elem))
            except (AttributeError, ValueError) as e:
                logging.warning(f"Error parsing update element: {str(e)}")
                continue
            
            updates.append({
                'status': status,
                'message': message,
                'timestamp': timestamp
            })

        return updates

    def _extract_date_info(self, soup: BeautifulSoup, small_elem) -> str:
        """Extract date information from update element."""
        try:
            if not small_elem or not small_elem.text:
                return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")
                
            selectors = self._selectors['incident']['date']
            text_parts = small_elem.text.strip().split()
            
            if not text_parts:
                return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")
                
            month = text_parts[0]
            day = (small_elem.select_one(selectors['day']).text.strip() 
                  if small_elem.select_one(selectors['day']) else '')
            time = (small_elem.select_one(selectors['time']).text.strip() 
                   if small_elem.select_one(selectors['time']) else '')
            year = (small_elem.select_one(selectors['year']).text.strip() 
                   if small_elem.select_one(selectors['year']) else str(datetime.now().year))
            
            # Ensure we have all required parts
            if not all([month, day, year, time]):
                return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")
            
            return f"{month} {day}, {year} {time}"
            
        except Exception as e:
            logging.warning(f"Error extracting date info: {str(e)}")
            return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")

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

        try:
            # Check overall status
            if (previous.get('overall', {}).get('description') != 
                current.get('overall', {}).get('description')):
                updates.append({
                    'type': 'status_change',
                    'message': f"System status changed to: {current['overall']['description']}",
                    'timestamp': current.get('timestamp', datetime.utcnow().isoformat()),
                    'level': current['overall'].get('level', 'unknown')
                })

            # Check components
            current_components = current.get('components', {})
            previous_components = previous.get('components', {})
            
            for component, current_status in current_components.items():
                previous_status = previous_components.get(component)
                if not previous_status or previous_status.get('status') != current_status.get('status'):
                    updates.append({
                        'type': 'component_update',
                        'message': f"{component} status changed to: {current_status.get('status', 'unknown')}",
                        'timestamp': current_status.get('timestamp', datetime.utcnow().isoformat()),
                        'component': component
                    })

            # Check incidents
            current_incidents = current.get('incidents', [])
            previous_incidents = previous.get('incidents', [])
            
            if current_incidents:
                current_incident_ids = {i.get('id') for i in current_incidents if i.get('id')}
                previous_incident_ids = {i.get('id') for i in previous_incidents if i.get('id')}

                for incident in current_incidents:
                    incident_id = incident.get('id')
                    if not incident_id:
                        continue
                        
                    if incident_id not in previous_incident_ids:
                        updates.append({
                            'type': 'new_incident',
                            'message': (
                                f"New incident reported:\n{incident.get('name', 'Unknown')}\n"
                                f"Impact: {incident.get('impact', 'unknown')}\n"
                                f"Status: {incident.get('status', 'unknown')}"
                            ),
                            'timestamp': (incident.get('updates', [{}])[0].get('timestamp') 
                                        if incident.get('updates') 
                                        else current.get('timestamp', datetime.utcnow().isoformat())),
                            'incident': incident
                        })
                        continue

                    previous_incident = next(
                        (i for i in previous_incidents if i.get('id') == incident_id),
                        None
                    )
                    
                    if (previous_incident and 
                        (previous_incident.get('status') != incident.get('status') or 
                         len(previous_incident.get('updates', [])) != len(incident.get('updates', [])))):
                        updates.append({
                            'type': 'incident_update',
                            'message': (
                                f"Incident \"{incident.get('name', 'Unknown')}\" "
                                f"status updated to: {incident.get('status', 'unknown')}"
                            ),
                            'timestamp': (incident.get('updates', [{}])[0].get('timestamp')
                                        if incident.get('updates')
                                        else current.get('timestamp', datetime.utcnow().isoformat())),
                            'incident': incident
                        })
        except Exception as e:
            logging.error(f"Error comparing states: {str(e)}")
            
        return updates