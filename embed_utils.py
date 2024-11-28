from discord import Embed, Colour
from datetime import datetime
from typing import Dict, Any, List

STATUS_COLORS = {
    'operational': Colour.from_rgb(40, 167, 69),  # Brighter green
    'degraded': Colour.from_rgb(255, 193, 7),     # Warmer yellow
    'outage': Colour.from_rgb(220, 53, 69),       # Brighter red
    'maintenance': Colour.from_rgb(0, 123, 255),   # Brighter blue
    'default': Colour.from_rgb(108, 117, 125)     # Darker grey
}

STATUS_EMOJIS = {
    'operational': '🟢',
    'degraded': '🟡',
    'outage': '🔴',
    'maintenance': '🔵',
    'default': '⚪'
}

def format_name(name: str) -> str:
    """Format component name with proper capitalization."""
    name = name.replace('- beta features', ' (beta)')
    return ' '.join(word.capitalize() for word in name.split())

def format_status(status: str) -> str:
    """Format status text with proper capitalization."""
    return status.capitalize()

def get_status_indicator(status: str) -> str:
    """Get status indicator emoji."""
    status_lower = status.lower()
    if 'operational' in status_lower:
        return STATUS_EMOJIS['operational']
    elif 'maintenance' in status_lower:
        return STATUS_EMOJIS['maintenance']
    elif 'resolved' in status_lower:
        return STATUS_EMOJIS['operational']
    elif 'degraded' in status_lower:
        return STATUS_EMOJIS['degraded']
    elif 'outage' in status_lower:
        return STATUS_EMOJIS['outage']
    return STATUS_EMOJIS['default']

def create_status_embed(status: Dict[str, Any]) -> Embed:
    """Create status embed message."""
    embed = Embed(
        title='🌟 Anthropic Status',
        description=f"{get_status_indicator(status['overall']['level'])} **{format_status(status['overall']['description'])}**",
        colour=STATUS_COLORS.get(status['overall']['level'], STATUS_COLORS['default']),
        timestamp=datetime.utcnow()
    )

    # Add components status
    component_status = '\n'.join(
        f"{get_status_indicator(data['status'])} **{format_name(name)}**\n┗━ {format_status(data['status'])}"
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
            f"{get_status_indicator(i['status'])} **{format_status(i['name'])}**\n┗━ Status: {format_status(i['status'])}"
            for i in active_incidents
        )
        embed.add_field(name='🚨 Active Incidents', value=incidents_list, inline=False)

    # Add divider before footer
    embed.add_field(name='', value='━━━━━━━━━━━━━━━', inline=False)
    embed.set_footer(text='Last Updated')
    return embed

def create_incident_embed(incident: Dict[str, Any], update: Dict[str, Any] = None) -> Embed:
    """Create incident embed message."""
    embed = Embed(
        title=format_status(incident['name']),
        colour=STATUS_COLORS.get(incident['impact'], STATUS_COLORS['default'])
    )

    if update:
        # Use the update's timestamp
        embed.timestamp = datetime.fromisoformat(update['timestamp'].replace('Z', '+00:00'))
        
        # Set description with status and message
        status_indicator = get_status_indicator(update['status'])
        embed.description = (
            f"{status_indicator} **{format_status(update['status'])}**\n"
            f"{update['message']}"
        )
    else:
        # Use current time and latest update
        embed.timestamp = datetime.utcnow()
        latest_update = incident['updates'][0] if incident.get('updates') else None
        
        if latest_update:
            status_indicator = get_status_indicator(latest_update['status'])
            embed.description = (
                f"{status_indicator} **{format_status(latest_update['status'])}**\n"
                f"{latest_update['message']}"
            )
        else:
            embed.description = f"🔍 **Status**: {format_status(incident['status'])}"

    return embed