"""
Telegram bot command handlers and message processing.
"""
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ..services.inventory_service import add_ingredient, find_ingredient

# Configure logging
logger = logging.getLogger(__name__)


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /contact command."""
    logger.info(f"Contact command received from user {update.effective_user.id}")
    await update.message.reply_text("this command will connect you to an agent.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "Available commands:\n"
        "/contact - Contact an agent\n"
        "/help - Show this help message\n"
        "/db - Make a database query (for now its a simple example)\n"
    )
    await update.message.reply_text(help_text)


async def db_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /db command - Test adding chocolate to inventory."""
    try:
        # Check if chocolate already exists
        existing_chocolate = find_ingredient("Chocolate")
        
        if existing_chocolate:
            message = f"Chocolate already exists in inventory:\n" \
                     f"ID: {existing_chocolate.id}\n" \
                     f"Quantity: {existing_chocolate.quantity} {existing_chocolate.unit}\n" \
                     f"Last updated: {existing_chocolate.last_updated}"
        else:
            # Add 2 kg of chocolate to the inventory
            new_chocolate = add_ingredient("Chocolate", 2.0, "kg")
            
            if new_chocolate:
                message = f"Successfully added chocolate to inventory!\n" \
                         f"ID: {new_chocolate.id}\n" \
                         f"Name: {new_chocolate.ingredient_name}\n" \
                         f"Quantity: {new_chocolate.quantity} {new_chocolate.unit}\n" \
                         f"Added at: {new_chocolate.last_updated}"
            else:
                message = "Failed to add chocolate to inventory."
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in db_command: {e}")
        await update.message.reply_text(f"Database error: {str(e)}")


def handle_response(message: str) -> str:
    """Generate a response based on the input message."""
    message = message.lower()
    
    if "hello" in message:
        return "Hi, I'm a FFStudios DB management bot"
    elif "how are you" in message:
        return "I'm just a bot, but I'm functioning as expected!"
    elif "bye" in message:
        return "Goodbye!"
    else:
        return "I donno wa to du"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    try:
        message_type: str = update.message.chat.type
        text: str = update.message.text
        user_id = update.effective_user.id
        
        # Get bot username from context
        bot_username = context.bot.username

        logger.info(f"User ({user_id}) in {message_type}: {text}")

        response: str = ""
        
        if message_type == "group":
            if bot_username and f"@{bot_username.lower()}" in text.lower():
                new_text = text.replace(f"@{bot_username}", "").strip()
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