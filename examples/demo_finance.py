"""
Demo script to verify the new financial and inventory logic without Telegram.
"""
import os
import logging
from src.database.db import init_database
from src.services.smart_inventory_service import SmartInventoryService

# Setup logging
logging.basicConfig(level=logging.INFO)

def main():
    # Ensure DB is connected
    init_database()
    
    # Needs API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY env var.")
        return

    service = SmartInventoryService(api_key)

    print("\n--- TEST 1: Register Purchase ---")
    msg = "Compré 10kg de arroz por 15000 en el Líder con débito"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

    print("\n--- TEST 2: Check Stock ---")
    msg = "¿Cuánto arroz tenemos?"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

    print("\n--- TEST 3: Register Expense ---")
    msg = "Pagué 45000 de internet a VTR con transferencia"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

    print("\n--- TEST 4: Register Usage ---")
    msg = "Usé 2kg de arroz para el almuerzo"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

    print("\n--- TEST 5: Verify Stock Decrease ---")
    msg = "¿Cuánto arroz queda?"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

    print("\n--- TEST 6: Finance Report ---")
    msg = "¿Cuánto hemos gastado por proveedor?"
    print(f"User: {msg}")
    success, response = service.process_natural_language_command(msg)
    print(f"Bot: {response}")

if __name__ == "__main__":
    main()
