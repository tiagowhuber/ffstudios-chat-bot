import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Import from organized modules
from src.bot.config import Config
from src.bot.handlers import (
    contact_command,
    help_command,
    db_command,
    handle_message,
    error_handler
)
from src.database.db import init_database, test_connection, close_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Main function to start the bot."""
    # Initialize configuration
    config = Config()
    config.validate()
    
    # Initialize database
    try:
        init_database()
        if test_connection():
            logger.info("Database connected successfully")
        else:
            logger.error("Database connection failed")
            raise RuntimeError("Failed to connect to database")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    
    # Create application
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("db", db_command))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    app.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is starting...")
    try:
        app.run_polling(poll_interval=3)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise
    finally:
        # Clean up database connections
        logger.info("Closing database connections...")
        close_database()


if __name__ == "__main__":
    main()