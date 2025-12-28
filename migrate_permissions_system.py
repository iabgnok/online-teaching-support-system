"""
数据库权限系统迁移脚本

功能：
1. 创建 Permission 和 AdminPermission 表
2. 初始化默认权限数据
3. 将现有的 permission_level 数据迁移到新的权限系统
4. 保留旧的 permission_level 字段以确保向后兼容

使用方法：
    python migrate_permissions_system.py
"""

from app import app, db
from models import Admin, Permission, AdminPermission
from sqlalchemy import text

def create_tables():
    """创建新的权限相关表"""
    print("=" * 60)
    print("步骤 1: 创建 Permission 和 AdminPermission 表")
    print("=" * 60)
    
    with app.app_context():
        # 创建表（如果不存在）
        db.create_all()
        print("✓ 表创建成功")

def init_permissions():
    """初始化默认权限数据"""
    print("\n" + "=" * 60)
    print("步骤 2: 初始化默认权限")
    print("=" * 60)
    
    # 定义系统权限
    permissions_data = [
        {
            'permission_name': 'permission_management',
            'display_name': '权限管理',
            'description': '管理其他管理员的权限，包括授予和撤销权限'
        },
        {
            'permission_name': 'user_management',
            'display_name': '用户管理',
            'description': '创建、编辑、删除用户（学生、教师、管理员）'
        },
        {
            'permission_name': 'data_import',
            'display_name': '数据导入',
            'description': '批量导入用户、课程、班级等数据'
        },
        {
            'permission_name': 'query_all',
            'display_name': '全局查询',
            'description': '查询所有用户、课程、成绩等信息'
        },
        {
            'permission_name': 'course_management',
            'display_name': '课程管理',
            'description': '管理课程信息，包括创建、编辑、删除课程'
        },
        {
            'permission_name': 'class_management',
            'display_name': '班级管理',
            'description': '管理教学班级，包括创建、编辑、删除班级'
        },
        {
            'permission_name': 'department_management',
            'display_name': '部门管理',
            'description': '管理部门信息'
        }
    ]
    
    with app.app_context():
        created_count = 0
        existing_count = 0
        
        for perm_data in permissions_data:
            # 检查权限是否已存在
            existing_perm = Permission.query.filter_by(
                permission_name=perm_data['permission_name']
            ).first()
            
            if existing_perm:
                print(f"  ⊙ 权限已存在: {perm_data['display_name']} ({perm_data['permission_name']})")
                existing_count += 1
            else:
                # 创建新权限
                new_permission = Permission(
                    permission_name=perm_data['permission_name'],
                    display_name=perm_data['display_name'],
                    description=perm_data['description']
                )
                db.session.add(new_permission)
                print(f"  ✓ 创建权限: {perm_data['display_name']} ({perm_data['permission_name']})")
                created_count += 1
        
        db.session.commit()
        print(f"\n权限初始化完成: 创建 {created_count} 个，已存在 {existing_count} 个")

def migrate_permission_levels():
    """将现有的 permission_level 迁移到新的权限系统"""
    print("\n" + "=" * 60)
    print("步骤 3: 迁移现有权限数据")
    print("=" * 60)
    
    # 定义权限级别到权限名称的映射
    level_to_permissions = {
        1: [  # 最高权限（超级管理员）
            'permission_management',
            'user_management',
            'data_import',
            'query_all',
            'course_management',
            'class_management',
            'department_management'
        ],
        2: [  # 中级权限（用户管理员）
            'user_management',
            'data_import',
            'query_all',
            'course_management',
            'class_management'
        ],
        3: [  # 一般权限（查询管理员）
            'query_all'
        ]
    }
    
    with app.app_context():
        # 获取所有管理员
        admins = Admin.query.all()
        print(f"找到 {len(admins)} 个管理员账户")
        
        migrated_count = 0
        skipped_count = 0
        
        for admin in admins:
            print(f"\n处理管理员: {admin.name} (ID: {admin.admin_id}, 权限级别: {admin.permission_level})")
            
            # 检查该管理员是否已有权限（避免重复迁移）
            existing_permissions = admin.permissions.count()
            if existing_permissions > 0:
                print(f"  ⊙ 跳过：该管理员已有 {existing_permissions} 个权限")
                skipped_count += 1
                continue
            
            # 根据 permission_level 授予相应权限
            permission_level = admin.permission_level if admin.permission_level else 3
            permission_names = level_to_permissions.get(permission_level, level_to_permissions[3])
            
            for perm_name in permission_names:
                permission = Permission.query.filter_by(permission_name=perm_name).first()
                if permission:
                    # 创建权限关联
                    admin_perm = AdminPermission(
                        admin_id=admin.admin_id,
                        permission_id=permission.permission_id,
                        granted_by=None  # 系统迁移，没有授予者
                    )
                    db.session.add(admin_perm)
                    print(f"  ✓ 授予权限: {permission.display_name}")
            
            migrated_count += 1
        
        db.session.commit()
        print(f"\n迁移完成: 处理 {migrated_count} 个管理员，跳过 {skipped_count} 个")

def verify_migration():
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("步骤 4: 验证迁移结果")
    print("=" * 60)
    
    with app.app_context():
        # 统计权限数量
        total_permissions = Permission.query.count()
        total_admin_permissions = AdminPermission.query.count()
        
        print(f"权限表记录数: {total_permissions}")
        print(f"管理员权限关联记录数: {total_admin_permissions}")
        
        # 显示每个管理员的权限
        admins = Admin.query.all()
        print(f"\n管理员权限分配情况:")
        print("-" * 60)
        
        for admin in admins:
            permissions = admin.get_all_permissions()
            perm_names = [p.display_name for p in permissions]
            print(f"{admin.name} (级别 {admin.permission_level}): {', '.join(perm_names) if perm_names else '无权限'}")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("数据库权限系统迁移")
    print("=" * 60)
    
    try:
        # 步骤 1: 创建表
        create_tables()
        
        # 步骤 2: 初始化权限
        init_permissions()
        
        # 步骤 3: 迁移数据
        migrate_permission_levels()
        
        # 步骤 4: 验证结果
        verify_migration()
        
        print("\n" + "=" * 60)
        print("✓ 迁移成功完成！")
        print("=" * 60)
        print("\n说明：")
        print("1. 旧的 permission_level 字段已保留，可用于向后兼容")
        print("2. 新的权限系统通过 AdminPermission 表管理")
        print("3. 推荐使用 has_permission(permission_name='xxx') 方法检查权限")
        print("4. 可以通过 admin.grant_permission() 和 admin.revoke_permission() 管理权限")
        
    except Exception as e:
        print(f"\n✗ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
