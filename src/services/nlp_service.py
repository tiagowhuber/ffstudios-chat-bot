"""
Natural Language Processing service using OpenAI GPT-4o-mini.
"""
import json
import logging
from typing import Dict, Any, Optional
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

Acepta variaciones como:
- "recibimos", "llegó", "entró", "compramos" para add_quantity
- "usé", "gasté", "consumí", "utilicé" para remove_quantity
- "¿cuánto hay de...?", "stock de...", "cantidad de..." para check_stock
- "poner", "establecer", "cambiar a" para update_quantity

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