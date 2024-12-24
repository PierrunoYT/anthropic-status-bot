import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from config import config

# Configure logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Create logger
logger = logging.getLogger('anthropic_status')
logger.setLevel(getattr(logging, config.logging.level.upper()))
logger.addHandler(console_handler)

def log_request(method: str, url: str, duration: float, status: int) -> None:
    """Log HTTP request details."""
    logger.info(
        f"HTTP {method} {url} - Status: {status} - Duration: {duration:.2f}ms"
    )

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log error with context."""
    error_details = {
        'error': str(error),
        'type': error.__class__.__name__,
        'timestamp': datetime.utcnow().isoformat(),
        **(context or {})
    }
    
    logger.error(
        f"Error in {context.get('operation', 'unknown_operation') if context else 'unknown_operation'}: "
        f"{error_details['error']}",
        extra={'error_details': error_details},
        exc_info=True
    )

# Export commonly used logging methods
info = logger.info
warn = logger.warning
error = logger.error
debug = logger.debug