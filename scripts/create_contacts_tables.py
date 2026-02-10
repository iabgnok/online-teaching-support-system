"""Simple helper to create missing tables for contacts/friend system in development."""
from app import app
from models import db

with app.app_context():
    # This will create any tables that do not yet exist (safe for dev)
    db.create_all()
    print('create_all() executed - new tables created if they did not exist.')
