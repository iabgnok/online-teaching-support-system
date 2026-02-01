"""
修复消息的发送者姓名显示
将所有消息的sender_name更新为用户的real_name
"""
from models import db, IMMessage, Users
from app import app

with app.app_context():
    print("=" * 60)
    print("Fixing message sender names...")
    print("=" * 60)
    
    # 获取所有消息
    messages = IMMessage.query.all()
    print(f"\nTotal messages: {len(messages)}")
    
    updated = 0
    for msg in messages:
        sender = Users.query.get(msg.sender_id)
        if sender:
            old_name = f"{msg.sender_id}"
            new_name = sender.real_name or sender.username
            print(f"Message {msg.id}: sender_id={msg.sender_id} -> {new_name}")
            updated += 1
    
    print(f"\n{updated} messages found")
    print("=" * 60)
    print("\nNote: sender_name is derived from sender relationship")
    print("No database update needed - just use msg.sender.real_name")
    print("=" * 60)
