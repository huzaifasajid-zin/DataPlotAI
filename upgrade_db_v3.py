import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'data.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['scrape_task', 'automation_schedule']
    columns = ['location', 'company', 'time_period', 'salary']
    
    for table in tables:
        for column in columns:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(255)")
                print(f"Added {column} to {table}")
            except sqlite3.OperationalError:
                pass # Column exists
                
    conn.commit()
    conn.close()
    print("Migration V3 Complete.")
