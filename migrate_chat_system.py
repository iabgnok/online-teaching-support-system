"""
数据库迁移脚本 - 添加即时通讯系统表
执行命令: python migrate_chat_system.py
"""

from app import app
from models import db, Conversation, ConversationMember, IMMessage, MessageStatus, UserOnlineStatus
from sqlalchemy import text

def migrate_chat_system():
    """创建即时通讯系统所需的表"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("开始创建即时通讯系统数据表...")
            print("=" * 60)
            
            # 创建新表
            tables_to_create = [
                ('Conversation', Conversation),
                ('ConversationMember', ConversationMember),
                ('IMMessage', IMMessage),
                ('MessageStatus', MessageStatus),
                ('UserOnlineStatus', UserOnlineStatus),
            ]
            
            for table_name, model in tables_to_create:
                try:
                    # 检查表是否已存在（SQL Server版本）
                    result = db.session.execute(
                        text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME=:table_name"),
                        {'table_name': table_name}
                    ).fetchone()
                    
                    if result:
                        print(f"✓ 表 {table_name} 已存在，跳过创建")
                    else:
                        model.__table__.create(db.engine)
                        print(f"✓ 成功创建表: {table_name}")
                except Exception as e:
                    print(f"✗ 创建表 {table_name} 时出错: {e}")
            
            print("\n" + "=" * 60)
            print("数据库迁移完成！")
            print("=" * 60)
            
            # 显示表结构信息
            print("\n新增的表结构:")
            print("-" * 60)
            print("1. Conversation - 对话表（私聊/群聊/课程群）")
            print("2. ConversationMember - 对话成员表")
            print("3. IMMessage - 即时消息表")
            print("4. MessageStatus - 消息状态表")
            print("5. UserOnlineStatus - 用户在线状态表")
            print("-" * 60)
            
        except Exception as e:
            print(f"\n迁移过程中发生错误: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_chat_system()
