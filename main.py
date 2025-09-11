from typing import Final
import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def _load_dotenv(path: Path) -> None:
    """Load environment variables from a .env file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")
        return
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'\"")
        
        if key and key not in os.environ:
            os.environ[key] = val


# Load environment variables
_load_dotenv(Path(__file__).parent / ".env")

# Bot configuration
TOKEN: Final = os.environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.environ.get("TELEGRAM_BOT_USERNAME")


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    logger.info(f"Start command received from user {update.effective_user.id}")
    await update.message.reply_text("Hello! I'm your bot. How can I assist you today?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/custom - Show custom command response"
    )
    await update.message.reply_text(help_text)


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /custom command."""
    await update.message.reply_text("This is a custom command response.")


# Message handling
def handle_response(message: str) -> str:
    """Generate a response based on the input message."""
    message = message.lower()
    
    if "hello" in message:
        return "Hello! How can I help you?"
    elif "how are you" in message:
        return "I'm just a bot, but I'm functioning as expected!"
    elif "bye" in message:
        return "Goodbye! Have a great day!"
    else:
        return "I'm not sure how to respond to that."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    try:
        message_type: str = update.message.chat.type
        text: str = update.message.text
        user_id = update.effective_user.id

        logger.info(f"User ({user_id}) in {message_type}: {text}")

        response: str = ""
        
        if message_type == "group":
            if BOT_USERNAME and f"@{BOT_USERNAME.lower()}" in text.lower():
                new_text = text.replace(f"@{BOT_USERNAME}", "").strip()
                response = handle_response(new_text)
            else:
                return
        else:
            response = handle_response(text)
        
        if response:
            logger.info(f"Bot response to user {user_id}: {response}")
            await update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your message.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors that occur during bot operation."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

def main() -> None:
    """Main function to start the bot."""
    if not TOKEN:
        logger.error("No token provided. Please set the TELEGRAM_BOT_TOKEN environment variable.")
        raise ValueError("No token provided. Please set the TELEGRAM_BOT_TOKEN environment variable.")
    
    # Create application
    app = ApplicationBuilder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    
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


if __name__ == "__main__":
    main()