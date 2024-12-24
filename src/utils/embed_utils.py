from datetime import datetime
from typing import Dict, Any
from discord import Embed

STATUS_COLORS = {
    "operational": 0x2ECC71,
    "degraded": 0xF1C40F,
    "outage": 0xE74C3C,
    "maintenance": 0x3498DB,
    "default": 0x95A5A6
}

def format_name(name: str) -> str:
    """Format component name for display."""
    return name.lower().replace("- beta features", " (beta)")

def format_status(status: str) -> str:
    """Format status text for display."""
    return status.lower()

def get_status_dot(status: str) -> str:
    """Get status indicator dot."""
    return "●" if any(s in status.lower() for s in ["operational", "maintenance", "resolved"]) else "○"

def create_status_embed(status: Dict[str, Any]) -> Embed:
    """Create status overview embed."""
    embed = Embed(
        title="anthropic status",
        description=f"{get_status_dot(status['overall']['level'])} {format_status(status['overall']['description'])}",
        color=STATUS_COLORS.get(status['overall']['level'], STATUS_COLORS['default'])
    )
    embed.timestamp = datetime.utcnow()

    # Add component statuses
    component_status = "\n".join(
        f"{get_status_dot(data['status'])} {format_name(name)} · {format_status(data['status'])}"
        for name, data in status['components'].items()
    )
    if component_status:
        embed.add_field(name="components", value=component_status, inline=False)

    # Add active incidents
    active_incidents = [i for i in status['incidents'] if i['status'] != 'resolved']
    if active_incidents:
        incidents_list = "\n\n".join(
            f"{get_status_dot(i['status'])} {format_status(i['name'])}\n   status: {format_status(i['status'])}"
            for i in active_incidents
        )
        embed.add_field(name="active incidents", value=incidents_list, inline=False)

    return embed

def create_incident_embed(incident: Dict[str, Any]) -> Embed:
    """Create incident details embed."""
    embed = Embed(
        title=format_status(incident['name']),
        description=f"impact: {format_status(incident['impact'])}\n"
                   f"{get_status_dot(incident['status'])} status: {format_status(incident['status'])}",
        color=STATUS_COLORS.get(incident['impact'], STATUS_COLORS['default'])
    )
    embed.timestamp = datetime.utcnow()

    # Add updates if available
    if incident.get('updates'):
        updates_text = "\n\n".join(
            f"{get_status_dot(update['status'])} {format_status(update['status'])}\n"
            f"    {datetime.fromisoformat(update['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"    {update['message']}"
            for update in incident['updates']
        )
        embed.add_field(name="updates", value=updates_text, inline=False)

    return embed