# FFStudios Chat Bot

A sophisticated Telegram bot built with Python for database management and natural language processing. The bot provides an interface to interact with a PostgreSQL database through intuitive commands.

## Features

- 🤖 Telegram bot integration with command handling
- 🗄️ PostgreSQL database connectivity with SQLAlchemy ORM
- 📦 Modular architecture with organized codebase
- 🛡️ Robust error handling and logging
- 🔧 Easy configuration management
- 📊 Inventory management system

## Project Structure

```
ffstudios-chat-bot/
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── handlers.py        # Telegram bot handlers
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py             # Database connection management
│   │   └── models.py         # SQLAlchemy models
│   └── services/
│       ├── __init__.py
│       └── inventory_service.py # Business logic for inventory
├── scripts/                   # Utility scripts
├── docs/                     # Documentation
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Setup

### Prerequisites

- Python 3.8+ (recommended 3.10+)
- PostgreSQL database server
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

5. Set up environment variables:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your actual values
   ```

   Required environment variables:
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_BOT_USERNAME=your_bot_username_here
   
   # PostgreSQL Database Configuration
   PGHOST=localhost
   PGPORT=5432
   PGUSER=your_database_username
   PGPASSWORD=your_database_password
   PGDATABASE=ffstudios_chatbot_db
   ```

### Database Setup

1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE ffstudios_chatbot_db;
   ```

2. Create the inventory table:
   ```sql
   CREATE TABLE inventory (
       id SERIAL PRIMARY KEY,
       ingredient_name VARCHAR(100) NOT NULL,
       quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
       unit VARCHAR(20) NOT NULL,
       last_updated TIMESTAMP DEFAULT NOW()
   );
   ```

### Running the Bot

```bash
python main.py
```

## Available Commands

- `/help` - Display help information
- `/contact` - Connect to an agent
- `/db` - Test database functionality (adds/checks chocolate inventory)

## Development

### Code Organization

- **`src/bot/`** - Telegram bot handlers and configuration
- **`src/database/`** - Database models and connection management
- **`src/services/`** - Business logic and service classes
- **`scripts/`** - Utility scripts for development and deployment
- **`docs/`** - Project documentation

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code structure
4. Test your changes thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

### Development Setup

For development, you might want to install additional tools:

```bash
pip install black flake8 mypy pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
