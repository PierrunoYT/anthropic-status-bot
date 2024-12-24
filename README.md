# anthropic-status-bot

discord bot that monitors anthropic's status page and provides real-time updates.

## features

- real-time status monitoring with in-place updates
- live status dashboard with custom embed formatting:
  - Overall system status with status indicators (○/●)
  - Component-wise status with indented layout
  - Active incident tracking
  - Timestamp with divider line
- incident notifications
- component status tracking

## requirements

- Python 3.9 or higher
- pip (Python package installer)

## local setup

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
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
CHECK_INTERVAL=5  # minutes between checks
LOG_LEVEL=info    # one of: info, warn, error
```

4. run
```bash
python src/index.py
```

## hosting service deployment

### sparked host setup
1. upload files to your server
2. set python version to 3.9 or higher in server panel
3. create .env file with your configuration
4. start the bot using the control panel

### other hosting services
The bot is compatible with any Python hosting service that supports:
- Python 3.9+
- Virtual environments
- Environment variables
- Background processes

## testing

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
- Status embed formatting and structure
- Component status display
- Incident handling
- Status indicators and visual elements

## development

The bot is built with:
- discord.py - Discord API wrapper
- beautifulsoup4 - HTML parsing
- requests - HTTP client
- pydantic - Data validation
- APScheduler - Task scheduling
- python-dotenv - Environment variable management
- tenacity - Retry handling
- lxml - XML/HTML processing

## license

this project is licensed under the [mit license](LICENSE)