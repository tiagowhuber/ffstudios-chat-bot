import pytest
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
from src.services.finance_service import FinanceService
from src.services.inventory_service import InventoryService
from src.database.models import Gasto, Inventario

@contextmanager
def mock_session_scope(session):
    yield session

def test_purchase_triggers_inventory(db_session, seed_data):
    """
    Test that registering a purchase automatically updates inventory via trigger.
    """
    # Patch the get_db_session in finance_service to use our test session
    # We need to target where it is IMPORTED
    with patch('src.services.finance_service.get_db_session', side_effect=lambda: mock_session_scope(db_session)):
        service = FinanceService()
        
        # 1. Register Purchase: 10kg Sugar
        gasto = service.register_purchase(
            product_name="Azúcar Test",
            quantity=10.0,
            unit="kg",
            cost=5000,
            provider_name="Super Test",
            payment_method_name="Efectivo"
        )
        
        assert gasto is not None
        assert gasto.monto == 5000
    
    # 2. Verify Inventory (Trigger Check)
    # Note: Since the test runs in a transaction that hasn't committed to the REAL DB,
    # the Postgres trigger only fires if the DB supports nested transactions or if we are lucky.
    # Actually, standard SQLALchemy tests with rollback rely on the fact that within the transaction
    # the state is consistent. Triggers fire within the transaction.
    
    # We need to query using the SAME session
    product_id = gasto.producto_id
    inventory = db_session.query(Inventario).filter_by(producto_id=product_id).first()
    
    assert inventory is not None, "Inventory record should be created/updated by trigger"
    assert inventory.cantidad_actual == 10.0, "Stock should be 10.0"

def test_expense_registration(db_session, seed_data):
    """Test registering a fixed expense."""
    with patch('src.services.finance_service.get_db_session', side_effect=lambda: mock_session_scope(db_session)):
        service = FinanceService()
        
        gasto = service.register_expense(
            category_name="Electricidad",
            cost=25000,
            provider_name="CGE",
            payment_method_name="Transferencia"
        )
        
        assert gasto is not None
        assert gasto.tipo_gasto.nombre == "Fijo"
        assert gasto.categoria.nombre == "Electricidad"

def test_usage_deducts_inventory(db_session, seed_data):
    """Test that usage reduces inventory."""
    # 1. Setup: Add stock first
    with patch('src.services.finance_service.get_db_session', side_effect=lambda: mock_session_scope(db_session)):
        finance = FinanceService()
        finance.register_purchase("Harina Test", 5.0, "kg", 1000, "Prov", "Efectivo")
    
    # 2. Use Stock
    with patch('src.services.inventory_service.get_db_session', side_effect=lambda: mock_session_scope(db_session)):
        inv_service = InventoryService()
        inv = inv_service.register_usage("Harina Test", 2.0, "Cake")
        
        assert inv is not None
        assert inv.cantidad_actual == 3.0 # 5 - 2
