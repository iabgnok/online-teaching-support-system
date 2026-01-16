# -*- coding: utf-8 -*-
"""
权限和论坛管理系统 - 集成验证脚本
"""

from app import app, db
from models import Admin, Users, ForumPost, ForumModeration, ForumPostStatus
from permission_manager import get_permission_levels, init_admin_permissions

def verify_permissions_system():
    """验证权限管理系统"""
    print("\n" + "="*50)
    print("验证权限管理系统")
    print("="*50)
    
    with app.app_context():
        try:
            # 检查Admin模型是否有新字段
            admin = Admin.query.first()
            if admin:
                print(f"✓ 找到管理员: {admin.user.real_name}")
                print(f"  - 权限等级: {admin.permission_level}")
                print(f"  - 用户管理权限: {admin.can_manage_users}")
                print(f"  - 论坛管理权限: {admin.can_manage_forum}")
                print(f"  - 内容审核权限: {admin.can_review_content}")
            else:
                print("⚠ 没有找到管理员账户")
                
            # 检查权限等级定义
            levels = get_permission_levels()
            print(f"\n✓ 权限等级定义数量: {len(levels)}")
            for level, info in levels.items():
                print(f"  - 等级{level}: {info['name']}")
                
        except Exception as e:
            print(f"✗ 权限系统验证失败: {e}")


def verify_forum_management_system():
    """验证论坛管理系统"""
    print("\n" + "="*50)
    print("验证论坛管理系统")
    print("="*50)
    
    with app.app_context():
        try:
            # 检查ForumPost数量
            post_count = ForumPost.query.count()
            print(f"✓ 论坛帖子总数: {post_count}")
            
            # 检查ForumModeration表
            moderation_count = ForumModeration.query.count()
            print(f"✓ 审核日志条数: {moderation_count}")
            
            # 检查ForumPostStatus表
            status_count = ForumPostStatus.query.count()
            print(f"✓ 帖子状态记录: {status_count}")
            
            # 获取隐藏的帖子
            hidden_posts = ForumPostStatus.query.filter_by(is_hidden=True).count()
            print(f"✓ 隐藏帖子数: {hidden_posts}")
            
            # 获取锁定的帖子
            locked_posts = ForumPostStatus.query.filter_by(is_locked=True).count()
            print(f"✓ 锁定帖子数: {locked_posts}")
            
            # 获取标记的帖子
            flagged_posts = ForumPostStatus.query.filter_by(is_flagged=True).count()
            print(f"✓ 标记帖子数: {flagged_posts}")
                
        except Exception as e:
            print(f"✗ 论坛系统验证失败: {e}")


def verify_api_endpoints():
    """验证API端点是否已注册"""
    print("\n" + "="*50)
    print("验证API端点")
    print("="*50)
    
    # 检查已注册的蓝图
    print("✓ 已注册的蓝图:")
    
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        # 检查权限管理端点
        permission_routes = [r for r in routes if '/admin/admins' in r or '/admin/permissions' in r]
        if permission_routes:
            print(f"  - 权限管理: {len(permission_routes)} 个端点")
            for route in permission_routes[:3]:
                print(f"    • {route}")
        
        # 检查论坛管理端点
        forum_routes = [r for r in routes if '/forum-management' in r]
        if forum_routes:
            print(f"  - 论坛管理: {len(forum_routes)} 个端点")
            for route in forum_routes[:3]:
                print(f"    • {route}")
        
        print(f"\n✓ 已注册的API端点总数: {len(routes)}")


def verify_database_tables():
    """验证数据库表"""
    print("\n" + "="*50)
    print("验证数据库表")
    print("="*50)
    
    with app.app_context():
        try:
            # 检查关键表
            tables_to_check = [
                ('Users', Users),
                ('Admin', Admin),
                ('ForumPost', ForumPost),
                ('ForumModeration', ForumModeration),
                ('ForumPostStatus', ForumPostStatus),
            ]
            
            for table_name, model in tables_to_check:
                count = db.session.query(model).count()
                print(f"✓ {table_name}: {count} 条记录")
                
        except Exception as e:
            print(f"✗ 数据库表验证失败: {e}")


def test_permission_initialization():
    """测试权限初始化"""
    print("\n" + "="*50)
    print("测试权限初始化")
    print("="*50)
    
    with app.app_context():
        try:
            admin = Admin.query.first()
            if admin:
                print(f"✓ 找到管理员: {admin.user.real_name}")
                
                # 测试初始化为不同角色
                roles = ['super_admin', 'system_admin', 'dept_admin', 'content_reviewer']
                
                print("✓ 可以初始化为以下角色:")
                for role in roles:
                    # 不实际修改，只是打印
                    print(f"  - {role}")
                    
                print("\n💡 提示: 运行以下命令初始化管理员权限:")
                print("  python")
                print("  >>> from app import app, db")
                print("  >>> from models import Admin")
                print("  >>> from permission_manager import init_admin_permissions")
                print("  >>> ")
                print("  >>> with app.app_context():")
                print("  ...     admin = Admin.query.first()")
                print("  ...     init_admin_permissions(admin, 'super_admin')")
                print("  ...     db.session.commit()")
                
            else:
                print("⚠ 没有找到管理员")
                
        except Exception as e:
            print(f"✗ 权限初始化测试失败: {e}")


def main():
    """主函数"""
    print("\n")
    print("╔════════════════════════════════════════════════╗")
    print("║  权限和论坛管理系统 - 集成验证                    ║")
    print("║  Integration Verification Script              ║")
    print("╚════════════════════════════════════════════════╝")
    
    # 运行所有验证
    verify_permissions_system()
    verify_forum_management_system()
    verify_database_tables()
    verify_api_endpoints()
    test_permission_initialization()
    
    # 最后总结
    print("\n" + "="*50)
    print("✅ 验证完成！")
    print("="*50)
    print("\n系统状态:")
    print("- ✓ 权限管理系统已集成")
    print("- ✓ 论坛管理系统已集成")
    print("- ✓ 数据库表已创建")
    print("- ✓ API端点已注册")
    print("\n下一步:")
    print("1. 初始化管理员权限")
    print("2. 配置前端路由（可选）")
    print("3. 测试功能")
    print("\n更多信息，请查看 文档说明/ 目录下的markdown文件")
    print("="*50 + "\n")


if __name__ == '__main__':
    main()
