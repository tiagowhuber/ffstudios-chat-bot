"""
Service for generating data insights using Text-to-SQL logic with OpenAI.
"""
import logging
import json
from typing import Optional, List, Any, Tuple
from sqlalchemy import text
from openai import OpenAI

# Import the DB session provider
from src.database.db import get_db_session

logger = logging.getLogger(__name__)

# Schema definition for the LLM
DB_SCHEMA_CONTEXT = """
POSTGRESQL SCHEMA:

CREATE TABLE tipos_gasto (id SERIAL PRIMARY KEY, nombre VARCHAR(20));
CREATE TABLE categorias (id SERIAL PRIMARY KEY, nombre VARCHAR(50), descripcion TEXT);
CREATE TABLE metodos_pago (id SERIAL PRIMARY KEY, nombre VARCHAR(50));
CREATE TABLE proveedores (id SERIAL PRIMARY KEY, nombre VARCHAR(100));

CREATE TABLE catalogo_productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    unidad_medida VARCHAR(20),
    categoria_id INT REFERENCES categorias(id)
);

CREATE TABLE inventario (
    producto_id INT PRIMARY KEY REFERENCES catalogo_productos(id),
    cantidad_actual DECIMAL(12,2) DEFAULT 0.00,
    ultima_actualizacion TIMESTAMP
);

CREATE TABLE gastos (
    id UUID PRIMARY KEY,
    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(12, 2),
    metodo_pago_id INT REFERENCES metodos_pago(id),
    proveedor_id INT REFERENCES proveedores(id),
    tipo_gasto_id INT REFERENCES tipos_gasto(id),
    categoria_id INT REFERENCES categorias(id),
    producto_id INT REFERENCES catalogo_productos(id),
    cantidad_comprada DECIMAL(10, 2),
    item_descripcion VARCHAR(255),
    observaciones TEXT
);

CREATE TABLE salidas_inventario (
    id UUID PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    producto_id INT NOT NULL REFERENCES catalogo_productos(id),
    cantidad_usada DECIMAL(10, 2),
    motivo VARCHAR(100)
);

RELATIONSHIPS to use in JOINS:
- gastos.proveedor_id -> proveedores.id (Get provider name: proveedores.nombre)
- gastos.categoria_id -> categorias.id (Get category name: categorias.nombre)
- gastos.metodo_pago_id -> metodos_pago.id (Get method name: metodos_pago.nombre)
- gastos.producto_id -> catalogo_productos.id (Get product name: catalogo_productos.nombre)
"""

class DataAnalystService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_insight(self, user_question: str) -> str:
        """
        Main entry point:
        1. Translate Question -> SQL
        2. Execute SQL (Safely)
        3. Translate Results -> Answer
        """
        try:
            # 1. Generate SQL
            sql_query = self._generate_sql(user_question)
            logger.info(f"Generated SQL: {sql_query}")

            # 2. Execute
            columns, rows = self._execute_safe_sql(sql_query)
            
            if not rows:
                return "Analicé la base de datos y no encontré registros que coincidan con tu búsqueda."

            # 3. Summarize
            answer = self._generate_summary(user_question, columns, rows)
            return answer

        except ValueError as ve:
            logger.warning(f"SQL Safety Warning: {ve}")
            return "Lo siento, no puedo realizar esa operación por motivos de seguridad (solo lectura)."
        except Exception as e:
            logger.error(f"Error in DataAnalystService: {e}")
            return "Tuve un problema analizando los datos. Intenta con una pregunta más simple."

    def _generate_sql(self, question: str) -> str:
        """Asks OpenAI to generate a SQL query based on the schema."""
        system_prompt = f"""
        You are a PostgreSQL Data Analyst for a business.
        Given the database schema below, write a SQL query to answer the user's question.
        
        {DB_SCHEMA_CONTEXT}
        
        RULES:
        1. Return ONLY the SQL query. No markdown, no explanations.
        2. Use only SELECT statements.
        3. Use standard PostgreSQL syntax (e.g. "EXTRACT(MONTH FROM date)").
        4. Always JOIN tables to provide readable names (e.g. join 'proveedores' to get 'nombre' instead of just 'proveedor_id').
        5. If the time is not specified, assume "ALL TIME". If "this month", use CURRENT_DATE.
        6. LIMIT results to 20 if logic implies a list.
        7. When filtering by names (proveedor, categoria, producto, etc.), ALWAYS use ILIKE with wildcards for robustness (e.g. WHERE p.nombre ILIKE '%Lider%').
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0
        )
        
        sql = response.choices[0].message.content.strip()
        # Cleanup markdown if present
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def _execute_safe_sql(self, sql_query: str) -> Tuple[List[str], List[Any]]:
        """Executes the SQL if it's a readonly SELECT."""
        
        # Basic Security Check
        forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "GRANT", "CREATE"]
        upper_sql = sql_query.upper()
        for word in forbidden:
            if word in upper_sql:
                raise ValueError(f"Forbidden keyword detected: {word}")

        with get_db_session() as session:
            result = session.execute(text(sql_query))
            rows = result.fetchall()
            columns = list(result.keys())
            return columns, rows

    def _generate_summary(self, question: str, columns: List[str], rows: List[Any]) -> str:
        """Turns the raw database rows into a friendly natural language response."""
        
        # Convert rows to a simple string representation
        data_str = f"Columns: {columns}\nData (first 20 rows): {rows[:20]}"
        
        system_prompt = """
        You are a helpful financial assistant.
        The user asked a question, and here is the raw data from the database.
        Summarize the answer in Spanish naturally. 
        
        - If it's a sum, just state the amount clearly.
        - If it's a list, summarize the top items.
        - Use Chilean Pesos formatting ($10.000) if context implies money.
        - Be concise.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nDatabase Result:\n{data_str}"}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
