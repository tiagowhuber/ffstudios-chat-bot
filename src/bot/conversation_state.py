"""
Conversation state management for multi-turn interactions.
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation state types."""
    IDLE = "idle"
    AWAITING_PURCHASE_DETAILS = "awaiting_purchase_details"
    AWAITING_EXPENSE_DETAILS = "awaiting_expense_details"
    AWAITING_USAGE_DETAILS = "awaiting_usage_details"


@dataclass
class PendingAction:
    """Stores a pending action waiting for additional information."""
    action: str  # 'register_purchase', 'register_expense', 'register_usage'
    original_message: str  # The original user message
    
    # Common fields
    ingredient_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    provider: Optional[str] = None
    payment_method: Optional[str] = None
    expense_category: Optional[str] = None
    reason: Optional[str] = None
    
    # Missing fields that need to be collected
    missing_fields: list = None
    
    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PendingAction':
        """Create from dictionary."""
        return cls(**data)
    
    def merge_with_supplement(self, supplement_data: Dict[str, Any]) -> None:
        """
        Merge supplementary data into this pending action.
        
        Args:
            supplement_data: Dictionary with additional fields collected from user
        """
        for field, value in supplement_data.items():
            if value is not None and hasattr(self, field):
                setattr(self, field, value)
                if field in self.missing_fields:
                    self.missing_fields.remove(field)


class ConversationStateManager:
    """Manages conversation state for users."""
    
    @staticmethod
    def get_state(context) -> ConversationState:
        """Get current conversation state."""
        return context.user_data.get('conversation_state', ConversationState.IDLE)
    
    @staticmethod
    def set_state(context, state: ConversationState) -> None:
        """Set conversation state."""
        context.user_data['conversation_state'] = state
        logger.info(f"Conversation state set to: {state.value}")
    
    @staticmethod
    def set_pending_action(context, pending_action: PendingAction) -> None:
        """Store a pending action."""
        context.user_data['pending_action'] = pending_action.to_dict()
        logger.info(f"Pending action stored: {pending_action.action} with missing fields: {pending_action.missing_fields}")
    
    @staticmethod
    def get_pending_action(context) -> Optional[PendingAction]:
        """Retrieve the pending action."""
        pending_data = context.user_data.get('pending_action')
        if pending_data:
            return PendingAction.from_dict(pending_data)
        return None
    
    @staticmethod
    def clear_pending_action(context) -> None:
        """Clear the pending action and reset state."""
        context.user_data.pop('pending_action', None)
        context.user_data['conversation_state'] = ConversationState.IDLE
        logger.info("Pending action cleared, state reset to IDLE")
    
    @staticmethod
    def has_pending_action(context) -> bool:
        """Check if there's a pending action."""
        return 'pending_action' in context.user_data


def get_required_fields(action: str) -> list:
    """
    Get the list of required fields for a given action.
    
    Args:
        action: The action type (register_purchase, register_expense, register_usage)
        
    Returns:
        List of required field names
    """
    required_fields_map = {
        'register_purchase': [
            'ingredient_name',
            'quantity',
            'unit',
            'cost',
            'provider',
            'payment_method'
        ],
        'register_expense': [
            'expense_category',
            'cost',
            'provider',
            'payment_method'
        ],
        'register_usage': [
            'ingredient_name',
            'quantity'
        ]
    }
    
    return required_fields_map.get(action, [])


def check_missing_fields(action: str, parsed_data: Dict[str, Any]) -> list:
    """
    Check which required fields are missing from the parsed data.
    
    Args:
        action: The action type
        parsed_data: Dictionary of parsed fields
        
    Returns:
        List of missing field names
    """
    required = get_required_fields(action)
    missing = []
    
    for field in required:
        value = parsed_data.get(field)
        # Consider None, empty string, or 0 cost as missing
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
        elif field == 'cost' and value == 0.0:
            missing.append(field)
    
    return missing


def format_missing_fields_prompt(missing_fields: list) -> str:
    """
    Create a user-friendly prompt asking for missing fields.
    
    Args:
        missing_fields: List of missing field names
        
    Returns:
        User-friendly prompt in Spanish
    """
    field_translations = {
        'ingredient_name': 'nombre del producto',
        'quantity': 'cantidad',
        'unit': 'unidad de medida',
        'cost': 'precio',
        'provider': 'proveedor',
        'payment_method': 'medio de pago',
        'expense_category': 'categoría del gasto',
        'reason': 'motivo'
    }
    
    translated = [field_translations.get(f, f) for f in missing_fields]
    
    if len(translated) == 1:
        return f"Por favor indícame: {translated[0]}"
    elif len(translated) == 2:
        return f"Por favor indícame: {translated[0]} y {translated[1]}"
    else:
        last = translated[-1]
        others = ', '.join(translated[:-1])
        return f"Por favor indícame: {others} y {last}"
