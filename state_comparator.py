from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class StateComparator:
    @staticmethod
    def compare_states(previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            logger.error(f"Error comparing states: {str(e)}")
            
        return updates

    @staticmethod
    def format_component_statuses(components: Dict[str, Dict[str, str]]) -> str:
        """Format component statuses for display."""
        return '\n'.join(f"{name}: {data['status']}" for name, data in components.items())