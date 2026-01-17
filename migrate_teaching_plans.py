"""
迁移脚本：添加教学计划和个人任务表
用法：python migrate_teaching_plans.py
"""

from app import app, db
from models import TeachingPlan, PersonalTask

def migrate():
    """执行迁移"""
    with app.app_context():
        # 创建所有新表
        db.create_all()
        print("✅ 数据库迁移完成")
        print("✅ 创建表: TeachingPlan (教学计划表)")
        print("✅ 创建表: PersonalTask (个人任务表)")

if __name__ == '__main__':
    migrate()
