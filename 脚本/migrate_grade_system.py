"""
成绩系统数据表迁移脚本
用于创建新的成绩系统所需的数据表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import GradeCategory, GradeItem, StudentGradeScore, StudentFinalGrade

def migrate_grade_tables():
    """创建成绩系统相关表"""
    with app.app_context():
        try:
            print("开始创建成绩系统表...")
            
            # 创建表
            db.create_all()
            
            print("✓ 成绩系统表创建成功！")
            print("已创建的表：")
            print("  - grade_categories (成绩分类表)")
            print("  - grade_items (成绩项表)")
            print("  - student_grade_scores (学生成绩得分表)")
            print("  - student_final_grades (学生总评成绩表)")
            
        except Exception as e:
            print(f"✗ 创建表时出错: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_grade_tables()
