"""
Natural Language Processing service using OpenAI GPT-4o-mini.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class InventoryAction:
    """Represents an inventory action parsed from natural language."""
    action: str  # 'register_purchase', 'register_expense', 'register_usage', 'check_stock', 'finance_report', 'unknown'
    ingredient_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    
    # Financial fields
    cost: Optional[float] = None
    currency: Optional[str] = None
    provider: Optional[str] = None
    payment_method: Optional[str] = None
    expense_category: Optional[str] = None # 'luz', 'agua', 'arriendo', 'comida', etc.
    
    reason: Optional[str] = None # For usage/waste
    
    confidence: float = 0.0

@dataclass
class MultipleInventoryActions:
    """Represents multiple inventory actions from a single message."""
    actions: List[InventoryAction]
    is_multiple: bool = True
    overall_confidence: float = 0.0

class NLPService:
    """Service for processing natural language inventory commands."""
    
    def __init__(self, api_key: str):
        """Initialize the NLP service with OpenAI API key."""
        self.client = OpenAI(api_key=api_key)
        
    def parse_inventory_message(self, message: str) -> InventoryAction:
        """
        Parse a natural language message into an inventory action.
        
        Args:
            message: User's message (e.g., "2 kg of chocolate arrived")
            
        Returns:
            InventoryAction object with parsed information
        """
        try:
            system_prompt = """
Eres un experto asistente de IA para la gestión de inventario y finanzas de un negocio (FFStudios).
Analiza el mensaje del usuario y extrae la intención estructurada.

SALIDA JSON (campos opcionales son null si no aplican):
{
  "action": "register_purchase" | "register_expense" | "register_usage" | "check_stock" | "finance_report" | "unknown",
  "ingredient_name": string | null, // Para compras/uso/stock
  "quantity": number | null,
  "unit": string | null,
  "cost": number | null, // Monto monetario
  "currency": "CLP" | "USD" | null,
  "provider": string | null, // Proveedor: Líder, CGE, SuKarne
  "payment_method": string | null, // Débito, Crédito, Transferencia, Efectivo
  "expense_category": string | null, // Para gastos fijos (Luz, Agua, Internet)
  "reason": string | null, // Para uso/baja (e.g. "para un queque")
  "confidence": number // 0.0 - 1.0
}

DEFINICIONES DE ACCIÓN:
1. "register_purchase": Compra de INSUMOS (ingredientes, materiales). Implica aumentar stock + registrar gasto.
   Ej: "Compré 2kg de azúcar por 8000 en el Líder con débito"
   -> action="register_purchase", ingredient="azúcar", quantity=2, unit="kg", cost=8000, provider="Líder", payment_method="débito"

2. "register_expense": Pago de SERVICIOS o GASTOS FIJOS (no inventario).
   Ej: "Pagué 35000 de luz a CGE con transferencia"
   -> action="register_expense", expense_category="luz", cost=35000, provider="CGE", payment_method="transferencia"

3. "register_usage": Salida de inventario (uso, consumo, baja).
   Ej: "Usé 1kg de harina para un queque"
   -> action="register_usage", ingredient="harina", quantity=1, unit="kg", reason="para un queque"

4. "check_stock": Consultar cantidad actual de inventario.
   Ej: "¿Cuánto chocolate nos queda?"

5. "finance_report": Consultas sobre gastos financieros.
   Ej: "¿Cuánto le compramos a santa isabel este mes?", "¿Cuánto gastamos en luz?", "¿Detalle de gastos por proveedor?"

NOTAS:
- Normaliza monedas: Si dice "8.000", es 8000.
- Si no menciona moneda, asume CLP si el contexto parece pesos chilenos.
- Para "check_stock" sin ingrediente ("¿Qué tenemos?"), usa ingredient_name="todo".
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Handle potential code block formatting
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            parsed_data = json.loads(content)
            
            return InventoryAction(
                action=parsed_data.get("action", "unknown"),
                ingredient_name=parsed_data.get("ingredient_name"),
                quantity=parsed_data.get("quantity"),
                unit=parsed_data.get("unit"),
                cost=parsed_data.get("cost"),
                currency=parsed_data.get("currency"),
                provider=parsed_data.get("provider"),
                payment_method=parsed_data.get("payment_method"),
                expense_category=parsed_data.get("expense_category"),
                reason=parsed_data.get("reason"),
                confidence=parsed_data.get("confidence", 0.0)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            logger.error(f"Raw response: {content}")
            return InventoryAction(action="unknown", ingredient_name="", confidence=0.0)
            
        except Exception as e:
            logger.error(f"Error parsing inventory message with OpenAI: {e}")
            return InventoryAction(action="unknown", ingredient_name="", confidence=0.0)

    def parse_multiple_ingredients_message(self, message: str) -> MultipleInventoryActions:
        """
        Parse a natural language message that may contain multiple ingredients.
        
        Args:
            message: User's message (e.g., "usamos 1 kg de harina, 2 kg de azucar y 200g de chocolate")
            
        Returns:
            MultipleInventoryActions object with parsed information
        """
        try:
            system_prompt = """
Eres un asistente de IA que analiza mensajes de gestión de inventario en español. 
Analiza el mensaje del usuario y extrae las acciones de inventario. El mensaje puede contener MÚLTIPLES ingredientes.

Devuelve un objeto JSON con estos campos:
- is_multiple: true si hay múltiples ingredientes, false si es solo uno
- actions: array de objetos de acción de inventario
- overall_confidence: puntuación de confianza general de 0.0 a 1.0

Cada objeto de acción debe tener:
- action: uno de "add_new", "add_quantity", "remove_quantity", "update_quantity", "check_stock", "unknown"
- ingredient_name: el nombre del ingrediente (string)
- quantity: la cantidad numérica (number, null si no se especifica)
- unit: la unidad de medida (string, null si no se especifica)
- confidence: puntuación de confianza de 0.0 a 1.0

Definiciones de acciones:
- "add_new": El usuario quiere agregar un ingrediente completamente nuevo
- "add_quantity": El usuario quiere agregar a stock existente (llegadas, reabastecimiento)
- "remove_quantity": El usuario quiere quitar del stock (uso, consumo)
- "update_quantity": El usuario quiere establecer una cantidad total específica
- "check_stock": El usuario quiere revisar los niveles de stock actuales
- "unknown": No se puede determinar la acción claramente

Ejemplos:

Mensaje con UN ingrediente:
"llegaron 2 kg de chocolate" → {
  "is_multiple": false,
  "actions": [{"action": "add_quantity", "ingredient_name": "chocolate", "quantity": 2.0, "unit": "kg", "confidence": 0.95}],
  "overall_confidence": 0.95
}

Mensaje con MÚLTIPLES ingredientes:
"usamos 1 kg de harina, 2 kg de azucar y 200g de chocolate" → {
  "is_multiple": true,
  "actions": [
    {"action": "remove_quantity", "ingredient_name": "harina", "quantity": 1.0, "unit": "kg", "confidence": 0.9},
    {"action": "remove_quantity", "ingredient_name": "azucar", "quantity": 2.0, "unit": "kg", "confidence": 0.9},
    {"action": "remove_quantity", "ingredient_name": "chocolate", "quantity": 0.2, "unit": "kg", "confidence": 0.9}
  ],
  "overall_confidence": 0.9
}

"llegaron 500g de sal, 1 litro de leche y 2 kg de azúcar" → {
  "is_multiple": true,
  "actions": [
    {"action": "add_quantity", "ingredient_name": "sal", "quantity": 0.5, "unit": "kg", "confidence": 0.9},
    {"action": "add_quantity", "ingredient_name": "leche", "quantity": 1.0, "unit": "liters", "confidence": 0.9},
    {"action": "add_quantity", "ingredient_name": "azúcar", "quantity": 2.0, "unit": "kg", "confidence": 0.9}
  ],
  "overall_confidence": 0.9
}

Reconoce patrones como:
- "usamos X de A, Y de B y Z de C" (remove_quantity)
- "llegaron X de A, Y de B y Z de C" (add_quantity)
- "compramos X de A, Y de B y Z de C" (add_quantity)
- "gastamos X de A, Y de B y Z de C" (remove_quantity)
- "consumimos X de A, Y de B y Z de C" (remove_quantity)

Convierte unidades cuando sea apropiado (g a kg, ml a litros, etc.).
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Handle potential code block formatting
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            parsed_data = json.loads(content)
            
            # Create InventoryAction objects from the actions array
            actions = []
            for action_data in parsed_data.get("actions", []):
                action = InventoryAction(
                    action=action_data.get("action", "unknown"),
                    ingredient_name=action_data.get("ingredient_name", ""),
                    quantity=action_data.get("quantity"),
                    unit=action_data.get("unit"),
                    confidence=action_data.get("confidence", 0.0)
                )
                actions.append(action)
            
            return MultipleInventoryActions(
                actions=actions,
                is_multiple=parsed_data.get("is_multiple", False),
                overall_confidence=parsed_data.get("overall_confidence", 0.0)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response for multiple ingredients: {e}")
            logger.error(f"Raw response: {content}")
            # Fallback to single ingredient parsing
            single_action = self.parse_inventory_message(message)
            return MultipleInventoryActions(
                actions=[single_action],
                is_multiple=False,
                overall_confidence=single_action.confidence
            )
            
        except Exception as e:
            logger.error(f"Error parsing multiple ingredients message with OpenAI: {e}")
            return MultipleInventoryActions(
                actions=[InventoryAction(action="unknown", ingredient_name="", confidence=0.0)],
                is_multiple=False,
                overall_confidence=0.0
            )

    def normalize_unit(self, unit: str, quantity: float) -> tuple[float, str]:
        """
        Normalize units to standard formats.
        
        Args:
            unit: Original unit
            quantity: Original quantity
            
        Returns:
            Tuple of (normalized_quantity, normalized_unit)
        """
        if not unit:
            return quantity, "pcs"
        
        unit = unit.lower().strip()
        
        # Weight conversions to kg
        if unit in ['g', 'gram', 'grams', 'gramo', 'gramos']:
            return quantity / 1000, "kg"
        elif unit in ['kg', 'kilogram', 'kilograms', 'kilo', 'kilos', 'kilogramo', 'kilogramos']:
            return quantity, "kg"
        
        # Volume conversions to liters
        elif unit in ['ml', 'milliliter', 'milliliters', 'mililitro', 'mililitros']:
            return quantity / 1000, "liters"
        elif unit in ['l', 'liter', 'liters', 'litre', 'litres', 'litro', 'litros']:
            return quantity, "liters"
        
        # Count units
        elif unit in ['pcs', 'pieces', 'piece', 'pc', 'units', 'unit', 'pieza', 'piezas', 'unidad', 'unidades']:
            return quantity, "pcs"
        
        # Default: return as-is
        else:
            return quantity, unit