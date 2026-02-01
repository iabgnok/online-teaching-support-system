from models import db, Conversation
from app import app

with app.app_context():
    conv = Conversation.query.filter_by(id=2).first()
    if conv:
        print(f'当前标题: {conv.title}')
        # 移除emoji
        conv.title = conv.title.replace('🏫 ', '').replace('🏫', '')
        db.session.commit()
        print(f'新标题: {conv.title}')
