"""
修复Conversation表缺少live_class_id列的问题
同时确保表结构与模型定义一致
"""

from models import db
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    print("开始修复Conversation表结构...")
    
    try:
        # 检查列是否已存在
        check_sql = """
        SELECT COUNT(*) as col_count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Conversation'
        AND COLUMN_NAME = 'live_class_id'
        """
        
        result = db.session.execute(text(check_sql)).fetchone()
        
        if result[0] == 0:
            print("  → live_class_id 列不存在，正在添加...")
            
            # 添加 live_class_id 列
            alter_sql = """
            ALTER TABLE [Conversation]
            ADD [live_class_id] BIGINT NULL
            """
            db.session.execute(text(alter_sql))
            
            # 添加外键约束
            fk_sql = """
            ALTER TABLE [Conversation]
            ADD CONSTRAINT FK_Conversation_LiveClass
            FOREIGN KEY ([live_class_id]) REFERENCES [LiveClass]([id])
            """
            try:
                db.session.execute(text(fk_sql))
                print("  ✓ 已添加外键约束")
            except Exception as e:
                print(f"  ⚠ 外键约束添加失败（可能已存在）: {e}")
            
            db.session.commit()
            print("  ✓ live_class_id 列添加成功！")
        else:
            print("  ✓ live_class_id 列已存在，无需添加")
        
        # 验证表结构
        print("\n验证Conversation表结构...")
        verify_sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Conversation'
        ORDER BY ORDINAL_POSITION
        """
        columns = db.session.execute(text(verify_sql)).fetchall()
        
        print("\n当前Conversation表结构：")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        print("\n✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        success = migrate()
        if success:
            print("\n可以重启后端服务了！")
        else:
            print("\n请检查错误信息并修复")
