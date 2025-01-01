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
    return name.lower().replace("- beta features", "(beta)")

def format_status(status: str) -> str:
    """Format status text for display."""
    return status.lower()

def get_status_dot(status: str) -> str:
    """Get status indicator dot using colored circle emojis."""
    status_lower = status.lower()
    if any(s in status_lower for s in ["operational"]):
        return "🟢"  # Green circle for operational
    elif any(s in status_lower for s in ["degraded"]):
        return "🟡"  # Yellow circle for degraded
    elif any(s in status_lower for s in ["outage"]):
        return "🔴"  # Red circle for outage
    elif any(s in status_lower for s in ["maintenance", "resolved"]):
        return "🔵"  # Blue circle for maintenance/resolved
    else:
        return "⚪"  # White circle for unknown/default

def create_status_embed(status: Dict[str, Any]) -> Embed:
    """Create status overview embed."""
    now = datetime.utcnow()
    status_level = status['overall']['level']
    embed = Embed(
        title="☀️ Anthropic Status",
        description=f"{get_status_dot(status['overall']['description'])} {format_status(status['overall']['description'])}",
        color=STATUS_COLORS.get(status_level, STATUS_COLORS['default'])
    )

    # Add component statuses with proper spacing
    components_text = []
    for name, data in status['components'].items():
        components_text.append(f"{get_status_dot(data['status'])} {format_name(name)}\n└─ {format_status(data['status'])}")
    
    if components_text:
        embed.add_field(
            name="components",
            value="\n\n".join(components_text),
            inline=False
        )
    
    # Set footer with divider and timestamp
    embed.set_footer(text=f"─────────────\nLast Updated • {now.strftime('%I:%M %p')}")

    return embed

def create_incident_embed(incident: Dict[str, Any]) -> Embed:
    """Create incident details embed."""
    embed = Embed(
        title=format_status(incident['name']),
        description=f"impact: {format_status(incident['impact'])}\n{get_status_dot(incident['status'])} status: {format_status(incident['status'])}",
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