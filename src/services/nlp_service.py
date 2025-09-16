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
You are an AI assistant that parses inventory management messages. 
Analyze the user's message and extract inventory actions.

Return a JSON object with these fields:
- action: one of "add_new", "add_quantity", "remove_quantity", "update_quantity", "check_stock", "unknown"
- ingredient_name: the name of the ingredient (string)
- quantity: the numeric quantity (number, null if not specified)
- unit: the unit of measurement (string, null if not specified)
- confidence: confidence score from 0.0 to 1.0

Action definitions:
- "add_new": User wants to add a completely new ingredient
- "add_quantity": User wants to add to existing stock (arrivals, restocking)
- "remove_quantity": User wants to remove from stock (usage, consumption)
- "update_quantity": User wants to set a specific total quantity
- "check_stock": User wants to check current stock levels
- "unknown": Cannot determine the action clearly

Examples:
"2 kg of chocolate arrived" → {"action": "add_quantity", "ingredient_name": "chocolate", "quantity": 2.0, "unit": "kg", "confidence": 0.95}
"used 500g of flour" → {"action": "remove_quantity", "ingredient_name": "flour", "quantity": 0.5, "unit": "kg", "confidence": 0.9}
"add new ingredient: vanilla extract 100ml" → {"action": "add_new", "ingredient_name": "vanilla extract", "quantity": 100.0, "unit": "ml", "confidence": 0.9}
"how much sugar do we have?" → {"action": "check_stock", "ingredient_name": "sugar", "quantity": null, "unit": null, "confidence": 0.85}
"set milk to 2 liters" → {"action": "update_quantity", "ingredient_name": "milk", "quantity": 2.0, "unit": "liters", "confidence": 0.9}

Be flexible with units (convert g to kg when appropriate, ml to liters, etc.).
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
        if unit in ['g', 'gram', 'grams']:
            return quantity / 1000, "kg"
        elif unit in ['kg', 'kilogram', 'kilograms', 'kilo', 'kilos']:
            return quantity, "kg"
        
        # Volume conversions to liters
        elif unit in ['ml', 'milliliter', 'milliliters']:
            return quantity / 1000, "liters"
        elif unit in ['l', 'liter', 'liters', 'litre', 'litres']:
            return quantity, "liters"
        
        # Count units
        elif unit in ['pcs', 'pieces', 'piece', 'pc', 'units', 'unit']:
            return quantity, "pcs"
        
        # Default: return as-is
        else:
            return quantity, unit