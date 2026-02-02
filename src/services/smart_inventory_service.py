"""
Smart inventory service associated with Finance and NLP.
"""
import logging
from typing import Optional, Tuple, List

from .inventory_service import InventoryService
from .finance_service import FinanceService
from .nlp_service import NLPService, InventoryAction, MultipleInventoryActions
from .data_analyst_service import DataAnalystService

logger = logging.getLogger(__name__)

class SmartInventoryService:
    """Service that combines NLP with inventory and finance management."""
    
    def __init__(self, openai_api_key: str):
        self.nlp_service = NLPService(openai_api_key)
        self.inventory_service = InventoryService()
        self.finance_service = FinanceService()
        self.data_analyst_service = DataAnalystService(openai_api_key)
    
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
                return False, " Error al registrar la compra. El formato para registrar compras es: 'Compré <cantidad> <unidad> de <producto> por <costo> en <proveedor>'. (Ejemplo: 'Compré 2 kg de arroz por $3000 en Líder')"

            elif action.action == "register_expense":
                result = self.finance_service.register_expense(
                    category_name=action.expense_category or "General",
                    cost=action.cost or 0.0,
                    provider_name=action.provider,
                    payment_method_name=action.payment_method
                )
                if result:
                    return True, f" Gasto registrado: ${action.cost} en {action.expense_category}"
                return False, " Error al registrar el gasto. El formato para registrar gastos es: 'Gasté <cantidad> en <categoría> con <método de pago>'. (Ejemplo: 'Gasté $500 en CGE con tarjeta de crédito')."

            elif action.action == "register_usage":
                if not action.ingredient_name: return False, "Falta nombre del producto."
                inv = self.inventory_service.register_usage(
                    ingredient_name=action.ingredient_name,
                    quantity=qty or 1.0,
                    reason=action.reason or "Uso"
                )
                if inv:
                    return True, f" Uso registrado: {qty} {unit} de {action.ingredient_name}. Stock restante: {inv.quantity}"
                return False, " Error al registrar uso (posible stock insuficiente). El formato para registrar uso es: 'Usé <cantidad> <unidad> de <producto> para la receta <nombre>'. (Ejemplo: 'Usé 1 kg de harina para la receta torta')"

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
                logger.info(f"Routing finance report question to Data Analyst: {message}")
                result = self.data_analyst_service.generate_insight(message)
                return True, result

            else:
                return False, "No entendí la acción solicitada."
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return False, f"Error del sistema: {str(e)}"
