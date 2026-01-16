# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加新的权限管理字段到Admin表
"""

from app import app, db
from models import Admin
from sqlalchemy import text

def migrate_admin_table():
    """为Admin表添加新的权限字段"""
    with app.app_context():
        try:
            # 获取数据库连接
            connection = db.engine.connect()
            
            # 需要添加的字段列表
            new_columns = [
                ('permission_level', 'SMALLINT DEFAULT 4'),
                ('permissions', 'VARCHAR(500) DEFAULT \'\''),
                ('can_manage_users', 'BIT DEFAULT 0'),
                ('can_manage_forum', 'BIT DEFAULT 0'),
                ('can_manage_courses', 'BIT DEFAULT 0'),
                ('can_manage_grades', 'BIT DEFAULT 0'),
                ('can_manage_announcements', 'BIT DEFAULT 0'),
                ('can_review_content', 'BIT DEFAULT 0'),
                ('can_ban_users', 'BIT DEFAULT 0'),
            ]
            
            print("开始迁移Admin表...")
            
            for column_name, column_type in new_columns:
                try:
                    # 检查列是否已存在
                    check_sql = f"""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME='Admin' AND COLUMN_NAME='{column_name}'
                    """
                    result = connection.execute(text(check_sql))
                    
                    if not result.fetchone():
                        # 列不存在，添加它
                        alter_sql = f"ALTER TABLE [Admin] ADD [{column_name}] {column_type}"
                        connection.execute(text(alter_sql))
                        print(f"✓ 已添加列: {column_name}")
                    else:
                        print(f"✓ 列已存在: {column_name}")
                        
                except Exception as e:
                    print(f"✗ 添加列 {column_name} 失败: {e}")
            
            connection.commit()
            connection.close()
            print("✓ 迁移完成！")
            return True
            
        except Exception as e:
            print(f"✗ 迁移失败: {e}")
            return False

def create_missing_tables():
    """创建缺失的表"""
    with app.app_context():
        try:
            print("创建缺失的表...")
            db.create_all()
            print("✓ 表创建完成！")
            return True
        except Exception as e:
            print(f"✗ 创建表失败: {e}")
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("数据库迁移工具")
    print("=" * 50)
    
    # 首先尝试创建所有表
    create_missing_tables()
    
    # 然后进行迁移
    migrate_admin_table()
    
    print("=" * 50)
    print("迁移过程完成！")
    print("=" * 50)
