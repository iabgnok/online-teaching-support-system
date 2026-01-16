#!/usr/bin/env python
"""
权限管理和论坛管理功能恢复验证脚本
验证所有必要的文件和配置都已正确部署
"""

import os
import sys
import json

def check_file_exists(path):
    """检查文件是否存在"""
    return os.path.exists(path)

def check_file_content(path, keyword):
    """检查文件是否包含特定关键字"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            return keyword in content
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return False

def main():
    print("=" * 60)
    print("权限管理和论坛管理功能恢复验证")
    print("=" * 60)
    
    checks = []
    
    # 检查前端文件
    print("\n📋 前端文件检查:")
    
    frontend_files = {
        'frontend/src/views/admin/PermissionManagement.vue': '权限管理',
        'frontend/src/views/admin/ForumManagement.vue': '论坛管理',
    }
    
    for file_path, name in frontend_files.items():
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {name} ({file_path})")
        checks.append(('frontend', name, exists))
    
    # 检查后端文件
    print("\n🔧 后端文件检查:")
    
    backend_files = {
        'permission_manager.py': '权限管理模块',
        'api/v1/forum_management.py': '论坛管理API',
    }
    
    for file_path, name in backend_files.items():
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {name} ({file_path})")
        checks.append(('backend', name, exists))
    
    # 检查router配置
    print("\n📍 路由配置检查:")
    
    router_path = 'frontend/src/router/index.js'
    has_permission_route = check_file_content(router_path, 'PermissionManagement')
    has_forum_route = check_file_content(router_path, 'ForumManagement')
    
    print(f"  {'✅' if has_permission_route else '❌'} 权限管理路由已配置")
    print(f"  {'✅' if has_forum_route else '❌'} 论坛管理路由已配置")
    
    checks.append(('routing', '权限管理路由', has_permission_route))
    checks.append(('routing', '论坛管理路由', has_forum_route))
    
    # 检查AdminDashboard菜单
    print("\n🏠 管理后台菜单检查:")
    
    dashboard_path = 'frontend/src/views/admin/AdminDashboard.vue'
    has_permission_menu = check_file_content(dashboard_path, '/admin/permissions')
    has_forum_menu = check_file_content(dashboard_path, '/admin/forum-management')
    
    print(f"  {'✅' if has_permission_menu else '❌'} 权限管理菜单已添加")
    print(f"  {'✅' if has_forum_menu else '❌'} 论坛管理菜单已添加")
    
    checks.append(('menu', '权限管理菜单', has_permission_menu))
    checks.append(('menu', '论坛管理菜单', has_forum_menu))
    
    # 检查app.py蓝图注册
    print("\n⚙️ 后端蓝图注册检查:")
    
    app_path = 'app.py'
    has_forum_import = check_file_content(app_path, 'from api.v1.forum_management')
    has_forum_register = check_file_content(app_path, 'register_blueprint(forum_mgmt_bp)')
    
    print(f"  {'✅' if has_forum_import else '❌'} 论坛管理蓝图已导入")
    print(f"  {'✅' if has_forum_register else '❌'} 论坛管理蓝图已注册")
    
    checks.append(('blueprint', '蓝图导入', has_forum_import))
    checks.append(('blueprint', '蓝图注册', has_forum_register))
    
    # 总结
    print("\n" + "=" * 60)
    total_checks = len(checks)
    passed_checks = sum(1 for _, _, result in checks if result)
    
    print(f"检查总数: {total_checks}")
    print(f"通过: {passed_checks}")
    print(f"失败: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        print("\n✅ 所有检查都已通过！功能恢复完成。")
        return 0
    else:
        print(f"\n⚠️ 有 {total_checks - passed_checks} 项检查未通过，请检查配置。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
