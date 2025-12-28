"""
数据库规范化迁移脚本
解决三个严重的规范化问题：
1. 删除 Student、Teacher、Admin 表中的 name 字段（使用 Users.real_name）
2. 创建 Department 表，将 department 字符串改为 dept_id 外键
3. 从 Student 表中删除 grade 和 class_name 字段

使用方法：
python normalize_database.py

注意：执行前请备份数据库！
"""

import pyodbc
from config import DB_DRIVER, DB_SERVER, DB_NAME
from datetime import datetime
import sys

def get_connection():
    """创建数据库连接"""
    try:
        conn_str = (
            f"DRIVER={{{DB_DRIVER}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print(f"连接字符串: {conn_str}")
        sys.exit(1)

def execute_sql(cursor, sql, description):
    """执行 SQL 并处理错误"""
    try:
        print(f"执行: {description}")
        cursor.execute(sql)
        print(f"✅ {description} - 成功")
        return True
    except Exception as e:
        print(f"⚠️  {description} - {e}")
        return False

def main():
    print("=" * 60)
    print("数据库规范化迁移脚本")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 确认操作
    print("⚠️  警告：此操作将修改数据库结构！")
    print("请确保已经备份数据库！")
    confirm = input("是否继续？(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("\n" + "=" * 60)
        print("步骤 1: 创建 Department 表")
        print("=" * 60)
        
        # 创建 Department 表
        create_dept_table = """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Department')
        BEGIN
            CREATE TABLE Department (
                dept_id BIGINT PRIMARY KEY,
                dept_name NVARCHAR(100) UNIQUE NOT NULL,
                description NVARCHAR(MAX),
                created_at DATETIME2(7) DEFAULT GETDATE(),
                updated_at DATETIME2(7) DEFAULT GETDATE()
            );
            PRINT 'Department 表创建成功';
        END
        ELSE
        BEGIN
            PRINT 'Department 表已存在';
        END
        """
        execute_sql(cursor, create_dept_table, "创建 Department 表")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("步骤 2: 提取并插入部门数据")
        print("=" * 60)
        
        # 从现有表中提取唯一的部门名称并插入到 Department 表
        insert_departments = """
        -- 从 Student、Teacher、Admin 表中提取所有唯一的部门
        DECLARE @dept_counter BIGINT = 1;
        
        -- 插入来自 Student 表的部门
        INSERT INTO Department (dept_id, dept_name, created_at)
        SELECT 
            ROW_NUMBER() OVER (ORDER BY department) AS dept_id,
            department,
            GETDATE()
        FROM (
            SELECT DISTINCT department 
            FROM Student 
            WHERE department IS NOT NULL AND department != ''
            UNION
            SELECT DISTINCT department 
            FROM Teacher 
            WHERE department IS NOT NULL AND department != ''
            UNION
            SELECT DISTINCT department 
            FROM Admin 
            WHERE department IS NOT NULL AND department != ''
        ) AS unique_depts
        WHERE department NOT IN (SELECT dept_name FROM Department);
        
        PRINT '部门数据插入完成';
        """
        execute_sql(cursor, insert_departments, "插入部门数据")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("步骤 3: 修改 Admin 表结构")
        print("=" * 60)
        
        # 为 Admin 表添加 dept_id 列
        alter_admin_add_dept = """
        IF NOT EXISTS (SELECT * FROM sys.columns 
                       WHERE object_id = OBJECT_ID('Admin') AND name = 'dept_id')
        BEGIN
            ALTER TABLE Admin ADD dept_id BIGINT;
            PRINT 'Admin.dept_id 列添加成功';
        END
        ELSE
        BEGIN
            PRINT 'Admin.dept_id 列已存在';
        END
        """
        execute_sql(cursor, alter_admin_add_dept, "Admin 表添加 dept_id 列")
        conn.commit()
        
        # 更新 Admin 表的 dept_id（根据原 department 字段）
        update_admin_dept = """
        UPDATE a
        SET a.dept_id = d.dept_id
        FROM Admin a
        INNER JOIN Department d ON a.department = d.dept_name
        WHERE a.department IS NOT NULL;
        
        PRINT 'Admin 表 dept_id 更新完成';
        """
        execute_sql(cursor, update_admin_dept, "更新 Admin 表 dept_id")
        conn.commit()
        
        # 添加外键约束
        add_admin_fk = """
        IF NOT EXISTS (SELECT * FROM sys.foreign_keys 
                       WHERE name = 'FK_Admin_Department')
        BEGIN
            ALTER TABLE Admin 
            ADD CONSTRAINT FK_Admin_Department 
            FOREIGN KEY (dept_id) REFERENCES Department(dept_id);
            PRINT 'Admin 外键约束添加成功';
        END
        """
        execute_sql(cursor, add_admin_fk, "Admin 表添加外键约束")
        conn.commit()
        
        # 删除 Admin 的 department 和 name 列
        drop_admin_cols = """
        -- 删除 department 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Admin') AND name = 'department')
        BEGIN
            ALTER TABLE Admin DROP COLUMN department;
            PRINT 'Admin.department 列删除成功';
        END
        
        -- 删除 name 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Admin') AND name = 'name')
        BEGIN
            ALTER TABLE Admin DROP COLUMN name;
            PRINT 'Admin.name 列删除成功';
        END
        """
        execute_sql(cursor, drop_admin_cols, "删除 Admin 表的 department 和 name 列")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("步骤 4: 修改 Student 表结构")
        print("=" * 60)
        
        # 为 Student 表添加 dept_id 列
        alter_student_add_dept = """
        IF NOT EXISTS (SELECT * FROM sys.columns 
                       WHERE object_id = OBJECT_ID('Student') AND name = 'dept_id')
        BEGIN
            ALTER TABLE Student ADD dept_id BIGINT;
            PRINT 'Student.dept_id 列添加成功';
        END
        """
        execute_sql(cursor, alter_student_add_dept, "Student 表添加 dept_id 列")
        conn.commit()
        
        # 更新 Student 表的 dept_id
        update_student_dept = """
        UPDATE s
        SET s.dept_id = d.dept_id
        FROM Student s
        INNER JOIN Department d ON s.department = d.dept_name
        WHERE s.department IS NOT NULL;
        
        PRINT 'Student 表 dept_id 更新完成';
        """
        execute_sql(cursor, update_student_dept, "更新 Student 表 dept_id")
        conn.commit()
        
        # 添加外键约束
        add_student_fk = """
        IF NOT EXISTS (SELECT * FROM sys.foreign_keys 
                       WHERE name = 'FK_Student_Department')
        BEGIN
            ALTER TABLE Student 
            ADD CONSTRAINT FK_Student_Department 
            FOREIGN KEY (dept_id) REFERENCES Department(dept_id);
            PRINT 'Student 外键约束添加成功';
        END
        """
        execute_sql(cursor, add_student_fk, "Student 表添加外键约束")
        conn.commit()
        
        # 删除 Student 的冗余列
        drop_student_cols = """
        -- 删除 department 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Student') AND name = 'department')
        BEGIN
            ALTER TABLE Student DROP COLUMN department;
            PRINT 'Student.department 列删除成功';
        END
        
        -- 删除 name 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Student') AND name = 'name')
        BEGIN
            ALTER TABLE Student DROP COLUMN name;
            PRINT 'Student.name 列删除成功';
        END
        
        -- 删除 gender 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Student') AND name = 'gender')
        BEGIN
            ALTER TABLE Student DROP COLUMN gender;
            PRINT 'Student.gender 列删除成功';
        END
        
        -- 删除 grade 列（变动属性）
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Student') AND name = 'grade')
        BEGIN
            ALTER TABLE Student DROP COLUMN grade;
            PRINT 'Student.grade 列删除成功';
        END
        
        -- 删除 class_name 列（变动属性）
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Student') AND name = 'class_name')
        BEGIN
            ALTER TABLE Student DROP COLUMN class_name;
            PRINT 'Student.class_name 列删除成功';
        END
        """
        execute_sql(cursor, drop_student_cols, "删除 Student 表的冗余列")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("步骤 5: 修改 Teacher 表结构")
        print("=" * 60)
        
        # 为 Teacher 表添加 dept_id 列
        alter_teacher_add_dept = """
        IF NOT EXISTS (SELECT * FROM sys.columns 
                       WHERE object_id = OBJECT_ID('Teacher') AND name = 'dept_id')
        BEGIN
            ALTER TABLE Teacher ADD dept_id BIGINT;
            PRINT 'Teacher.dept_id 列添加成功';
        END
        """
        execute_sql(cursor, alter_teacher_add_dept, "Teacher 表添加 dept_id 列")
        conn.commit()
        
        # 更新 Teacher 表的 dept_id
        update_teacher_dept = """
        UPDATE t
        SET t.dept_id = d.dept_id
        FROM Teacher t
        INNER JOIN Department d ON t.department = d.dept_name
        WHERE t.department IS NOT NULL;
        
        PRINT 'Teacher 表 dept_id 更新完成';
        """
        execute_sql(cursor, update_teacher_dept, "更新 Teacher 表 dept_id")
        conn.commit()
        
        # 添加外键约束
        add_teacher_fk = """
        IF NOT EXISTS (SELECT * FROM sys.foreign_keys 
                       WHERE name = 'FK_Teacher_Department')
        BEGIN
            ALTER TABLE Teacher 
            ADD CONSTRAINT FK_Teacher_Department 
            FOREIGN KEY (dept_id) REFERENCES Department(dept_id);
            PRINT 'Teacher 外键约束添加成功';
        END
        """
        execute_sql(cursor, add_teacher_fk, "Teacher 表添加外键约束")
        conn.commit()
        
        # 删除 Teacher 的冗余列
        drop_teacher_cols = """
        -- 删除 department 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Teacher') AND name = 'department')
        BEGIN
            ALTER TABLE Teacher DROP COLUMN department;
            PRINT 'Teacher.department 列删除成功';
        END
        
        -- 删除 name 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Teacher') AND name = 'name')
        BEGIN
            ALTER TABLE Teacher DROP COLUMN name;
            PRINT 'Teacher.name 列删除成功';
        END
        
        -- 删除 gender 列
        IF EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('Teacher') AND name = 'gender')
        BEGIN
            ALTER TABLE Teacher DROP COLUMN gender;
            PRINT 'Teacher.gender 列删除成功';
        END
        """
        execute_sql(cursor, drop_teacher_cols, "删除 Teacher 表的冗余列")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ 数据库规范化迁移完成！")
        print("=" * 60)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("已完成的改动：")
        print("1. ✅ 创建了 Department 表")
        print("2. ✅ Admin 表：删除 name 和 department，添加 dept_id 外键")
        print("3. ✅ Student 表：删除 name、gender、department、grade、class_name，添加 dept_id 外键")
        print("4. ✅ Teacher 表：删除 name、gender、department，添加 dept_id 外键")
        print()
        print("注意事项：")
        print("- 原有的 name 字段数据已删除，请通过 Users.real_name 获取用户姓名")
        print("- 原有的 department 字符串已转换为 dept_id 外键")
        print("- Student 的 grade 和 class_name 已删除（这些是变动属性）")
        print("- 应用代码中对这些字段的引用需要更新")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
