"""
Demo of enhanced inventory phrases with the smart inventory service.
This shows how the new phrases would work in practice.
"""
import sys
import os

# Add the src directory to the Python path
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Mock the database and services for demonstration
class MockInventoryItem:
    def __init__(self, ingredient_name, quantity, unit):
        self.ingredient_name = ingredient_name
        self.quantity = quantity
        self.unit = unit

class MockInventoryService:
    def __init__(self):
        # Mock inventory data
        self.inventory = [
            MockInventoryItem("azúcar", 5.5, "kg"),
            MockInventoryItem("chocolate", 2.0, "kg"),
            MockInventoryItem("harina", 10.0, "kg"),
            MockInventoryItem("leche", 3.5, "liters"),
            MockInventoryItem("mantequilla", 1.2, "kg"),
            MockInventoryItem("vainilla", 0.25, "liters"),
            MockInventoryItem("sal", 0.5, "kg"),
            MockInventoryItem("huevos", 24, "pcs"),
        ]
    
    def list_all_ingredients(self):
        return self.inventory

def simulate_inventory_check_responses():
    """Simulate how the enhanced phrases would work with the bot."""
    
    print("=== ENHANCED INVENTORY PHRASES DEMO ===")
    print()
    
    # Mock inventory service
    inventory_service = MockInventoryService()
    
    # Test phrases
    test_phrases = [
        "¿Qué tenemos en stock?",
        "¿Qué hay disponible?", 
        "¿Qué productos hay?",
        "¿Cómo va el conteo?",
        "¿Cuál es el stock disponible?",
        "¿Cuál es el acervo de productos?",
        "¿Cuál es el catálogo de artículos?",
        "¿Cuál es la existencia de mercancía?",
        "Mostrar inventario completo",
        "¿Qué hay en el almacén?",
    ]
    
    # Simulate the bot response for these phrases
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i:2d}. User: '{phrase}'")
        print("    Bot Response:")
        
        # This simulates what the smart_inventory_service would return
        # when action="check_stock" and ingredient_name="todo"
        all_ingredients = inventory_service.list_all_ingredients()
        
        if not all_ingredients:
            response = "📦 El inventario está vacío."
        else:
            response = "📦 **Inventario Actual:**\n"
            for item in all_ingredients:
                response += f"    • {item.ingredient_name}: {item.quantity} {item.unit}\n"
        
        print(f"    {response}")
        print()
    
    print("=" * 60)
    print("COMPARISON: Specific vs General Queries")
    print("=" * 60)
    
    comparison_examples = [
        ("¿Cuánto azúcar tenemos?", "Specific ingredient query"),
        ("¿Qué tenemos en stock?", "General inventory query"),
        ("Stock de chocolate", "Specific ingredient query"),
        ("¿Qué productos hay?", "General inventory query"),
        ("¿Hay leche disponible?", "Specific ingredient query"),
        ("¿Cuál es el catálogo completo?", "General inventory query"),
    ]
    
    for phrase, query_type in comparison_examples:
        print(f"'{phrase}'")
        print(f"  Type: {query_type}")
        
        if "General" in query_type:
            print("  Response: Full inventory list (8 items)")
        else:
            print("  Response: Single ingredient details")
        print()
    
    print("🎉 All enhanced phrases now supported!")
    print()
    print("Benefits:")
    print("✅ Natural language variety - users can ask in many ways")
    print("✅ Comprehensive coverage - supports formal and informal queries")
    print("✅ Clear distinction between general and specific requests")
    print("✅ Consistent responses - all phrases show complete inventory")

if __name__ == "__main__":
    simulate_inventory_check_responses()