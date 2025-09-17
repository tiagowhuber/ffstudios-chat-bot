#!/usr/bin/env python3
"""
Test script to verify Spanish language functionality in the chatbot.
This script tests the NLP service and smart inventory service with Spanish inputs.
"""

import os
import sys
from typing import Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.nlp_service import NLPService
from src.services.smart_inventory_service import SmartInventoryService

def test_nlp_spanish_parsing():
    """Test if the NLP service correctly parses Spanish messages."""
    
    # Note: This requires a valid OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment variables")
        print("⚠️  Set OPENAI_API_KEY to test the NLP functionality")
        return False
    
    print("🧠 Probando análisis de lenguaje natural en español...")
    
    nlp = NLPService(api_key)
    
    # Test cases in Spanish
    test_cases = [
        ("llegaron 2 kg de chocolate", "add_quantity", "chocolate", 2.0, "kg"),
        ("usé 500g de harina", "remove_quantity", "harina", 500.0, "g"),
        ("¿cuánto azúcar tenemos?", "check_stock", "azúcar", None, None),
        ("agregar nuevo ingrediente: vainilla 100ml", "add_new", "vainilla", 100.0, "ml"),
        ("establecer leche a 2 litros", "update_quantity", "leche", 2.0, "litros"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, (message, expected_action, expected_ingredient, expected_quantity, expected_unit) in enumerate(test_cases, 1):
        print(f"\n📝 Prueba {i}: '{message}'")
        
        try:
            result = nlp.parse_inventory_message(message)
            
            print(f"   Acción: {result.action} (esperado: {expected_action})")
            print(f"   Ingrediente: {result.ingredient_name} (esperado: {expected_ingredient})")
            print(f"   Cantidad: {result.quantity} (esperado: {expected_quantity})")
            print(f"   Unidad: {result.unit} (esperado: {expected_unit})")
            print(f"   Confianza: {result.confidence}")
            
            # Check if the main parsing is correct
            if (result.action == expected_action and 
                expected_ingredient.lower() in result.ingredient_name.lower() and
                result.confidence > 0.6):
                print("   ✅ ¡Correcto!")
                success_count += 1
            else:
                print("   ❌ Fallo en el análisis")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Resultados: {success_count}/{total_tests} pruebas exitosas")
    return success_count == total_tests

def test_basic_responses():
    """Test basic response functions with Spanish keywords."""
    print("\n💬 Probando respuestas básicas en español...")
    
    # Import the response function
    from src.bot.handlers import handle_response
    
    test_cases = [
        ("hola", "Hola"),
        ("¿cómo estás?", "Solo soy un bot"),
        ("adiós", "Hasta luego"),
        ("buenas", "Hola"),
        ("chao", "Hasta luego"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, (input_msg, expected_keyword) in enumerate(test_cases, 1):
        print(f"\n📝 Prueba {i}: '{input_msg}'")
        
        try:
            response = handle_response(input_msg)
            if response and expected_keyword.lower() in response.lower():
                print(f"   ✅ Respuesta correcta: {response[:50]}...")
                success_count += 1
            else:
                print(f"   ❌ Respuesta inesperada: {response}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Resultados: {success_count}/{total_tests} respuestas correctas")
    return success_count == total_tests

def test_unit_normalization():
    """Test unit normalization with Spanish units."""
    print("\n⚖️  Probando normalización de unidades...")
    
    from src.services.nlp_service import NLPService
    
    # Create a dummy NLP service just for unit normalization
    nlp = NLPService("dummy_key")
    
    test_cases = [
        ("gramos", 500, 0.5, "kg"),
        ("kg", 2, 2, "kg"),
        ("ml", 1000, 1.0, "liters"),
        ("litros", 2, 2, "liters"),
        ("piezas", 5, 5, "pcs"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, (unit, quantity, expected_quantity, expected_unit) in enumerate(test_cases, 1):
        print(f"\n📝 Prueba {i}: {quantity} {unit}")
        
        try:
            normalized_quantity, normalized_unit = nlp.normalize_unit(unit, quantity)
            
            print(f"   Resultado: {normalized_quantity} {normalized_unit}")
            print(f"   Esperado: {expected_quantity} {expected_unit}")
            
            if (abs(normalized_quantity - expected_quantity) < 0.001 and 
                normalized_unit == expected_unit):
                print("   ✅ ¡Correcto!")
                success_count += 1
            else:
                print("   ❌ Normalización incorrecta")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Resultados: {success_count}/{total_tests} normalizaciones correctas")
    return success_count == total_tests

def main():
    """Run all tests."""
    print("🚀 Iniciando pruebas de funcionalidad en español")
    print("=" * 50)
    
    all_passed = True
    
    # Test unit normalization (doesn't require API key)
    all_passed &= test_unit_normalization()
    
    # Test basic responses
    all_passed &= test_basic_responses()
    
    # Test NLP parsing (requires API key)
    all_passed &= test_nlp_spanish_parsing()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ El bot está listo para trabajar en español")
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("🔧 Revisa la configuración o las claves de API")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)