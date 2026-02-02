"""
Smart inventory service associated with Finance and NLP.
"""
import logging
from typing import Optional, Tuple, List

from .inventory_service import InventoryService
from .finance_service import FinanceService
from .nlp_service import NLPService, InventoryAction, MultipleInventoryActions

logger = logging.getLogger(__name__)

class SmartInventoryService:
    """Service that combines NLP with inventory and finance management."""
    
    def __init__(self, openai_api_key: str):
        self.nlp_service = NLPService(openai_api_key)
        self.inventory_service = InventoryService()
        self.finance_service = FinanceService()
    
    def process_natural_language_command(self, message: str) -> Tuple[bool, str]:
        """
        Process a natural language command.
        """
        try:
            # Check for multiple ingredients? (skipped for now to prioritize finance flows)
            # The NLP model can handle simple "Purchase X and Y" if we upgrade prompts later,
            # but for now let's persist single action focus for the new finance actions.
            
            action = self.nlp_service.parse_inventory_message(message)
            
            if action.confidence < 0.6:
                return False, f"No estoy seguro de lo que quisiste decir. Intenta ser más específico."
            
            # Normalize Units
            qty, unit = action.quantity, action.unit
            if qty and unit:
                qty, unit = self.nlp_service.normalize_unit(unit, qty)
            
            # ROUTING
            if action.action == "register_purchase":
                if not action.ingredient_name:
                    return False, "Para registrar una compra necesito saber qué compraste."
                
                result = self.finance_service.register_purchase(
                    product_name=action.ingredient_name,
                    quantity=qty or 1.0,
                    unit=unit or "unidad",
                    cost=action.cost or 0.0,
                    provider_name=action.provider,
                    payment_method_name=action.payment_method
                )
                if result:
                    return True, f" Compra registrada: {qty} {unit} de {action.ingredient_name} por ${action.cost} ({action.provider})"
                return False, " Error al registrar la compra."

            elif action.action == "register_expense":
                result = self.finance_service.register_expense(
                    category_name=action.expense_category or "General",
                    cost=action.cost or 0.0,
                    provider_name=action.provider,
                    payment_method_name=action.payment_method
                )
                if result:
                    return True, f" Gasto registrado: ${action.cost} en {action.expense_category}"
                return False, " Error al registrar el gasto."

            elif action.action == "register_usage":
                if not action.ingredient_name: return False, "Falta nombre del producto."
                inv = self.inventory_service.register_usage(
                    ingredient_name=action.ingredient_name,
                    quantity=qty or 1.0,
                    reason=action.reason or "Uso"
                )
                if inv:
                    return True, f" Uso registrado: {qty} {unit} de {action.ingredient_name}. Stock restante: {inv.quantity}"
                return False, " Error al registrar uso (posible stock insuficiente)."

            elif action.action == "check_stock":
                name = action.ingredient_name
                if name.lower() in ["todo", "inventario"]:
                    # All
                    items = self.inventory_service.list_all_ingredients()
                    if not items: return True, "Inventario vacío."
                    msg = " **Inventario:**\n"
                    for i in items:
                        msg += f"• {i.ingredient_name}: {i.quantity} {i.unit}\n"
                    return True, msg
                else:
                    # Specific
                    item = self.inventory_service.get_ingredient_by_name(name)
                    if not item:
                         # Fuzzy?
                         match = self.inventory_service.get_ingredient_by_name_fuzzy(name)
                         if match: 
                             item, score = match
                             return True, f" '{item.ingredient_name}' (conf{score:.2f}): {item.quantity} {item.unit}"
                         return True, "No se encontró el producto."
                    return True, f" {item.ingredient_name}: {item.quantity} {item.unit}"

            elif action.action == "finance_report":
                # Basic routing for now
                if "proveedor" in message.lower():
                    report = self.finance_service.get_expenses_by_provider()
                    return True, report
                return True, "Reporte financiero no implementado completamente."

            else:
                return False, "No entendí la acción solicitada."
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return False, f"Error del sistema: {str(e)}"
