"""
数据库迁移脚本：为Admin表添加permission_level字段
运行此脚本以更新现有数据库结构
支持 SQL Server 和 SQLite
"""

from app import app, db
from models import Admin
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            print("正在检查数据库结构...")
            
            with db.engine.connect() as conn:
                # 检测数据库类型
                db_type = db.engine.dialect.name
                print(f"检测到数据库类型: {db_type}")
                
                if db_type == 'mssql':
                    # SQL Server 数据库
                    # 检查列是否存在
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM sys.columns 
                        WHERE object_id = OBJECT_ID('Admin') 
                        AND name = 'permission_level'
                    """))
                    column_exists = result.scalar() > 0
                    
                    if not column_exists:
                        print("添加permission_level字段...")
                        conn.execute(text(
                            "ALTER TABLE [Admin] ADD permission_level INT DEFAULT 3"
                        ))
                        conn.commit()
                        print("✅ permission_level字段添加成功！")
                        
                        # 将第一个管理员设为最高权限
                        print("正在设置默认权限...")
                        result = conn.execute(text(
                            "SELECT TOP 1 admin_id, admin_no FROM [Admin] ORDER BY admin_id"
                        ))
                        first_admin = result.fetchone()
                        
                        if first_admin:
                            conn.execute(text(
                                f"UPDATE [Admin] SET permission_level = 1 WHERE admin_id = {first_admin[0]}"
                            ))
                            print(f"✅ 管理员 {first_admin[1]} 已设置为最高权限（级别1）")
                            conn.commit()
                        
                        print("✅ 所有权限设置完成！")
                    else:
                        print("✅ permission_level字段已存在，无需迁移。")
                        
                elif db_type == 'sqlite':
                    # SQLite 数据库
                    result = conn.execute(text("PRAGMA table_info(Admin)"))
                    columns = [row[1] for row in result]
                    
                    if 'permission_level' not in columns:
                        print("添加permission_level字段...")
                        conn.execute(text(
                            "ALTER TABLE Admin ADD COLUMN permission_level INTEGER DEFAULT 3"
                        ))
                        conn.commit()
                        print("✅ permission_level字段添加成功！")
                        
                        print("正在设置默认权限...")
                        result = conn.execute(text(
                            "SELECT admin_id, admin_no FROM Admin ORDER BY admin_id LIMIT 1"
                        ))
                        first_admin = result.fetchone()
                        
                        if first_admin:
                            conn.execute(text(
                                f"UPDATE Admin SET permission_level = 1 WHERE admin_id = {first_admin[0]}"
                            ))
                            print(f"✅ 管理员 {first_admin[1]} 已设置为最高权限（级别1）")
                            conn.commit()
                        
                        print("✅ 所有权限设置完成！")
                    else:
                        print("✅ permission_level字段已存在，无需迁移。")
                else:
                    print(f"⚠️ 不支持的数据库类型: {db_type}")
                    print("请手动执行以下SQL（根据你的数据库类型调整语法）:")
                    print("ALTER TABLE Admin ADD COLUMN permission_level INTEGER DEFAULT 3;")
                    print("UPDATE Admin SET permission_level = 1 WHERE admin_no = 'A001';")
                    
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            print("\n请手动执行以下SQL:")
            print("-- SQL Server:")
            print("ALTER TABLE [Admin] ADD permission_level INT DEFAULT 3;")
            print("UPDATE [Admin] SET permission_level = 1 WHERE admin_no = 'A001';")
            print("\n-- SQLite:")
            print("ALTER TABLE Admin ADD COLUMN permission_level INTEGER DEFAULT 3;")
            print("UPDATE Admin SET permission_level = 1 WHERE admin_no = 'A001';")

if __name__ == '__main__':
    print("=" * 50)
    print("开始数据库迁移...")
    print("=" * 50)
    migrate_database()
    print("=" * 50)
    print("迁移完成！")
    print("=" * 50)
