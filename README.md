# anthropic-status-bot

discord bot that monitors anthropic's status page and provides real-time updates.

## features

- real-time status monitoring with in-place updates
- live status dashboard
- incident notifications
- component status tracking

## requirements

- Python 3.9 or higher
- pip (Python package installer)

## setup

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

## development

The bot is built with:
- discord.py - Discord API wrapper
- beautifulsoup4 - HTML parsing
- requests - HTTP client
- pydantic - Data validation
- APScheduler - Task scheduling

## license

this project is licensed under the [mit license](LICENSE)