# Anthropic Status Bot

A Discord bot that monitors Anthropic's status page and provides real-time updates about system status, incidents, and component health.

## Features

- Real-time monitoring of Anthropic's status page
- Automatic status updates in a designated Discord channel
- Component status tracking
- Incident reporting and updates
- Configurable check intervals

## Requirements

- Python 3.9 or higher (3.11+ recommended for best performance)
- Discord Bot Token
- Discord Channel ID

## Required Bot Permissions

The bot requires the following Discord permissions and intents:

### Intents
- Message Content Intent (Privileged Intent)
- Default Intents

### Bot Permissions
The bot requires the following specific permissions:
- View Channels (to see the channel)
- Send Messages (to post status updates)
- Manage Messages (to edit status messages)
- Embed Links (to send rich embeds)
- Read Message History (to update existing messages)

Permissions Integer: 68608
To set up these permissions:
1. Go to the Discord Developer Portal
2. Select your application
3. Navigate to the "Bot" section
4. Enable "Message Content Intent" under Privileged Gateway Intents
5. In the OAuth2 URL Generator:
   - Select "bot" scope
   - Select the required permissions listed above
   - Use the generated URL to invite the bot to your server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PierrunoYT/anthropic-status-bot.git
cd anthropic-status-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Required package versions:
- discord.py >= 2.3.2
- aiohttp >= 3.9.1
- beautifulsoup4 >= 4.12.2
- python-dotenv >= 1.0.0
- apscheduler >= 3.10.4
- python-dateutil >= 2.8.2
- pydantic >= 2.5.3
- pydantic-settings >= 2.1.0

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
python main.py
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

## Troubleshooting

### Permission Issues

If you see "403 Forbidden: Missing Permissions" errors in the logs:

1. Verify Bot Permissions:
   - Go to your Discord server settings
   - Click on "Roles"
   - Find your bot's role
   - Enable exactly these permissions:
     * View Channels
     * Send Messages
     * Manage Messages
     * Embed Links
     * Read Message History
   - Or use this permissions integer in the OAuth2 URL: 68608

2. Check Channel Permissions:
   - Right-click the channel where the bot posts updates
   - Click "Edit Channel"
   - Go to "Permissions"
   - Find your bot's role
   - Ensure all required permissions are enabled for that channel

3. Bot Role Position:
   - In server settings under "Roles"
   - Make sure the bot's role is positioned high enough to have permission to manage messages
   - Drag the bot's role above any roles it needs to manage

4. Channel Type:
   - Ensure the configured channel is a text channel
   - The bot cannot post updates in voice channels, forums, or announcement channels

If issues persist:
1. Remove the bot from your server
2. Generate a new invite link with all required permissions
3. Reinvite the bot using the new link

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Anthropic Status Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```