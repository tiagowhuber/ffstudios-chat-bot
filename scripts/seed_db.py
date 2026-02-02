"""
Script to seed the database with initial data from scripts/seed_data.sql.
"""
import sys
import os
from sqlalchemy import text

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.db import init_database, get_db_session, close_database

def seed_database():
    print("Initializing database...")
    init_database()
    
    sql_file_path = os.path.join(os.path.dirname(__file__), 'seed_data.sql')
    print(f"Reading SQL from {sql_file_path}...")
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Split by statements to ensure proper execution if the driver doesn't support multiple statements at once reliably
    # Or just execute the whole block if supported. SQLAlchemy execute(text()) can often handle scripts if the driver does.
    # psycopg2 usually supports it.
    
    print("Executing SQL...")
    try:
        with get_db_session() as session:
            session.execute(text(sql_content))
            session.commit()
            print("✅ Database seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        close_database()

if __name__ == "__main__":
    seed_database()
