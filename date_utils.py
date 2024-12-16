from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def parse_timestamp(timestamp_str: str) -> str:
    """Parse timestamp string to ISO format in UTC."""
    try:
        # Try different timestamp formats
        formats = [
            "%B %d, %Y %I:%M %p",  # "November 28, 2024 04:47 PM"
            "%b %d, %Y %H:%M",     # "Nov 28, 2024 16:47"
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
            
        # Add 8 hours to convert PST to UTC (simplified conversion)
        utc_dt = dt + timedelta(hours=8)
        return utc_dt.isoformat() + "Z"  # Adding Z to indicate UTC
    except Exception as e:
        logger.warning(f"Error parsing timestamp '{timestamp_str}': {str(e)}")
        return datetime.utcnow().isoformat() + "Z"  # Adding Z to indicate UTC

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format UTC."""
    return datetime.utcnow().isoformat() + "Z"

def format_datetime(dt: datetime, include_year: bool = True) -> str:
    """Format datetime object to string."""
    if include_year:
        return dt.strftime("%B %d, %Y %I:%M %p")
    return dt.strftime("%B %d %I:%M %p")