# Anthropic Status Bot

A Discord bot that monitors Anthropic's status page and provides real-time updates about system status, incidents, and component health.

## Features

- Real-time monitoring of Anthropic's status page
- Automatic status updates in a designated Discord channel
- Component status tracking
- Incident reporting and updates
- Configurable check intervals

## Requirements

- Python 3.9 or higher
- Discord Bot Token
- Discord Channel ID

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/anthropic-status-bot.git
cd anthropic-status-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Configure your environment variables in `.env`:
```
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
CHECK_INTERVAL=5
LOG_LEVEL=info
```

## Usage

Run the bot:
```bash
python src/main.py
```

The bot will:
- Connect to Discord using your bot token
- Monitor Anthropic's status page at the specified interval
- Post updates to the configured Discord channel
- Send notifications for any status changes or incidents

## Configuration

- `DISCORD_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL_ID`: The ID of the channel where updates will be posted
- `CHECK_INTERVAL`: How often to check for updates (in minutes)
- `LOG_LEVEL`: Logging level (none, debug, info, warn, error)

## License

ISC License