import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'data.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE scrape_task ADD COLUMN user_id INTEGER REFERENCES user(id)")
        print("Successfully added 'user_id' column to scrape_task table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e} (Column might already exist)")
    except Exception as e:
        print(f"Error: {e}")

    try:
        # Default all existing scrape tasks to user ID 1 (presumably the admin) to prevent orphans
        cursor.execute("UPDATE scrape_task SET user_id = 1 WHERE user_id IS NULL")
        print("Updated existing scrape tasks to belong to user ID 1.")
    except Exception as e:
        print(f"Error updating task ownership: {e}")

    conn.commit()
    conn.close()
else:
    print("Database data.db does not exist yet.")
