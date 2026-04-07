import os
import psycopg2 # Ensure this is in your requirements.txt
import sqlite3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_connection():
    # Render provides DATABASE_URL in the environment
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        # Use PostgreSQL for Render
        return psycopg2.connect(db_url)
    else:
        # Fallback to SQLite for local development
        return sqlite3.connect('neural_core.db')

def init_neural_core():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Example Schema - Adjust to your actual table needs
    # Note: PostgreSQL syntax uses SERIAL instead of AUTOINCREMENT
    create_table_query = """
    CREATE TABLE IF NOT EXISTS neural_data (
        id SERIAL PRIMARY KEY,
        key_name TEXT UNIQUE NOT NULL,
        value_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        cursor.execute(create_table_query)
        conn.commit()
        print("Neural Core initialized successfully on " + 
              ("PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"))
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_neural_core()