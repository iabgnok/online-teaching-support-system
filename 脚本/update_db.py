import sys
import os
# Add parent directory to path to allow importing app and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Announcement, Attendance, AttendanceRecord, ForumPost, ForumComment, Message

with app.app_context():
    print("Creating new tables...")
    try:
        # Create only the tables that don't exist
        db.create_all()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
