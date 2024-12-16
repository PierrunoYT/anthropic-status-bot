# Anthropic Status Bot

## 🌟 Introduction

The **Anthropic Status Bot** is a Discord bot designed to monitor and report the real-time status of Anthropic's services. It fetches data from Anthropic's status page and posts updates to a designated Discord channel. The bot notifies users about service outages, degraded performance, and active incidents, ensuring teams and communities stay informed.

---

## ✨ Features

- **Real-Time Status Monitoring**: Fetches and parses the status of Anthropic services.
- **Discord Integration**: Posts updates directly to a specified Discord channel.
- **Incident Tracking**: Highlights active incidents with severity levels.
- **Customizable Alerts**: Sends notifications for status changes or critical incidents.
- **Uptime Overview**: Provides uptime metrics, including percentage, history, and periods.
- **Emoji Indicators**: Uses intuitive emojis to represent service statuses:
  - 🟢 Operational
  - 🟡 Degraded
  - 🔴 Outage
  - 🔵 Maintenance

---

## 🛠️ Requirements

The following dependencies are required to run the bot:

| Dependency       | Version      |
|------------------|--------------|
| `discord.py`     | `>=2.3.2`    |
| `aiohttp`        | `>=3.9.1`    |
| `beautifulsoup4` | `>=4.12.2`   |
| `python-dotenv`  | `>=1.0.0`    |
| `apscheduler`    | `>=3.10.4`   |
| `python-dateutil`| `>=2.8.2`    |
| `pydantic`       | `>=2.5.3`    |
| `pydantic-settings` | `>=2.1.0` |

Ensure Python 3.8 or higher is installed.

---

## 🚀 Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/PierrunoYT/anthropic-status-bot.git
   cd anthropic-status-bot
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory with the following variables:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_channel_id
   CHECK_INTERVAL=5
   LOG_LEVEL=info
   ```

---

## 📖 Usage

1. **Run the Bot**:
   ```bash
   python main.py
   ```

2. **Discord Commands**:
   - The bot automatically posts updates to the configured channel at regular intervals.
   - Status updates are pinned for visibility.

3. **Monitor Logs**:
   Logs are generated for debugging and tracking bot activities.

---

## ⚙️ Configuration

The bot's configuration is managed via the `config.py` file and `.env` variables.

### Key Configurations:
- **Status Monitoring**:
  - URL: `https://status.anthropic.com`
  - Components: Specific services to monitor.
- **Discord Bot**:
  - Token: Your bot's authentication token.
  - Channel ID: Target Discord channel for updates.
  - Check Interval: Frequency (in minutes) for status checks.
- **Logging**:
  - Levels: `none`, `debug`, `info`, `warn`, `error`.

---

## 🤝 Contributing

Contributions are welcome! Follow these steps:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of the feature or fix"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.