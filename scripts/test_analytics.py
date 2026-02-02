"""
Script to test the DataAnalystService with various natural language queries.
This script bypasses the NLP intent classifier and tests the Text-to-SQL logic directly.
"""
import sys
import os
import logging
import time

# Add the project root to the python path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from src.services.data_analyst_service import DataAnalystService
from src.database.db import init_database, close_database

# Configure logging to show us the generated SQL
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    # 1. Load Environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return

    # 2. Initialize Database
    print("Initializing Database...")
    init_database()

    # 3. Initialize Service
    print("Initializing Data Analyst Service...")
    service = DataAnalystService(api_key)

    # 4. Define Test Questions
    test_questions = [
        # --- Basic Aggregations ---
        "¿Cuál es el gasto total histórico?",
        "¿Cuántas transacciones de gasto hay en total?",

        # --- Filtering by Provider (JOIN) ---
        "¿Cuánto le hemos comprado a 'Lider' en total?",
        "¿Cuánto se ha gastado en 'CGE'?",

        # --- Filtering by Date/Time ---
        "¿Cuánto gastamos el mes pasado?",
        "¿Cuáles fueron los gastos de la semana pasada?",
        "¿Cuánto gastamos en diciembre de 2025?",

        # --- Filtering by Category/Type ---
        "¿Cuánto hemos gastado en la categoría 'comida'?",
        "¿Cuál es el total de gastos fijos?",

        # --- Complex / Multi-filter ---
        "¿Cuál fue la compra más cara que hicimos en Lider?",
        "Muéstrame los 3 gastos más altos de la historia.",
        
        # --- Payment Methods ---
        "¿Cuánto hemos pagado con tarjeta de crédito?",
        
        # --- Inventory Interaction (via generated SQL) ---
        "¿Cuál es el producto con más stock en el inventario?",
        "¿Cuánto dinero tenemos invertido en stock actual (cantidad * costo promedio estimativo)?" 
        # Note: Cost logic might be tricky for AI if cost isn't in inventory table, but let's see what it tries.
        # Actually, standard inventory table here has 'cantidad_actual' but cost is in 'gastos'. 
        # This is a hard question for the AI without a clear 'cost' column in 'catalogo_productos'.
    ]

    print(f"\nRunning {len(test_questions)} test questions...\n")
    print("="*60)

    for i, question in enumerate(test_questions, 1):
        print(f"\n🔹 QUESTION {i}: {question}")
        print("-" * 20)
        
        start_time = time.time()
        try:
            # The service logs the SQL at INFO level, so it will appear in stdout
            result = service.generate_insight(question)
            
            elapsed = time.time() - start_time
            print(f"⏱️  Time: {elapsed:.2f}s")
            print(f"🤖 ANSWER: {result}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("="*60)

    # Cleanup
    close_database()

if __name__ == "__main__":
    main()
