"""
验证并修复数据库规范化
检查表结构并执行缺失的修改
"""

import pyodbc
from config import DB_DRIVER, DB_SERVER, DB_NAME
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
        sys.exit(1)

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    query = """
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
    """
    cursor.execute(query, table_name, column_name)
    result = cursor.fetchone()
    return result[0] > 0

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    query = """
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = ?
    """
    cursor.execute(query, table_name)
    result = cursor.fetchone()
    return result[0] > 0

def main():
    print("=" * 60)
    print("数据库结构验证和修复工具")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n检查当前表结构...")
    
    # 检查 Department 表
    print("\n【Department 表】")
    if check_table_exists(cursor, 'Department'):
        print("✅ Department 表已存在")
    else:
        print("❌ Department 表不存在 - 需要创建")
    
    # 检查 Admin 表
    print("\n【Admin 表】")
    has_name = check_column_exists(cursor, 'Admin', 'name')
    has_dept = check_column_exists(cursor, 'Admin', 'department')
    has_dept_id = check_column_exists(cursor, 'Admin', 'dept_id')
    
    print(f"  name 列: {'❌ 仍存在（需要删除）' if has_name else '✅ 已删除'}")
    print(f"  department 列: {'❌ 仍存在（需要删除）' if has_dept else '✅ 已删除'}")
    print(f"  dept_id 列: {'✅ 已添加' if has_dept_id else '❌ 不存在（需要添加）'}")
    
    # 检查 Student 表
    print("\n【Student 表】")
    s_name = check_column_exists(cursor, 'Student', 'name')
    s_gender = check_column_exists(cursor, 'Student', 'gender')
    s_dept = check_column_exists(cursor, 'Student', 'department')
    s_grade = check_column_exists(cursor, 'Student', 'grade')
    s_class = check_column_exists(cursor, 'Student', 'class_name')
    s_dept_id = check_column_exists(cursor, 'Student', 'dept_id')
    
    print(f"  name 列: {'❌ 仍存在（需要删除）' if s_name else '✅ 已删除'}")
    print(f"  gender 列: {'❌ 仍存在（需要删除）' if s_gender else '✅ 已删除'}")
    print(f"  department 列: {'❌ 仍存在（需要删除）' if s_dept else '✅ 已删除'}")
    print(f"  grade 列: {'❌ 仍存在（需要删除）' if s_grade else '✅ 已删除'}")
    print(f"  class_name 列: {'❌ 仍存在（需要删除）' if s_class else '✅ 已删除'}")
    print(f"  dept_id 列: {'✅ 已添加' if s_dept_id else '❌ 不存在（需要添加）'}")
    
    # 检查 Teacher 表
    print("\n【Teacher 表】")
    t_name = check_column_exists(cursor, 'Teacher', 'name')
    t_gender = check_column_exists(cursor, 'Teacher', 'gender')
    t_dept = check_column_exists(cursor, 'Teacher', 'department')
    t_dept_id = check_column_exists(cursor, 'Teacher', 'dept_id')
    
    print(f"  name 列: {'❌ 仍存在（需要删除）' if t_name else '✅ 已删除'}")
    print(f"  gender 列: {'❌ 仍存在（需要删除）' if t_gender else '✅ 已删除'}")
    print(f"  department 列: {'❌ 仍存在（需要删除）' if t_dept else '✅ 已删除'}")
    print(f"  dept_id 列: {'✅ 已添加' if t_dept_id else '❌ 不存在（需要添加）'}")
    
    # 判断是否需要修复
    needs_fix = (has_name or has_dept or s_name or s_gender or s_dept or s_grade or 
                 s_class or t_name or t_gender or t_dept)
    
    if needs_fix:
        print("\n" + "=" * 60)
        print("⚠️  发现需要修复的问题！")
        print("=" * 60)
        print("\n是否执行修复？这将删除上述标记为'需要删除'的列。")
        confirm = input("确认修复？(yes/no): ")
        
        if confirm.lower() == 'yes':
            print("\n开始修复...")
            fix_database(cursor, conn)
        else:
            print("❌ 修复已取消")
    else:
        print("\n" + "=" * 60)
        print("✅ 数据库结构正确，无需修复！")
        print("=" * 60)
    
    cursor.close()
    conn.close()

def fix_database(cursor, conn):
    """执行数据库修复"""
    
    try:
        # 先删除所有相关的索引
        print("\n删除相关索引...")
        
        # 删除 Student 表的索引
        if check_column_exists(cursor, 'Student', 'department'):
            try:
                cursor.execute("DROP INDEX IF EXISTS idx_student_department ON Student")
                print("  ✅ 删除索引 idx_student_department")
            except:
                pass
        
        # 删除 Teacher 表的索引
        if check_column_exists(cursor, 'Teacher', 'department'):
            try:
                cursor.execute("DROP INDEX IF EXISTS idx_teacher_department ON Teacher")
                print("  ✅ 删除索引 idx_teacher_department")
            except:
                pass
        
        # 删除 Admin 表的索引（如果有）
        if check_column_exists(cursor, 'Admin', 'department'):
            try:
                cursor.execute("DROP INDEX IF EXISTS idx_admin_department ON Admin")
                print("  ✅ 删除索引 idx_admin_department")
            except:
                pass
        
        # 删除 Admin 表的列
        print("\n修复 Admin 表...")
        if check_column_exists(cursor, 'Admin', 'name'):
            cursor.execute("ALTER TABLE Admin DROP COLUMN name")
            print("  ✅ 删除 Admin.name")
        if check_column_exists(cursor, 'Admin', 'department'):
            cursor.execute("ALTER TABLE Admin DROP COLUMN department")
            print("  ✅ 删除 Admin.department")
        
        # 删除 Student 表的列
        print("\n修复 Student 表...")
        if check_column_exists(cursor, 'Student', 'name'):
            cursor.execute("ALTER TABLE Student DROP COLUMN name")
            print("  ✅ 删除 Student.name")
        if check_column_exists(cursor, 'Student', 'gender'):
            cursor.execute("ALTER TABLE Student DROP COLUMN gender")
            print("  ✅ 删除 Student.gender")
        if check_column_exists(cursor, 'Student', 'department'):
            cursor.execute("ALTER TABLE Student DROP COLUMN department")
            print("  ✅ 删除 Student.department")
        if check_column_exists(cursor, 'Student', 'grade'):
            cursor.execute("ALTER TABLE Student DROP COLUMN grade")
            print("  ✅ 删除 Student.grade")
        if check_column_exists(cursor, 'Student', 'class_name'):
            cursor.execute("ALTER TABLE Student DROP COLUMN class_name")
            print("  ✅ 删除 Student.class_name")
        
        # 删除 Teacher 表的列
        print("\n修复 Teacher 表...")
        if check_column_exists(cursor, 'Teacher', 'name'):
            cursor.execute("ALTER TABLE Teacher DROP COLUMN name")
            print("  ✅ 删除 Teacher.name")
        if check_column_exists(cursor, 'Teacher', 'gender'):
            cursor.execute("ALTER TABLE Teacher DROP COLUMN gender")
            print("  ✅ 删除 Teacher.gender")
        if check_column_exists(cursor, 'Teacher', 'department'):
            cursor.execute("ALTER TABLE Teacher DROP COLUMN department")
            print("  ✅ 删除 Teacher.department")
        
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ 修复完成！")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 修复失败: {e}")
        raise

if __name__ == "__main__":
    main()
