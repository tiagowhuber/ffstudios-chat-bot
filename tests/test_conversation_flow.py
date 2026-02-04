"""
Test conversation flow with missing fields collection.
"""
import pytest
from src.services.smart_inventory_service import SmartInventoryService
from src.bot.conversation_state import PendingAction, check_missing_fields, format_missing_fields_prompt
from src.bot.config import Config


@pytest.fixture
def smart_inventory():
    """Create SmartInventoryService instance."""
    config = Config()
    if not config.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not configured")
    return SmartInventoryService(config.OPENAI_API_KEY)


def test_missing_fields_detection():
    """Test detection of missing required fields."""
    # Purchase with missing provider and payment_method
    action_data = {
        'ingredient_name': 'vino blanco',
        'quantity': 1.0,
        'unit': 'litro',
        'cost': 1790.0,
        'provider': None,
        'payment_method': None
    }
    
    missing = check_missing_fields('register_purchase', action_data)
    assert 'provider' in missing
    assert 'payment_method' in missing
    assert len(missing) == 2


def test_missing_fields_prompt():
    """Test generation of user-friendly prompts for missing fields."""
    # Test single missing field
    prompt = format_missing_fields_prompt(['provider'])
    assert 'proveedor' in prompt.lower()
    
    # Test two missing fields
    prompt = format_missing_fields_prompt(['provider', 'payment_method'])
    assert 'proveedor' in prompt.lower()
    assert 'medio de pago' in prompt.lower()
    assert ' y ' in prompt
    
    # Test three missing fields
    prompt = format_missing_fields_prompt(['ingredient_name', 'cost', 'provider'])
    assert 'nombre del producto' in prompt.lower()
    assert 'precio' in prompt.lower()
    assert 'proveedor' in prompt.lower()


def test_pending_action_merge():
    """Test merging supplemental data into pending action."""
    pending = PendingAction(
        action='register_purchase',
        original_message='compre un vino blanco 1 litro en $1790',
        ingredient_name='vino blanco',
        quantity=1.0,
        unit='litro',
        cost=1790.0,
        missing_fields=['provider', 'payment_method']
    )
    
    # Merge supplement
    supplement = {
        'provider': 'Líder',
        'payment_method': 'Débito'
    }
    
    pending.merge_with_supplement(supplement)
    
    assert pending.provider == 'Líder'
    assert pending.payment_method == 'Débito'
    assert 'provider' not in pending.missing_fields
    assert 'payment_method' not in pending.missing_fields


def test_conversation_flow_incomplete_purchase(smart_inventory):
    """Test conversation flow with incomplete purchase information."""
    # First message - incomplete purchase
    success, response, pending = smart_inventory.process_natural_language_command(
        "compre un vino blanco 1 litro en $1790"
    )
    
    # Should ask for missing fields
    assert not success or pending is not None
    if pending:
        assert pending.action == 'register_purchase'
        assert 'provider' in pending.missing_fields or 'payment_method' in pending.missing_fields
        assert 'proveedor' in response.lower() or 'medio de pago' in response.lower()


def test_conversation_flow_supplemental_message(smart_inventory):
    """Test processing supplemental message."""
    # Create a pending action
    pending = PendingAction(
        action='register_purchase',
        original_message='compre un vino blanco 1 litro en $1790',
        ingredient_name='vino blanco',
        quantity=1.0,
        unit='litro',
        cost=1790.0,
        missing_fields=['provider', 'payment_method']
    )
    
    # Second message - provide missing info
    success, response, new_pending = smart_inventory.process_natural_language_command(
        "lider, débito",
        pending_action=pending
    )
    
    # Should complete the action or have fewer missing fields
    if new_pending:
        # Still missing some fields
        assert len(new_pending.missing_fields) < len(pending.missing_fields)
    else:
        # Action completed successfully
        assert success
        assert 'registrada' in response.lower() or 'éxito' in response.lower()


def test_parse_supplemental_provider_payment(smart_inventory):
    """Test parsing supplemental message with provider and payment method."""
    supplement = smart_inventory.parse_supplemental_message(
        "lider, débito",
        ['provider', 'payment_method']
    )
    
    assert supplement.get('provider') is not None
    assert supplement.get('payment_method') is not None


def test_parse_supplemental_cost_provider(smart_inventory):
    """Test parsing supplemental message with cost and provider."""
    supplement = smart_inventory.parse_supplemental_message(
        "$2500 en santa isabel",
        ['cost', 'provider']
    )
    
    assert supplement.get('cost') is not None
    assert supplement.get('provider') is not None
    assert supplement['cost'] > 0


def test_expense_missing_fields():
    """Test missing fields detection for expense."""
    action_data = {
        'expense_category': 'luz',
        'cost': 35000.0,
        'provider': None,
        'payment_method': 'transferencia'
    }
    
    missing = check_missing_fields('register_expense', action_data)
    assert 'provider' in missing
    assert 'payment_method' not in missing


def test_usage_complete_fields():
    """Test usage with all required fields."""
    action_data = {
        'ingredient_name': 'harina',
        'quantity': 1.0,
        'unit': 'kg'
    }
    
    missing = check_missing_fields('register_usage', action_data)
    assert len(missing) == 0  # All required fields present


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
