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
    await update.message.reply_text("Este comando te conectará con un agente.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "Comandos disponibles:\n"
        "/contact - Contactar con un agente\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/db - Hacer una consulta a la base de datos (por ahora es un ejemplo simple)\n\n"
        "🤖 **Gestión de Inventario en Lenguaje Natural:**\n"
        "¡Ahora puedes hablarme de forma natural! Prueba estos ejemplos:\n"
        "• 'llegaron 2 kg de chocolate'\n"
        "• 'usé 500g de harina'\n"
        "• '¿cuánto azúcar tenemos?'\n"
        "• 'agregar nuevo ingrediente: extracto de vainilla 100ml'\n"
        "• 'establecer leche a 2 litros'\n"
        "• 'mostrar todo el inventario'"
    )
    await update.message.reply_text(help_text)


async def db_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /db command - Test adding chocolate to inventory."""
    try:
        # Check if chocolate already exists
        existing_chocolate = find_ingredient("Chocolate")
        
        if existing_chocolate:
            message = f"El chocolate ya existe en el inventario:\n" \
                     f"ID: {existing_chocolate.id}\n" \
                     f"Cantidad: {existing_chocolate.quantity} {existing_chocolate.unit}\n" \
                     f"Última actualización: {existing_chocolate.last_updated}"
        else:
            # Add 2 kg of chocolate to the inventory
            new_chocolate = add_ingredient("Chocolate", 2.0, "kg")
            
            if new_chocolate:
                message = f"¡Chocolate agregado exitosamente al inventario!\n" \
                         f"ID: {new_chocolate.id}\n" \
                         f"Nombre: {new_chocolate.ingredient_name}\n" \
                         f"Cantidad: {new_chocolate.quantity} {new_chocolate.unit}\n" \
                         f"Agregado en: {new_chocolate.last_updated}"
            else:
                message = "Error al agregar chocolate al inventario."
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in db_command: {e}")
        await update.message.reply_text(f"Error de base de datos: {str(e)}")


def handle_response(message: str) -> Optional[str]:
    """Generate a response based on the input message."""
    message = message.lower()
    
    if any(word in message for word in ["hola", "hello", "hi", "buenas", "saludos"]):
        return "¡Hola! Soy un bot de gestión de inventario de FFStudios 🤖\n\nPuedes decirme cosas como:\n• 'llegaron 2 kg de chocolate'\n• 'usé 500g de harina'\n• '¿cuánto azúcar tenemos?'"
    elif any(word in message for word in ["cómo estás", "how are you", "qué tal"]):
        return "Solo soy un bot, ¡pero estoy funcionando como se esperaba! Listo para ayudarte a gestionar tu inventario. 📦"
    elif any(word in message for word in ["adiós", "bye", "chao", "hasta luego"]):
        return "¡Hasta luego! 👋"
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
                response = "Lo siento, encontré un error al procesar tu solicitud de inventario."
        
        # Fallback response
        if response is None:
            response = "No estoy seguro de cómo ayudar con eso. ¡Prueba preguntando sobre inventario o escribe /help para ver los comandos disponibles!"
        
        if response:
            logger.info(f"Bot response to user {user_id}: {response}")
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Lo siento, encontré un error al procesar tu mensaje.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors that occur during bot operation."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)