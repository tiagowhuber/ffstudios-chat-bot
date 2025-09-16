"""
Telegram bot command handlers and message processing.
"""
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ..services.inventory_service import add_ingredient, find_ingredient
from ..services.smart_inventory_service import SmartInventoryService
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize smart inventory service
config = Config()
smart_inventory = SmartInventoryService(config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None


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
        "/db - Make a database query (for now its a simple example)\n\n"
        "🤖 **Natural Language Inventory Management:**\n"
        "You can now talk to me naturally! Try these examples:\n"
        "• '2 kg of chocolate arrived'\n"
        "• 'used 500g of flour'\n"
        "• 'how much sugar do we have?'\n"
        "• 'add new ingredient: vanilla extract 100ml'\n"
        "• 'set milk to 2 liters'\n"
        "• 'show me all inventory'"
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


def handle_response(message: str) -> Optional[str]:
    """Generate a response based on the input message."""
    message = message.lower()
    
    if "hello" in message:
        return "Hi, I'm a FFStudios DB management bot! 🤖\n\nYou can tell me things like:\n• '2 kg of chocolate arrived'\n• 'used 500g of flour'\n• 'how much sugar do we have?'"
    elif "how are you" in message:
        return "I'm just a bot, but I'm functioning as expected! Ready to help you manage your inventory. 📦"
    elif "bye" in message:
        return "Goodbye! 👋"
    else:
        return None  # Let smart inventory handle it


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    try:
        message_type: str = update.message.chat.type
        text: str = update.message.text
        user_id = update.effective_user.id
        
        # Get bot username from context
        bot_username = context.bot.username

        logger.info(f"User ({user_id}) in {message_type}: {text}")

        # Handle group messages
        if message_type == "group":
            if bot_username and f"@{bot_username.lower()}" in text.lower():
                text = text.replace(f"@{bot_username}", "").strip()
            else:
                return
        
        # Try basic responses first
        response = handle_response(text)
        
        # If no basic response and smart inventory is available, try NLP processing
        if response is None and smart_inventory:
            try:
                success, nlp_response = smart_inventory.process_natural_language_command(text)
                response = nlp_response
            except Exception as e:
                logger.error(f"Error in smart inventory processing: {e}")
                response = "Sorry, I encountered an error processing your inventory request."
        
        # Fallback response
        if response is None:
            response = "I'm not sure how to help with that. Try asking about inventory or type /help for available commands!"
        
        if response:
            logger.info(f"Bot response to user {user_id}: {response}")
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your message.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors that occur during bot operation."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)