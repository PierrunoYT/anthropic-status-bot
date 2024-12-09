from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class StatusParser:
    def __init__(self):
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

    def parse_status_page(self, html: str) -> Dict[str, Any]:
        """Parse status page HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        return {
            'overall': self._parse_overall_status(soup),
            'components': self._parse_components(soup),
            'incidents': self._parse_incidents(soup),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _parse_overall_status(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse overall system status."""
        selectors = self._selectors['overall']
        status_elem = soup.select_one(selectors['status'])
        description_elem = soup.select_one(selectors['description'])
        
        # Check component statuses to determine overall status
        components = self._parse_components(soup)
        has_degraded = any(comp.get('status', '').lower() == 'degraded performance' 
                          for comp in components.values())
        has_outage = any(comp.get('status', '').lower() == 'outage' 
                        for comp in components.values())
        
        if has_outage:
            status = 'System Outage'
            level = 'outage'
        elif has_degraded:
            status = 'Degraded Performance'
            level = 'degraded'
        else:
            status = description_elem.text.strip() if description_elem else 'All Systems Operational'
            level = self._determine_status_level(status_elem.get('class', []) if status_elem else [])
            
        return {
            'description': status,
            'level': level
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
                incidents.append(self._parse_incident_element(incident_elem))

        return incidents

    def _parse_incident_element(self, incident_elem) -> Dict[str, Any]:
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
        updates = self._parse_updates(incident_elem)
        
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

    def _parse_updates(self, incident_elem) -> List[Dict[str, Any]]:
        """Parse incident updates."""
        selectors = self._selectors['incident']
        updates = []

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
                timestamp = self._parse_timestamp(self._extract_date_info(small_elem))
            except (AttributeError, ValueError) as e:
                logging.warning(f"Error parsing update element: {str(e)}")
                continue
            
            updates.append({
                'status': status,
                'message': message,
                'timestamp': timestamp
            })

        return updates

    def _extract_date_info(self, small_elem) -> str:
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
            
            if not all([month, day, year, time]):
                return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")
            
            return f"{month} {day}, {year} {time}"
            
        except Exception as e:
            logging.warning(f"Error extracting date info: {str(e)}")
            return datetime.utcnow().strftime("%B %d, %Y %I:%M %p")

    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse timestamp string to ISO format in UTC."""
        try:
            formats = [
                "%B %d, %Y %I:%M %p",
                "%b %d, %Y %H:%M",
            ]
            
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                raise ValueError(f"Could not parse timestamp with any known format: {timestamp_str}")
                
            utc_dt = dt + timedelta(hours=8)
            return utc_dt.isoformat() + "Z"
        except Exception as e:
            logger.warning(f"Error parsing timestamp '{timestamp_str}': {str(e)}")
            return datetime.utcnow().isoformat() + "Z"
