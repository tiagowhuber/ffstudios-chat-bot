# FFStudios Chat Bot Documentation

This directory contains documentation for the FFStudios Chat Bot project.

## Available Documentation

- **API Documentation**: Coming soon
- **Database Schema**: See `database_schema.md`
- **Deployment Guide**: See `deployment.md`
- **Development Guide**: See the main README.md

## Getting Started

For quick start instructions, refer to the main [README.md](../README.md) in the project root.

## Architecture Overview

The bot follows a modular architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │ -> │   Bot Handlers  │ -> │    Services     │
│   (External)    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       v
                                               ┌─────────────────┐
                                               │    Database     │
                                               │   (PostgreSQL)  │
                                               └─────────────────┘
```

## Components

### Bot Layer (`src/bot/`)
- **handlers.py**: Telegram command and message handlers
- **config.py**: Configuration management and environment variables

### Database Layer (`src/database/`)
- **db.py**: Database connection management and session handling
- **models.py**: SQLAlchemy ORM models

### Services Layer (`src/services/`)
- **inventory_service.py**: Business logic for inventory management

### Scripts (`scripts/`)
- **init_db.py**: Database initialization script
- **run_bot.py**: Development utility to start the bot