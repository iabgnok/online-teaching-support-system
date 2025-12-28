"""
清理新权限系统的数据库表

功能：删除 Permission 和 AdminPermission 表
说明：由于已回滚到旧的权限系统，需要清理数据库中遗留的表

使用方法：
    python cleanup_permission_tables.py
"""

from app import app, db
from sqlalchemy import text

def cleanup_permission_tables():
    """删除新权限系统的数据库表"""
    print("=" * 60)
    print("清理新权限系统的数据库表")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 删除 AdminPermission 表（先删除，因为有外键依赖）
            print("\n检查并删除 AdminPermission 表...")
            db.session.execute(text("""
                IF OBJECT_ID('dbo.AdminPermission', 'U') IS NOT NULL
                BEGIN
                    DROP TABLE dbo.AdminPermission;
                    PRINT '✓ AdminPermission 表已删除';
                END
                ELSE
                BEGIN
                    PRINT '⊙ AdminPermission 表不存在';
                END
            """))
            
            # 删除 Permission 表
            print("\n检查并删除 Permission 表...")
            db.session.execute(text("""
                IF OBJECT_ID('dbo.Permission', 'U') IS NOT NULL
                BEGIN
                    DROP TABLE dbo.Permission;
                    PRINT '✓ Permission 表已删除';
                END
                ELSE
                BEGIN
                    PRINT '⊙ Permission 表不存在';
                END
            """))
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✓ 清理完成！")
            print("=" * 60)
            print("\n说明：")
            print("- AdminPermission 表已删除")
            print("- Permission 表已删除")
            print("- Admin 表的 permission_level 字段保持不变")
            print("- 系统继续使用简单的权限级别（1-3）")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 清理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def verify_cleanup():
    """验证清理结果"""
    print("\n" + "=" * 60)
    print("验证清理结果")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 检查表是否还存在
            result = db.session.execute(text("""
                SELECT 
                    CASE WHEN OBJECT_ID('dbo.AdminPermission', 'U') IS NOT NULL THEN 1 ELSE 0 END AS AdminPermission_exists,
                    CASE WHEN OBJECT_ID('dbo.Permission', 'U') IS NOT NULL THEN 1 ELSE 0 END AS Permission_exists,
                    CASE WHEN OBJECT_ID('dbo.Admin', 'U') IS NOT NULL THEN 1 ELSE 0 END AS Admin_exists
            """))
            
            row = result.fetchone()
            
            print("\n表存在状态：")
            print(f"  Admin 表: {'✓ 存在' if row[2] else '✗ 不存在（异常！）'}")
            print(f"  Permission 表: {'✗ 仍存在（需要清理）' if row[1] else '✓ 已删除'}")
            print(f"  AdminPermission 表: {'✗ 仍存在（需要清理）' if row[0] else '✓ 已删除'}")
            
            if row[0] == 0 and row[1] == 0 and row[2] == 1:
                print("\n✓ 清理成功！数据库状态正常。")
                return True
            else:
                print("\n⚠ 清理可能不完整，请检查。")
                return False
                
        except Exception as e:
            print(f"\n✗ 验证失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("新权限系统数据库表清理工具")
    print("=" * 60)
    print("\n⚠ 警告：此操作将删除以下表：")
    print("  - dbo.Permission")
    print("  - dbo.AdminPermission")
    print("\n这些表中的数据将永久丢失！")
    
    # 确认操作
    confirm = input("\n是否继续？(输入 yes 确认): ")
    if confirm.lower() != 'yes':
        print("\n操作已取消。")
        return False
    
    # 执行清理
    success = cleanup_permission_tables()
    
    if success:
        # 验证结果
        verify_cleanup()
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
