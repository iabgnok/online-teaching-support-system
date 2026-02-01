"""
检查聊天系统数据库状态
"""
from models import db, Conversation, ConversationMember, IMMessage, Users
from app import app

with app.app_context():
    print("=" * 60)
    print("聊天系统数据库状态")
    print("=" * 60)
    
    # 检查对话数量
    conv_count = Conversation.query.count()
    print(f"\n对话总数: {conv_count}")
    
    # 检查消息数量
    msg_count = IMMessage.query.count()
    print(f"消息总数: {msg_count}")
    
    # 检查用户
    users = Users.query.limit(5).all()
    print(f"\n前5个用户:")
    for user in users:
        print(f"  - {user.username} (ID: {user.user_id}, 角色: {user.role})")
    
    # 显示所有对话
    if conv_count > 0:
        print(f"\n所有对话:")
        conversations = Conversation.query.all()
        for conv in conversations:
            members_count = ConversationMember.query.filter_by(conversation_id=conv.id).count()
            messages_count = IMMessage.query.filter_by(conversation_id=conv.id).count()
            print(f"  - ID: {conv.id}, 类型: {conv.conversation_type}, 成员: {members_count}, 消息: {messages_count}")
    
    print("=" * 60)
