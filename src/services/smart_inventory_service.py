"""
Smart inventory service that handles natural language commands.
"""
import logging
from typing import Optional, Tuple

from .inventory_service import InventoryService
from .nlp_service import NLPService, InventoryAction

logger = logging.getLogger(__name__)

class SmartInventoryService:
    """Service that combines NLP with inventory management."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the smart inventory service."""
        self.nlp_service = NLPService(openai_api_key)
        self.inventory_service = InventoryService()
    
    def process_natural_language_command(self, message: str) -> Tuple[bool, str]:
        """
        Process a natural language inventory command.
        
        Args:
            message: User's natural language message
            
        Returns:
            Tuple of (success: bool, response_message: str)
        """
        try:
            # Parse the message using NLP
            action = self.nlp_service.parse_inventory_message(message)
            
            if action.confidence < 0.6:
                return False, f"I'm not sure what you meant by '{message}'. Could you please be more specific?"
            
            if action.action == "unknown" or not action.ingredient_name:
                return False, f"I couldn't understand what inventory action you want to perform. Try phrases like '2 kg of chocolate arrived' or 'used 500g of flour'."
            
            # Normalize units if quantity is provided
            if action.quantity and action.unit:
                normalized_quantity, normalized_unit = self.nlp_service.normalize_unit(action.unit, action.quantity)
            else:
                normalized_quantity, normalized_unit = action.quantity, action.unit
            
            # Execute the appropriate action
            if action.action == "add_quantity":
                return self._handle_add_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
            
            elif action.action == "add_new":
                return self._handle_add_new(action.ingredient_name, normalized_quantity, normalized_unit)
            
            elif action.action == "remove_quantity":
                return self._handle_remove_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
            
            elif action.action == "update_quantity":
                return self._handle_update_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
            
            elif action.action == "check_stock":
                return self._handle_check_stock(action.ingredient_name)
            
            else:
                return False, f"I understood you want to do something with {action.ingredient_name}, but I'm not sure what action to take."
                
        except Exception as e:
            logger.error(f"Error processing natural language command '{message}': {e}")
            return False, f"Sorry, I encountered an error processing your request: {str(e)}"
    
    def _handle_add_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle adding quantity to existing ingredient."""
        try:
            # Check if ingredient exists
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if existing:
                # Add to existing stock
                updated = self.inventory_service.add_quantity(existing.id, quantity)
                if updated:
                    return True, f"✅ Added {quantity} {unit} of {ingredient_name}.\nNew total: {updated.quantity} {updated.unit}"
                else:
                    return False, f"Failed to add {quantity} {unit} of {ingredient_name}."
            else:
                # Create new ingredient
                new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
                if new_item:
                    return True, f"✅ Added new ingredient: {ingredient_name} ({quantity} {unit})"
                else:
                    return False, f"Failed to add new ingredient {ingredient_name}."
                    
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_add_quantity: {e}")
            return False, f"❌ Database error while adding {ingredient_name}."
    
    def _handle_add_new(self, ingredient_name: str, quantity: Optional[float], unit: Optional[str]) -> Tuple[bool, str]:
        """Handle adding a completely new ingredient."""
        try:
            if quantity is None:
                quantity = 0.0
            if unit is None:
                unit = "pcs"
                
            new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
            if new_item:
                return True, f"✅ Added new ingredient: {ingredient_name} ({quantity} {unit})"
            else:
                return False, f"Failed to add new ingredient {ingredient_name}."
                
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_add_new: {e}")
            return False, f"❌ Database error while adding {ingredient_name}."
    
    def _handle_remove_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle removing quantity from existing ingredient."""
        try:
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if not existing:
                return False, f"❌ {ingredient_name} not found in inventory."
            
            updated = self.inventory_service.remove_quantity(existing.id, quantity)
            if updated:
                return True, f"✅ Removed {quantity} {unit} of {ingredient_name}.\nRemaining: {updated.quantity} {updated.unit}"
            else:
                return False, f"Failed to remove {quantity} {unit} of {ingredient_name}."
                
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_remove_quantity: {e}")
            return False, f"❌ Database error while removing {ingredient_name}."
    
    def _handle_update_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle setting a specific quantity for an ingredient."""
        try:
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if existing:
                updated = self.inventory_service.update_quantity(existing.id, quantity)
                if updated:
                    return True, f"✅ Set {ingredient_name} to {quantity} {unit}"
                else:
                    return False, f"Failed to update {ingredient_name} quantity."
            else:
                # Create new ingredient with specified quantity
                new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
                if new_item:
                    return True, f"✅ Added new ingredient: {ingredient_name} ({quantity} {unit})"
                else:
                    return False, f"Failed to add {ingredient_name}."
                    
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_update_quantity: {e}")
            return False, f"❌ Database error while updating {ingredient_name}."
    
    def _handle_check_stock(self, ingredient_name: str) -> Tuple[bool, str]:
        """Handle checking stock levels for an ingredient."""
        try:
            if ingredient_name.lower() in ['all', 'everything', 'inventory']:
                # Show all ingredients
                all_ingredients = self.inventory_service.list_all_ingredients()
                if not all_ingredients:
                    return True, "📦 Inventory is empty."
                
                response = "📦 **Current Inventory:**\n"
                for item in all_ingredients:
                    response += f"• {item.ingredient_name}: {item.quantity} {item.unit}\n"
                
                return True, response
            else:
                # Show specific ingredient
                existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
                
                if existing:
                    return True, f"📦 {existing.ingredient_name}: {existing.quantity} {existing.unit}"
                else:
                    return True, f"📦 {ingredient_name} not found in inventory."
                    
        except Exception as e:
            logger.error(f"Error in _handle_check_stock: {e}")
            return False, f"❌ Database error while checking {ingredient_name}."