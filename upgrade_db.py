import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'data.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        print("Successfully added 'is_admin' column to user table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e} (Column might already exist)")
    except Exception as e:
        print(f"Error: {e}")

    try:
        # Make the very first user the admin by default
        cursor.execute("UPDATE user SET is_admin = 1 WHERE id = 1")
        print("Updated user ID 1 to be an admin for testing purposes.")
    except Exception as e:
        print(f"Error updating admin status: {e}")

    conn.commit()
    conn.close()
else:
    print("Database data.db does not exist yet.")
