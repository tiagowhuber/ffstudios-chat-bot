# FFStudios Chat Bot

A sophisticated Telegram bot built with Python for database management and natural language processing. The bot provides an interface to interact with a PostgreSQL database through intuitive commands.

## Features

-  Telegram bot integration with command handling
- 🗄️ PostgreSQL database connectivity with SQLAlchemy ORM
-  Modular architecture with organized codebase
- 🛡️ Robust error handling and logging
- 🔧 Easy configuration management
- 📊 Inventory management system

## Project Structure

```
ffstudios-chat-bot/
├── src/                       # Source code
│   ├── bot/
│   │   ├── config.py         # Configuration management
│   │   └── handlers.py       # Telegram bot handlers
│   ├── database/
│   │   ├── db.py            # Database connection management
│   │   ├── models.py        # SQLAlchemy models
│   │   └── databaseschema.pgsql
│   └── services/
│       ├── finance_service.py
│       ├── fuzzy_matcher.py
│       ├── inventory_service.py
│       ├── nlp_service.py
│       └── smart_inventory_service.py
├── examples/                  # Demo scripts and examples
│   ├── demo_finance.py       # Financial & inventory demo
│   └── README.md
├── tests/                     # Test suite
│   ├── conftest.py
│   ├── test_finance_flow.py
│   └── README.md
├── scripts/                   # Utility scripts
│   ├── init_db.py
│   └── run_bot.py
├── docs/                      # Documentation
├── main.py                    # Application entry point
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project configuration
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Setup

### Prerequisites

- Python 3.9+ (recommended 3.10+)
- Docker (for PostgreSQL database)
- A Telegram Bot Token (get one from [@BotFather](https://t.me/botfather))
- OpenAI API Key (for natural language processing features)

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
   PGPORT=5431
   PGUSER=postgres
   PGPASSWORD=your_secure_password_here
   PGDATABASE=postgres
   
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Database Setup
Start PostgreSQL using Docker:
   ```bash
   docker run --name ffstudios-db \
     -e POSTGRES_PASSWORD=your_password \
     -p 5431:5432 \
     -v ffstudios-data:/var/lib/postgresql/data \
     -d postgres
   ```

2. Verify the container is running:
   ```bash
   docker ps
   ```

3. The database tables will be created automatically when you first run the bot.

### Running the Bot

**Using the run script (recommended):**
```bash
python scripts/run_bot.py
```

**Or directly:**
```bash
python main.py
```

### Testing and Examples

**Run example demos:**
```bash
python examples/demo_finance.py
```

**Run tests:**
```bash
# Install dev dependencies first
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
python main.py
```
 and available commands
- `/contact` - Connect to an agent
- `/db` - Test database connectivity

The bot also supports natural language commands for:
- **Inventory Management**: "Llegaron 2kg de chocolate", "¿Cuánto azúcar tenemos?"
- **Financial Tracking**: "Pagué 45000 de internet a VTR", "¿Cuánto hemos gastado?"
- **Usage Recording**: "Usé 500g de harina para el pan"
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
