#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化管理员权限脚本
为所有管理员赋予论坛管理和权限管理权限
"""

from app import app, db
from models import Admin
from permission_manager import init_admin_permissions

def initialize_permissions():
    """为所有管理员初始化权限"""
    with app.app_context():
        try:
            # 获取所有管理员
            admins = Admin.query.all()
            
            if not admins:
                print("❌ 未找到管理员记录")
                return False
            
            print(f"✓ 找到 {len(admins)} 个管理员账户")
            
            for admin in admins:
                # 获取用户信息
                user = admin.user  # 通过关系获取用户对象
                user_name = user.real_name if user else "未知"
                
                # 为第一个管理员设置为超级管理员
                if admin.admin_id == admins[0].admin_id:
                    role_type = 'super_admin'
                    print(f"\n✓ 初始化 {admin.admin_no} ({user_name}) 为超级管理员")
                else:
                    # 其他管理员设置为系统管理员
                    role_type = 'system_admin'
                    print(f"✓ 初始化 {admin.admin_no} ({user_name}) 为系统管理员")
                
                # 调用初始化函数
                init_admin_permissions(admin, role_type)
                
                # 显示权限信息
                print(f"  - 权限等级: {admin.permission_level}")
                print(f"  - 论坛管理: {admin.can_manage_forum}")
                print(f"  - 用户管理: {admin.can_manage_users}")
                print(f"  - 课程管理: {admin.can_manage_courses}")
                print(f"  - 成绩管理: {admin.can_manage_grades}")
                print(f"  - 公告管理: {admin.can_manage_announcements}")
                print(f"  - 内容审核: {admin.can_review_content}")
                print(f"  - 封禁用户: {admin.can_ban_users}")
            
            # 提交更改
            db.session.commit()
            print("\n✅ 管理员权限初始化成功！")
            print("\n现在所有管理员都可以访问论坛管理功能了。")
            print("请重新登录以获取新的权限。")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("管理员权限初始化工具")
    print("=" * 50)
    initialize_permissions()
