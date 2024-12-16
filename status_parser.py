from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class StatusParser:
    def __init__(self):
        # Cache selectors and status mappings
        self._selectors = {
            'overall': {
                'banner': '[role="alert"]',
                'status': '[role="alert"] span'
            },
            'component': {
                'container': '[role="listitem"]',
                'name': 'h3',
                'status': '[role="status"]',
                'uptime': '[title*="%"]'
            },
            'uptime': {
                'period': 'time',
                'graph': '[role="list"]',
                'bars': '[role="presentation"]',
                'link': 'a[href*="uptime"]'
            }
        }

        # Map status colors to states
        self._status_colors = {
            '#22C55E': 'operational',
            '#EAB308': 'degraded',
            '#EF4444': 'outage'
        }

    def _clean_component_name(self, name: str) -> str:
        """Remove emoji and extra whitespace from component name."""
        cleaned = re.sub(r'[^\w\s\.-]', '', name).strip()
        return cleaned

    def parse_status_page(self, content: str, is_html: bool = True) -> Dict[str, Any]:
        """Parse status page content (HTML or text)."""
        if is_html:
            return self._parse_html_content(content)
        else:
            return self._parse_text_content(content)

    def _parse_html_content(self, html: str) -> Dict[str, Any]:
        """Parse status page HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        timestamp = datetime.utcnow().isoformat()
        
        return {
            'overall': self._parse_overall_status(soup),
            'components': self._parse_components(soup),
            'timestamp': timestamp,
            'last_updated': timestamp
        }

    def _determine_status_from_text(self, text: str, is_overall: bool = False) -> Tuple[str, str]:
        """
        Determine status level and description from text.
        
        Args:
            text: The status text to parse
            is_overall: Whether this is an overall status (affects how outages are labeled)
        """
        text = text.strip().lower()
        
        if "major" in text and "outage" in text:
            return ('major_outage' if is_overall else 'outage', text)
        elif "outage" in text:
            return ('outage', text)
        elif "degraded" in text:
            return ('degraded', text)
        elif "all systems operational" in text or "operational" in text:
            return ('operational', text)
        else:
            return ('unknown', text)

    def _parse_text_content(self, text: str) -> Dict[str, Any]:
        """Parse status page text content."""
        lines = text.strip().split('\n')
        timestamp = datetime.utcnow().isoformat()

        # Parse overall status
        overall_status = next((line.strip() for line in lines 
                             if any(x in line.lower() for x in ["systems", "outage", "degraded"])), "Unknown")
        overall_level, _ = self._determine_status_from_text(overall_status, is_overall=True)
        
        # Parse components
        components = {}
        current_component = None
        
        for line in lines:
            line = line.strip()
            if not line or "components" in line.lower():
                continue
                
            # Skip the header and overall status
            if "Anthropic Status" in line or line == overall_status:
                continue
                
            # Check if this is a component name (not a status line and not a divider)
            if not any(x in line for x in ["Operational", "Degraded", "Outage"]) and not all(c in '─_' for c in line):
                current_component = self._clean_component_name(line)
            # Check if this is a status line
            elif current_component and any(x in line for x in ["Operational", "Degraded", "Outage"]):
                status_level, _ = self._determine_status_from_text(line)
                components[current_component] = {
                    'status': status_level,
                    'uptime_percentage': None,
                    'uptime_period': None,
                    'status_history': [],
                    'timestamp': timestamp
                }

        # Parse last updated time
        last_updated = None
        for line in lines:
            if "Last Updated" in line:
                try:
                    time_str = line.split("um ")[-1].replace(" Uhr", "")
                    hour, minute = map(int, time_str.split(":"))
                    last_updated = datetime.now().replace(hour=hour, minute=minute).isoformat()
                except Exception as e:
                    logger.error(f"Failed to parse last updated time: {e}")
                    last_updated = timestamp

        return {
            'overall': {
                'description': overall_status,  # Keep original case for description
                'level': overall_level
            },
            'components': components,
            'timestamp': timestamp,
            'last_updated': last_updated or timestamp
        }

    def _parse_overall_status(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse overall system status from alert banner."""
        selectors = self._selectors['overall']
        banner = soup.select_one(selectors['banner'])
        status_text = soup.select_one(selectors['status'])
        
        if not banner or not status_text:
            return {
                'description': 'Unknown',
                'level': 'unknown'
            }
            
        text = status_text.text.strip()
        level, _ = self._determine_status_from_text(text, is_overall=True)
        
        return {
            'description': text,  # Keep original case for description
            'level': level
        }

    def _determine_status_level(self, status_classes: List[str]) -> str:
        """Determine status level from CSS classes."""
        status_map = {
            'operational': 'operational',
            'degraded': 'degraded',
            'outage': 'outage'
        }
        
        status_class = ' '.join(status_classes)
        return next((level for key, level in status_map.items() if key in status_class), 'unknown')

    def _parse_components(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        """Parse component statuses and uptime information."""
        selectors = self._selectors['component']
        components = {}
        timestamp = datetime.utcnow().isoformat()

        for element in soup.select(selectors['container']):
            name_elem = element.select_one(selectors['name'])
            status_elem = element.select_one(selectors['status'])
            uptime_elem = element.select_one(selectors['uptime'])
            
            if not name_elem:
                continue
                
            name = self._clean_component_name(name_elem.text.strip())
            
            # Get current status from status indicator
            current_status = 'unknown'
            if status_elem:
                status_text = status_elem.text.strip()
                current_status, _ = self._determine_status_from_text(status_text)
            
            # Parse uptime information
            uptime_info = self._parse_uptime_info(element)
            
            components[name] = {
                'status': current_status,
                'uptime_percentage': uptime_info.get('percentage'),
                'uptime_period': uptime_info.get('period'),
                'status_history': uptime_info.get('history', []),
                'timestamp': timestamp
            }

        return components

    def _parse_uptime_info(self, element: BeautifulSoup) -> Dict[str, Any]:
        """Parse uptime percentage, period and status history."""
        uptime_elem = element.select_one(self._selectors['component']['uptime'])
        period_elem = element.select_one(self._selectors['uptime']['period'])
        graph_elem = element.select_one(self._selectors['uptime']['graph'])
        
        # Parse uptime percentage
        uptime_percentage = None
        if uptime_elem and '%' in uptime_elem.text:
            try:
                uptime_percentage = float(uptime_elem.text.strip().replace('%', ''))
            except ValueError:
                pass
        
        # Parse uptime period
        period = "60 days"  # Default
        if period_elem:
            period = period_elem.text.strip()
        
        # Parse status history from bars
        history = []
        if graph_elem:
            for bar in graph_elem.select(self._selectors['uptime']['bars']):
                style = bar.get('style', '')
                color = next((c for c in self._status_colors.keys() 
                            if c.lower() in style.lower()), None)
                if color:
                    history.append(self._status_colors[color])
                else:
                    history.append('unknown')
        
        return {
            'percentage': uptime_percentage,
            'period': period,
            'history': history
        }
