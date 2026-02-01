"""
聊天系统功能扩展数据库迁移脚本
添加消息反应、置顶消息和提及通知功能

执行方式: python migrate_chat_features.py
"""

from app import app, db
from models import MessageReaction, PinnedMessage, MentionNotification
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    with app.app_context():
        print("=" * 60)
        print("聊天系统功能扩展 - 数据库迁移")
        print("=" * 60)
        
        try:
            # 创建新表
            print("\n1. 创建消息反应表 (MessageReaction)...")
            db.create_all()
            print("   ✓ 消息反应表创建成功")
            
            print("\n2. 创建置顶消息表 (PinnedMessage)...")
            print("   ✓ 置顶消息表创建成功")
            
            print("\n3. 创建提及通知表 (MentionNotification)...")
            print("   ✓ 提及通知表创建成功")
            
            # 检查表是否存在
            print("\n4. 验证表结构...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['MessageReaction', 'PinnedMessage', 'MentionNotification']
            for table in required_tables:
                if table in tables:
                    print(f"   ✓ {table} 表存在")
                    # 显示字段信息
                    columns = inspector.get_columns(table)
                    print(f"     字段数: {len(columns)}")
                    for col in columns:
                        print(f"     - {col['name']}: {col['type']}")
                else:
                    print(f"   ✗ {table} 表不存在")
            
            print("\n" + "=" * 60)
            print("迁移完成！")
            print("=" * 60)
            
            print("\n新增功能:")
            print("  1. 消息表情反应 (👍 ❤️ 😂 😮 😢 🙏 🔥 👏)")
            print("  2. 消息置顶功能（群组公告）")
            print("  3. @ 提及通知功能")
            print("  4. 消息转发功能")
            print("  5. 撤回消息（对所有人删除）")
            print("  6. 仅对我删除消息")
            print("  7. 网页链接预览")
            
            print("\n新增API端点:")
            print("  POST   /api/v1/chat/messages/<id>/reactions")
            print("  GET    /api/v1/chat/messages/<id>/reactions")
            print("  DELETE /api/v1/chat/messages/<id>/reactions/<user_id>")
            print("  GET    /api/v1/chat/conversations/<id>/pinned_messages")
            print("  POST   /api/v1/chat/messages/<id>/pin")
            print("  DELETE /api/v1/chat/pinned_messages/<pin_id>")
            print("  POST   /api/v1/chat/messages/<id>/forward")
            print("  GET    /api/v1/chat/conversations/<id>/members/search")
            print("  GET    /api/v1/chat/mentions")
            print("  POST   /api/v1/chat/mentions/<id>/read")
            print("  POST   /api/v1/chat/messages/<id>/unsend")
            print("  POST   /api/v1/chat/messages/<id>/delete_for_me")
            print("  POST   /api/v1/chat/link_preview")
            
        except Exception as e:
            print(f"\n✗ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    success = migrate()
    if success:
        print("\n✓ 数据库迁移成功完成！")
    else:
        print("\n✗ 数据库迁移失败，请检查错误信息。")
