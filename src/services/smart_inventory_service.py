"""
Smart inventory service that handles natural language commands.
"""
import logging
from typing import Optional, Tuple, List

from .inventory_service import InventoryService
from .nlp_service import NLPService, InventoryAction, MultipleInventoryActions

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
            # First check if the message might contain multiple ingredients
            if self._contains_multiple_ingredients(message):
                return self._process_multiple_ingredients_command(message)
            
            # Parse the message using NLP for single ingredient
            action = self.nlp_service.parse_inventory_message(message)
            
            if action.confidence < 0.6:
                return False, f"No estoy seguro de lo que quisiste decir con '{message}'. ¿Podrías ser más específico?"
            
            if action.action == "unknown" or not action.ingredient_name:
                return False, f"No pude entender qué acción de inventario quieres realizar. Intenta frases como 'llegaron 2 kg de chocolate' o 'usé 500g de harina'."
            
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
                return False, f"Entiendo que quieres hacer algo con {action.ingredient_name}, pero no estoy seguro de qué acción tomar."
                
        except Exception as e:
            logger.error(f"Error processing natural language command '{message}': {e}")
            return False, f"Lo siento, encontré un error al procesar tu solicitud: {str(e)}"
    
    def _contains_multiple_ingredients(self, message: str) -> bool:
        """
        Check if a message likely contains multiple ingredients.
        
        Args:
            message: User's message
            
        Returns:
            True if the message likely contains multiple ingredients
        """
        message_lower = message.lower()
        
        # Look for patterns that suggest multiple ingredients
        multiple_indicators = [
            ' y ', ' e ', ',', 
            'de harina', 'de azucar', 'de chocolate', 'de leche', 'de sal',
            'de mantequilla', 'de vainilla', 'de huevos', 'de café'
        ]
        
        # Count how many different ingredients might be mentioned
        ingredient_count = 0
        for indicator in ['de ']:
            ingredient_count += message_lower.count(indicator)
        
        # If we have multiple "de" (indicating multiple ingredients) or common conjunctions
        return ingredient_count > 1 or any(ind in message_lower for ind in [' y ', ' e ', ','])
    
    def _process_multiple_ingredients_command(self, message: str) -> Tuple[bool, str]:
        """
        Process a natural language command with multiple ingredients.
        
        Args:
            message: User's natural language message
            
        Returns:
            Tuple of (success: bool, response_message: str)
        """
        try:
            # Parse the message for multiple ingredients
            multiple_actions = self.nlp_service.parse_multiple_ingredients_message(message)
            
            if multiple_actions.overall_confidence < 0.6:
                return False, f"No estoy seguro de lo que quisiste decir con '{message}'. ¿Podrías ser más específico?"
            
            if not multiple_actions.actions:
                return False, f"No pude identificar ningún ingrediente en tu mensaje."
            
            # Process each action
            results = []
            success_count = 0
            
            for action in multiple_actions.actions:
                if action.action == "unknown" or not action.ingredient_name:
                    results.append(f"❌ No pude entender la acción para '{action.ingredient_name}'")
                    continue
                
                # Normalize units if quantity is provided
                if action.quantity and action.unit:
                    normalized_quantity, normalized_unit = self.nlp_service.normalize_unit(action.unit, action.quantity)
                else:
                    normalized_quantity, normalized_unit = action.quantity, action.unit
                
                # Execute the appropriate action
                try:
                    if action.action == "add_quantity":
                        success, result = self._handle_add_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
                    elif action.action == "add_new":
                        success, result = self._handle_add_new(action.ingredient_name, normalized_quantity, normalized_unit)
                    elif action.action == "remove_quantity":
                        success, result = self._handle_remove_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
                    elif action.action == "update_quantity":
                        success, result = self._handle_update_quantity(action.ingredient_name, normalized_quantity, normalized_unit)
                    elif action.action == "check_stock":
                        success, result = self._handle_check_stock(action.ingredient_name)
                    else:
                        success, result = False, f"❌ Acción desconocida para {action.ingredient_name}"
                    
                    if success:
                        success_count += 1
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing action for {action.ingredient_name}: {e}")
                    results.append(f"❌ Error procesando {action.ingredient_name}: {str(e)}")
            
            # Compile final response
            total_actions = len(multiple_actions.actions)
            
            if success_count == total_actions:
                final_response = f"✅ Procesados exitosamente {success_count} ingredientes:\n\n" + "\n".join(results)
                return True, final_response
            elif success_count > 0:
                final_response = f"⚠️ Procesados {success_count} de {total_actions} ingredientes:\n\n" + "\n".join(results)
                return True, final_response
            else:
                final_response = f"❌ No se pudo procesar ningún ingrediente:\n\n" + "\n".join(results)
                return False, final_response
                
        except Exception as e:
            logger.error(f"Error processing multiple ingredients command '{message}': {e}")
            return False, f"Lo siento, encontré un error al procesar múltiples ingredientes: {str(e)}"
    
    def _handle_add_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle adding quantity to existing ingredient."""
        try:
            # Check if ingredient exists (exact match first)
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if existing:
                # Add to existing stock
                updated = self.inventory_service.add_quantity(existing.id, quantity)
                if updated:
                    return True, f"✅ Se agregaron {quantity} {unit} de {ingredient_name}.\nNuevo total: {updated.quantity} {updated.unit}"
                else:
                    return False, f"Error al agregar {quantity} {unit} de {ingredient_name}."
            else:
                # Try fuzzy matching for typos
                fuzzy_match = self.inventory_service.get_ingredient_by_name_fuzzy(ingredient_name, min_similarity=0.7)
                
                if fuzzy_match:
                    matched_item, similarity = fuzzy_match
                    # Ask for confirmation if it's a potential typo
                    if similarity < 0.9:  # Likely a typo
                        return True, f"🤔 ¿Te refieres a '{matched_item.ingredient_name}'? (encontré una similitud del {similarity:.0%})\n\nSi es correcto, puedes confirmar diciendo 'sí, agregar {quantity} {unit} de {matched_item.ingredient_name}'"
                    else:
                        # High similarity, proceed with the correction
                        updated = self.inventory_service.add_quantity(matched_item.id, quantity)
                        if updated:
                            return True, f"✅ Se agregaron {quantity} {unit} de {matched_item.ingredient_name} (corregido de '{ingredient_name}').\nNuevo total: {updated.quantity} {updated.unit}"
                        else:
                            return False, f"Error al agregar {quantity} {unit} de {matched_item.ingredient_name}."
                else:
                    # Create new ingredient if no similar match found
                    new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
                    if new_item:
                        return True, f"✅ Se agregó nuevo ingrediente: {ingredient_name} ({quantity} {unit})"
                    else:
                        return False, f"Error al agregar nuevo ingrediente {ingredient_name}."
                    
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_add_quantity: {e}")
            return False, f"❌ Error de base de datos al agregar {ingredient_name}."
    
    def _handle_add_new(self, ingredient_name: str, quantity: Optional[float], unit: Optional[str]) -> Tuple[bool, str]:
        """Handle adding a completely new ingredient."""
        try:
            if quantity is None:
                quantity = 0.0
            if unit is None:
                unit = "pcs"
                
            new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
            if new_item:
                return True, f"✅ Se agregó nuevo ingrediente: {ingredient_name} ({quantity} {unit})"
            else:
                return False, f"Error al agregar nuevo ingrediente {ingredient_name}."
                
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_add_new: {e}")
            return False, f"❌ Error de base de datos al agregar {ingredient_name}."
    
    def _handle_remove_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle removing quantity from existing ingredient."""
        try:
            # Try exact match first
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if not existing:
                # Try fuzzy matching for typos
                fuzzy_match = self.inventory_service.get_ingredient_by_name_fuzzy(ingredient_name, min_similarity=0.7)
                
                if fuzzy_match:
                    matched_item, similarity = fuzzy_match
                    if similarity < 0.9:  # Likely a typo, ask for confirmation
                        return True, f"🤔 ¿Te refieres a '{matched_item.ingredient_name}'? (encontré una similitud del {similarity:.0%})\n\nSi es correcto, puedes confirmar diciendo 'sí, quitar {quantity} {unit} de {matched_item.ingredient_name}'"
                    else:
                        existing = matched_item  # Use the corrected ingredient
                else:
                    return False, f"❌ {ingredient_name} no se encontró en el inventario."
            
            # Proceed with removal using the found ingredient (exact or fuzzy match)
            updated = self.inventory_service.remove_quantity(existing.id, quantity)
            if updated:
                correction_note = f" (corregido de '{ingredient_name}')" if existing.ingredient_name != ingredient_name else ""
                return True, f"✅ Se quitaron {quantity} {unit} de {existing.ingredient_name}{correction_note}.\nRestante: {updated.quantity} {updated.unit}"
            else:
                return False, f"Error al quitar {quantity} {unit} de {existing.ingredient_name}."
                
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_remove_quantity: {e}")
            return False, f"❌ Error de base de datos al quitar {ingredient_name}."
    
    def _handle_update_quantity(self, ingredient_name: str, quantity: float, unit: str) -> Tuple[bool, str]:
        """Handle setting a specific quantity for an ingredient."""
        try:
            # Try exact match first
            existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
            
            if existing:
                updated = self.inventory_service.update_quantity(existing.id, quantity)
                if updated:
                    return True, f"✅ Se estableció {ingredient_name} a {quantity} {unit}"
                else:
                    return False, f"Error al actualizar la cantidad de {ingredient_name}."
            else:
                # Try fuzzy matching for typos
                fuzzy_match = self.inventory_service.get_ingredient_by_name_fuzzy(ingredient_name, min_similarity=0.7)
                
                if fuzzy_match:
                    matched_item, similarity = fuzzy_match
                    if similarity < 0.9:  # Likely a typo, ask for confirmation
                        return True, f"🤔 ¿Te refieres a '{matched_item.ingredient_name}'? (encontré una similitud del {similarity:.0%})\n\nSi es correcto, puedes confirmar diciendo 'sí, establecer {matched_item.ingredient_name} a {quantity} {unit}'"
                    else:
                        # High similarity, proceed with the correction
                        updated = self.inventory_service.update_quantity(matched_item.id, quantity)
                        if updated:
                            return True, f"✅ Se estableció {matched_item.ingredient_name} (corregido de '{ingredient_name}') a {quantity} {unit}"
                        else:
                            return False, f"Error al actualizar la cantidad de {matched_item.ingredient_name}."
                else:
                    # Create new ingredient with specified quantity
                    new_item = self.inventory_service.add_ingredient(ingredient_name, quantity, unit)
                    if new_item:
                        return True, f"✅ Se agregó nuevo ingrediente: {ingredient_name} ({quantity} {unit})"
                    else:
                        return False, f"Error al agregar {ingredient_name}."
                    
        except ValueError as e:
            return False, f"❌ Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in _handle_update_quantity: {e}")
            return False, f"❌ Error de base de datos al actualizar {ingredient_name}."
    
    def _handle_check_stock(self, ingredient_name: str) -> Tuple[bool, str]:
        """Handle checking stock levels for an ingredient."""
        try:
            if ingredient_name.lower() in ['todo', 'todos', 'all', 'everything', 'inventario', 'inventory']:
                # Show all ingredients
                all_ingredients = self.inventory_service.list_all_ingredients()
                if not all_ingredients:
                    return True, "📦 El inventario está vacío."
                
                response = "📦 **Inventario Actual:**\n"
                for item in all_ingredients:
                    response += f"• {item.ingredient_name}: {item.quantity} {item.unit}\n"
                
                return True, response
            else:
                # Show specific ingredient - try exact match first
                existing = self.inventory_service.get_ingredient_by_name(ingredient_name)
                
                if existing:
                    return True, f"📦 {existing.ingredient_name}: {existing.quantity} {existing.unit}"
                else:
                    # Try fuzzy matching for typos
                    fuzzy_match = self.inventory_service.get_ingredient_by_name_fuzzy(ingredient_name, min_similarity=0.7)
                    
                    if fuzzy_match:
                        matched_item, similarity = fuzzy_match
                        if similarity < 0.9:  # Likely a typo, show suggestion
                            return True, f"📦 {ingredient_name} no se encontró exactamente.\n🤔 ¿Te refieres a '{matched_item.ingredient_name}'? (similitud: {similarity:.0%})\n📦 {matched_item.ingredient_name}: {matched_item.quantity} {matched_item.unit}"
                        else:
                            # High similarity, show the result with correction note
                            return True, f"📦 {matched_item.ingredient_name} (corregido de '{ingredient_name}'): {matched_item.quantity} {matched_item.unit}"
                    else:
                        return True, f"📦 {ingredient_name} no se encontró en el inventario."
                    
        except Exception as e:
            logger.error(f"Error in _handle_check_stock: {e}")
            return False, f"❌ Error de base de datos al verificar {ingredient_name}."