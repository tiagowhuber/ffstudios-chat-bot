"""
Smart inventory service associated with Finance and NLP.
"""
import logging
from typing import Optional, Tuple, List, Dict, Any

from .inventory_service import InventoryService
from .finance_service import FinanceService
from .nlp_service import NLPService, InventoryAction, MultipleInventoryActions
from .data_analyst_service import DataAnalystService
from ..bot.conversation_state import (
    PendingAction,
    check_missing_fields,
    format_missing_fields_prompt
)

logger = logging.getLogger(__name__)

class SmartInventoryService:
    """Service that combines NLP with inventory and finance management."""
    
    def __init__(self, openai_api_key: str):
        self.nlp_service = NLPService(openai_api_key)
        self.inventory_service = InventoryService()
        self.finance_service = FinanceService()
        self.data_analyst_service = DataAnalystService(openai_api_key)
    
    def parse_supplemental_message(self, message: str, missing_fields: list) -> Dict[str, Any]:
        """
        Parse a supplemental message that provides missing information.
        
        Args:
            message: User's supplemental message (e.g., "lider, débito")
            missing_fields: List of fields we're expecting
            
        Returns:
            Dictionary with parsed supplemental data
        """
        try:
            # Build a targeted prompt for OpenAI to extract the requested fields
            field_descriptions = {
                'provider': 'nombre del proveedor (tienda, supermercado)',
                'payment_method': 'método de pago (débito, crédito, transferencia, efectivo)',
                'ingredient_name': 'nombre del producto o ingrediente',
                'quantity': 'cantidad numérica',
                'unit': 'unidad de medida (kg, litros, unidades)',
                'cost': 'costo o precio',
                'expense_category': 'categoría del gasto',
                'reason': 'motivo o razón'
            }
            
            fields_str = ', '.join([f'"{f}": {field_descriptions.get(f, f)}' for f in missing_fields])
            
            system_prompt = f"""
Eres un asistente que extrae información específica de mensajes cortos del usuario.
El usuario está proporcionando la siguiente información que faltaba: {fields_str}

Devuelve un JSON con SOLO los campos solicitados. Si no puedes identificar un campo, usa null.

Ejemplos:
Si falta [provider, payment_method] y el usuario dice "lider, débito":
{{"provider": "Líder", "payment_method": "Débito"}}

Si falta [cost, provider] y el usuario dice "$2500 en santa isabel":
{{"cost": 2500, "provider": "Santa Isabel"}}

Si falta [payment_method] y el usuario dice "con tarjeta de crédito":
{{"payment_method": "Tarjeta de Crédito"}}

IMPORTANTE:
- Normaliza nombres: "lider" -> "Líder", "debito" -> "Débito"
- Convierte montos: "2.500" o "$2500" -> 2500
- Mapea abreviaciones: "tc" -> "Tarjeta de Crédito", "td" -> "Tarjeta de Débito"
"""

            response = self.nlp_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Handle potential code block formatting
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            import json
            parsed_data = json.loads(content)
            
            logger.info(f"Parsed supplemental data: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing supplemental message: {e}")
            return {}
    
    def process_natural_language_command(self, message: str, pending_action: Optional[PendingAction] = None) -> Tuple[bool, str, Optional[PendingAction]]:
        """
        Process a natural language command.
        
        Args:
            message: User's message
            pending_action: Optional pending action from conversation state
            
        Returns:
            Tuple of (success, response_message, new_pending_action)
        """
        try:
            # If there's a pending action, try to supplement it with this message
            if pending_action:
                logger.info(f"Processing supplemental message for pending action: {pending_action.action}")
                
                # Parse the supplemental message
                supplement_data = self.parse_supplemental_message(message, pending_action.missing_fields)
                
                # Merge with pending action
                pending_action.merge_with_supplement(supplement_data)
                
                # Check if we still have missing fields
                if pending_action.missing_fields:
                    # Still missing some fields, ask again
                    prompt = format_missing_fields_prompt(pending_action.missing_fields)
                    return False, prompt, pending_action
                
                # All fields collected! Now execute the action
                action = pending_action
                logger.info(f"All fields collected, executing action: {action.action}")
                
            else:
                # No pending action, parse the message normally
                action = self.nlp_service.parse_inventory_message(message)
                
                if action.confidence < 0.6:
                    return False, f"No estoy seguro de lo que quisiste decir. Intenta ser más específico.", None
                
                # Convert InventoryAction to dict for checking missing fields
                action_dict = {
                    'ingredient_name': action.ingredient_name,
                    'quantity': action.quantity,
                    'unit': action.unit,
                    'cost': action.cost,
                    'provider': action.provider,
                    'payment_method': action.payment_method,
                    'expense_category': action.expense_category,
                    'reason': action.reason
                }
                
                # Check for missing required fields
                missing = check_missing_fields(action.action, action_dict)
                
                if missing:
                    # Create pending action
                    new_pending = PendingAction(
                        action=action.action,
                        original_message=message,
                        ingredient_name=action.ingredient_name,
                        quantity=action.quantity,
                        unit=action.unit,
                        cost=action.cost,
                        currency=action.currency,
                        provider=action.provider,
                        payment_method=action.payment_method,
                        expense_category=action.expense_category,
                        reason=action.reason,
                        missing_fields=missing
                    )
                    
                    prompt = format_missing_fields_prompt(missing)
                    return False, prompt, new_pending
            
            # Normalize Units
            qty, unit = action.quantity, action.unit
            if qty and unit:
                qty, unit = self.nlp_service.normalize_unit(unit, qty)
            
            # ROUTING - Execute the action
            if action.action == "register_purchase":
                if not action.ingredient_name:
                    return False, "Para registrar una compra necesito saber qué compraste.", None
                
                result = self.finance_service.register_purchase(
                    product_name=action.ingredient_name,
                    quantity=qty or 1.0,
                    unit=unit or "unidad",
                    cost=action.cost or 0.0,
                    provider_name=action.provider,
                    payment_method_name=action.payment_method
                )
                if result:
                    # Format a nice confirmation message
                    provider_text = f" en {action.provider}" if action.provider else ""
                    payment_text = f" con {action.payment_method}" if action.payment_method else ""
                    return True, f"✅ Compra registrada: {qty} {unit} de {action.ingredient_name} por ${action.cost}{provider_text}{payment_text}", None
                return False, "❌ Error al registrar la compra.", None

            elif action.action == "register_expense":
                result = self.finance_service.register_expense(
                    category_name=action.expense_category or "General",
                    cost=action.cost or 0.0,
                    provider_name=action.provider,
                    payment_method_name=action.payment_method
                )
                if result:
                    provider_text = f" a {action.provider}" if action.provider else ""
                    payment_text = f" con {action.payment_method}" if action.payment_method else ""
                    return True, f"✅ Gasto registrado: ${action.cost} en {action.expense_category}{provider_text}{payment_text}", None
                return False, "❌ Error al registrar el gasto.", None

            elif action.action == "register_usage":
                if not action.ingredient_name: 
                    return False, "Falta nombre del producto.", None
                inv = self.inventory_service.register_usage(
                    ingredient_name=action.ingredient_name,
                    quantity=qty or 1.0,
                    reason=action.reason or "Uso"
                )
                if inv:
                    return True, f"✅ Uso registrado: {qty} {unit} de {action.ingredient_name}. Stock restante: {inv.quantity}", None
                return False, "❌ Error al registrar uso (posible stock insuficiente).", None

            elif action.action == "check_stock":
                name = action.ingredient_name
                if name.lower() in ["todo", "inventario"]:
                    # All
                    items = self.inventory_service.list_all_ingredients()
                    if not items: return True, "Inventario vacío.", None
                    msg = "📦 **Inventario:**\n"
                    for i in items:
                        msg += f"• {i.ingredient_name}: {i.quantity} {i.unit}\n"
                    return True, msg, None
                else:
                    # Specific
                    item = self.inventory_service.get_ingredient_by_name(name)
                    if not item:
                         # Fuzzy?
                         match = self.inventory_service.get_ingredient_by_name_fuzzy(name)
                         if match: 
                             item, score = match
                             return True, f"📦 '{item.ingredient_name}' (conf{score:.2f}): {item.quantity} {item.unit}", None
                         return True, "No se encontró el producto.", None
                    return True, f"📦 {item.ingredient_name}: {item.quantity} {item.unit}", None

            elif action.action == "finance_report":
                logger.info(f"Routing finance report question to Data Analyst: {message}")
                result = self.data_analyst_service.generate_insight(message)
                return True, result, None

            else:
                return False, "No entendí la acción solicitada.", None
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return False, f"Error del sistema: {str(e)}", None
