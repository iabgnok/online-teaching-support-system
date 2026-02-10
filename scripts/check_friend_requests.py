from app import app
from models import db, FriendRequest

with app.app_context():
    reqs = FriendRequest.query.order_by(FriendRequest.created_at.desc()).limit(10).all()
    for r in reqs:
        print(r.id, r.requester_id, r.target_id, r.status, r.message, r.created_at)
