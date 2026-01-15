import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Updating database schema...")
    try:
        # Attempt to add columns. If they exist, it might fail or we can catch it.
        # Syntax for SQL Server / SQLite / PostgreSQL usually supports ADD COLUMN or ADD.
        # Assuming SQL Server based on previous context warnings, or generic SQL.
        
        # Checking connection dialect to be safe, but generic ALTER TABLE usually works for simple columns
        with db.engine.connect() as conn:
            with conn.begin():
                try:
                    conn.execute(text("ALTER TABLE ForumPost ADD file_name VARCHAR(255) NULL"))
                    print("Added file_name column.")
                except Exception as e:
                    print(f"file_name column might already exist or error: {e}")
                
                try:
                    conn.execute(text("ALTER TABLE ForumPost ADD file_path VARCHAR(500) NULL"))
                    print("Added file_path column.")
                except Exception as e:
                    print(f"file_path column might already exist or error: {e}")

    except Exception as e:
        print(f"Migration failed: {e}")
