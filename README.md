# Anthropic Status Bot

Discord bot that monitors Anthropic's status page and provides real-time updates.

## Features

- real-time status monitoring with in-place updates
- live status dashboard with rich Discord embed formatting:
  - Color-coded status indicators (operational: green, degraded: yellow, outage: red)
  - Smart status dots (● for operational/resolved, ○ for issues)
  - Hierarchical component layout with proper indentation
  - Active incident tracking with impact levels
  - User-friendly timestamp formatting with divider line
  - Detailed incident updates with UTC timestamps
- incident notifications with impact level tracking (minor/major/critical)
- intelligent component status tracking:
  - Duplicate detection with configurable expiry window
  - Detailed state comparison and change detection
  - Timestamp tracking for each component
- robust error handling and logging:
  - Exponential backoff retry mechanism
  - Configurable retry attempts and timeouts
  - Structured logging with detailed formatting
  - Request logging with duration tracking
  - Error logging with context and stack traces
  - Multiple log levels (info, warn, error, debug)
  - UTC timestamp standardization
- advanced monitoring capabilities:
  - Configurable component filtering
  - Custom user agent support
  - Cache control
  - Flexible HTML parsing with configurable selectors
- monitored components:
  - console.anthropic.com
  - api.anthropic.com
  - api.anthropic.com - Beta Features
  - anthropic.com

## Requirements

- Python 3.9 or higher
- pip (Python package installer)

## Local Setup

1. clone and create virtual environment
```bash
git clone https://github.com/peltae/anthropic-status-bot.git
cd anthropic-status-bot
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

2. install dependencies
```bash
pip install -r requirements.txt
```

3. configure
```bash
# copy example environment file
cp .env.example .env

# edit .env file with your settings:
DISCORD_TOKEN=your_bot_token                # Discord bot token
DISCORD_CHANNEL_ID=your_channel_id          # Channel for status updates
CHECK_INTERVAL=5                            # Minutes between checks (minimum: 1)
LOG_LEVEL=info                              # Logging level (info, warn, error, debug)

# Advanced Configuration (optional):
# Status Page Configuration:
STATUS__URL=https://status.anthropic.com    # Status page URL
STATUS__TIMEOUT=10000                       # Request timeout in ms
STATUS__RETRIES=3                          # Number of retry attempts
STATUS__USER_AGENT=AnthropicStatusBot/1.0  # Custom user agent

# Logging Configuration:
LOGGING__FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Log format
LOGGING__DATE_FORMAT="%Y-%m-%d %H:%M:%S"                               # Date format
```

4. run
```bash
python src/index.py
```

## Hosting Service Deployment

### Sparked Host Setup
1. upload files to your server
2. set python version to 3.9 or higher in server panel
3. create .env file with your configuration
4. start the bot using the control panel

### Other Hosting Services
The bot is compatible with any Python hosting service that supports:
- Python 3.9+
- Virtual environments
- Environment variables
- Background processes

## Testing

Run the test suite to verify embed formatting and functionality. You have multiple options:

1. Using pytest directly:
```bash
# Activate virtual environment if not already active
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/MacOS

# Run tests
python -m pytest src/tests/test_bot.py -v
```

2. Using provided test runners:
```bash
# On Windows:
.\run_tests.ps1

# On Unix/MacOS:
python run_test.py
```

The test suite verifies:
- Status embed formatting and structure:
  - Color codes and status indicators
  - Component hierarchy and indentation
  - Timestamp formatting
  - Status dot logic
- Component status tracking:
  - State changes and updates
  - Status level determination
- Incident handling:
  - Impact level assessment
  - Update tracking
  - Resolution detection

## Development

The bot is built with:
- discord.py - Discord API wrapper
- beautifulsoup4 - HTML parsing
- requests - HTTP client
- pydantic - Data validation
- APScheduler - Task scheduling
- python-dotenv - Environment variable management
- tenacity - Retry handling
- lxml - XML/HTML processing

## License

This project is licensed under the [MIT License](LICENSE)