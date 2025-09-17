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
    action: str  # 'add_new', 'add_quantity', 'remove_quantity', 'update_quantity', 'check_stock', 'unknown'
    ingredient_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
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
Eres un asistente de IA que analiza mensajes de gestión de inventario en español. 
Analiza el mensaje del usuario y extrae las acciones de inventario.

Devuelve un objeto JSON con estos campos:
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

Ejemplos en español:
"llegaron 2 kg de chocolate" → {"action": "add_quantity", "ingredient_name": "chocolate", "quantity": 2.0, "unit": "kg", "confidence": 0.95}
"usé 500g de harina" → {"action": "remove_quantity", "ingredient_name": "harina", "quantity": 0.5, "unit": "kg", "confidence": 0.9}
"agregar nuevo ingrediente: extracto de vainilla 100ml" → {"action": "add_new", "ingredient_name": "extracto de vainilla", "quantity": 100.0, "unit": "ml", "confidence": 0.9}
"¿cuánto azúcar tenemos?" → {"action": "check_stock", "ingredient_name": "azúcar", "quantity": null, "unit": null, "confidence": 0.85}
"establecer leche a 2 litros" → {"action": "update_quantity", "ingredient_name": "leche", "quantity": 2.0, "unit": "litros", "confidence": 0.9}

Para consultas de inventario completo, usa ingredient_name: "todo":
"¿Qué tenemos en stock?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Qué hay disponible?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Qué productos hay?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Cómo va el conteo?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Cuál es el stock disponible?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Cuál es el acervo de productos?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Cuál es el catálogo de artículos?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}
"¿Cuál es la existencia de mercancía?" → {"action": "check_stock", "ingredient_name": "todo", "quantity": null, "unit": null, "confidence": 0.9}

Acepta variaciones como:
- "recibimos", "llegó", "entró", "compramos" para add_quantity
- "usé", "gasté", "consumí", "utilicé" para remove_quantity
- "¿cuánto hay de...?", "stock de...", "cantidad de...", "¿qué tenemos?", "¿qué hay?", "inventario", "catálogo", "existencias", "acervo", "disponible", "conteo" para check_stock
- "poner", "establecer", "cambiar a" para update_quantity

IMPORTANTE: Para preguntas generales sobre el inventario completo (sin mencionar un ingrediente específico), 
siempre usa ingredient_name: "todo" y action: "check_stock".

Sé flexible con unidades (convierte g a kg cuando sea apropiado, ml a litros, etc.).
También acepta sinónimos comunes de ingredientes.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=200
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
                ingredient_name=parsed_data.get("ingredient_name", ""),
                quantity=parsed_data.get("quantity"),
                unit=parsed_data.get("unit"),
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