# FFStudios Chat Bot

A simple Telegram bot built with Python that can respond to basic commands and messages.

## Features

- Basic command handling (`/start`, `/help`, `/custom`)
- Text message processing with keyword-based responses
- Group chat support with bot mention handling
- Environment variable configuration

## Setup

### Prerequisites

- Python 3.7+
- A Telegram Bot Token (get one from [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tiagowhuber/ffstudios-chat-bot.git
   cd ffstudios-chat-bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_BOT_USERNAME=your_bot_username_here
   ```

### Running the Bot

```bash
python main.py
```

## Commands

- `/start` - Start the bot and get a welcome message
- `/help` - Show available commands
- `/custom` - Get a custom response

## Message Responses

The bot responds to certain keywords in messages:
- "hello" → Greeting response
- "how are you" → Status response  
- "bye" → Goodbye response
- Other messages → Default response

## Project Structure

```
ffstudios-chat-bot/
├── main.py              # Main bot application
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (not in repo)
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).