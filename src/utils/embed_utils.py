from discord import Embed, Colour
from datetime import datetime
from typing import Dict, Any, List

STATUS_COLORS = {
    'operational': Colour.green(),
    'degraded': Colour.gold(),
    'outage': Colour.red(),
    'maintenance': Colour.blue(),
    'default': Colour.light_grey()
}

def format_name(name: str) -> str:
    """Format component name."""
    return name.lower().replace('- beta features', ' (beta)')

def format_status(status: str) -> str:
    """Format status text."""
    return status.lower()

def get_status_dot(status: str) -> str:
    """Get status indicator dot."""
    return '●' if any(s in status.lower() for s in ['operational', 'maintenance', 'resolved']) else '○'

def create_status_embed(status: Dict[str, Any]) -> Embed:
    """Create status embed message."""
    embed = Embed(
        title='anthropic status',
        description=f"{get_status_dot(status['overall']['level'])} {format_status(status['overall']['description'])}",
        colour=STATUS_COLORS.get(status['overall']['level'], STATUS_COLORS['default']),
        timestamp=datetime.utcnow()
    )

    # Add components status
    component_status = '\n'.join(
        f"{get_status_dot(data['status'])} {format_name(name)} · {format_status(data['status'])}"
        for name, data in status['components'].items()
    )

    if component_status:
        embed.add_field(name='components', value=component_status, inline=False)

    # Filter and sort active incidents
    active_incidents = [
        i for i in status['incidents']
        if i['status'] != 'resolved'
    ]
    
    priority_map = {'critical': 3, 'major': 2, 'minor': 1, 'none': 0}
    active_incidents.sort(key=lambda x: priority_map.get(x['impact'], 0), reverse=True)

    if active_incidents:
        incidents_list = '\n\n'.join(
            f"{get_status_dot(i['status'])} {format_status(i['name'])}\n    status: {format_status(i['status'])}"
            for i in active_incidents
        )
        embed.add_field(name='active incidents', value=incidents_list, inline=False)

    embed.set_footer(text='last updated')
    return embed

def create_incident_embed(incident: Dict[str, Any]) -> Embed:
    """Create incident embed message."""
    embed = Embed(
        title=format_status(incident['name']),
        colour=STATUS_COLORS.get(incident['impact'], STATUS_COLORS['default']),
        timestamp=datetime.utcnow()
    )

    # Set description with impact and status
    embed.description = (
        f"impact: {format_status(incident['impact'])}\n"
        f"{get_status_dot(incident['status'])} status: {format_status(incident['status'])}\n\n"
        f"timeline:"
    )

    # Add updates if available
    if incident.get('updates'):
        updates_text = '\n\n'.join(
            f"{get_status_dot(update['status'])} {format_status(update['status'])}  ·  "
            f"{datetime.fromisoformat(update['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"    {format_status(update['message'])}"
            for update in incident['updates']
        )
        embed.add_field(name='updates', value=updates_text, inline=False)

    return embed