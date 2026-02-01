#!/usr/bin/env python3
"""线上授课功能数据库迁移脚本"""

from app import app, db
from models import LiveClass, DrawingData, ChatMessage, LiveParticipant, ClassNote
import sys

def migrate_live_class():
    """创建线上授课相关的数据表"""
    with app.app_context():
        try:
            print("🔄 开始创建线上授课数据表...")

            # 创建表
            db.create_all()

            print("✅ 数据库迁移完成")
            print("✅ 创建表: LiveClass (线上课堂表)")
            print("✅ 创建表: DrawingData (画板绘制数据表)")
            print("✅ 创建表: ChatMessage (课堂聊天消息表)")
            print("✅ 创建表: LiveParticipant (课堂参与者表)")
            print("✅ 创建表: ClassNote (课堂笔记表)")

            return True

        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            return False

if __name__ == "__main__":
    success = migrate_live_class()
    sys.exit(0 if success else 1)