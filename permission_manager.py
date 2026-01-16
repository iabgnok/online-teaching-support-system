# -*- coding: utf-8 -*-
"""
权限管理模块 - 权限装饰器、中间件和权限检查函数
"""

from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user
from models import Admin


class PermissionDeniedError(Exception):
    """权限拒绝异常"""
    def __init__(self, message="Permission denied", status_code=403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ==================== 权限装饰器 ====================

def api_login_required(f):
    """API 登录装饰器 - 返回 JSON 401"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """要求管理员角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def admin_permission_required(min_level):
    """要求特定权限等级
    
    等级说明：
    1 = 超级管理员 (最高权限)
    2 = 系统管理员
    3 = 部门管理员
    4 = 内容审核员 (最低权限)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            admin_profile = current_user.admin_profile
            if not admin_profile:
                return jsonify({'error': 'Admin profile not found'}), 403
            
            if admin_profile.permission_level > min_level:
                return jsonify({
                    'error': f'Insufficient permissions. Required level: {min_level}, Your level: {admin_profile.permission_level}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def feature_permission_required(*features):
    """要求特定功能权限
    
    Args:
        features: 功能权限名称列表，如 'forum_manage', 'user_manage' 等
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            admin_profile = current_user.admin_profile
            if not admin_profile:
                return jsonify({'error': 'Admin profile not found'}), 403
            
            # 检查所有要求的功能权限
            for feature in features:
                if not admin_profile.has_feature_permission(feature):
                    return jsonify({
                        'error': f'Permission denied: {feature}',
                        'required_permission': feature
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def forum_admin_required(f):
    """论坛管理员装饰器 - 要求论坛管理权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        admin_profile = current_user.admin_profile
        if not admin_profile or not admin_profile.can_manage_forum:
            return jsonify({'error': 'Forum management permission required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def content_reviewer_required(f):
    """内容审核员装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        admin_profile = current_user.admin_profile
        if not admin_profile or not admin_profile.can_review_content:
            return jsonify({'error': 'Content review permission required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== 权限检查函数 ====================

def check_admin_permission(permission_level):
    """检查管理员权限等级
    
    Args:
        permission_level: 所需的最低权限等级
        
    Returns:
        True 如果有权限, False 否则
    """
    if not current_user.is_authenticated or current_user.role != 'admin':
        return False
    
    admin_profile = current_user.admin_profile
    if not admin_profile:
        return False
    
    return admin_profile.permission_level <= permission_level


def check_feature_permission(feature):
    """检查特定功能权限
    
    Args:
        feature: 功能权限名称
        
    Returns:
        True 如果有权限, False 否则
    """
    if not current_user.is_authenticated or current_user.role != 'admin':
        return False
    
    admin_profile = current_user.admin_profile
    if not admin_profile:
        return False
    
    return admin_profile.has_feature_permission(feature)


def get_admin_permissions():
    """获取当前用户的所有权限
    
    Returns:
        权限信息字典，如果不是管理员返回 None
    """
    if not current_user.is_authenticated or current_user.role != 'admin':
        return None
    
    admin_profile = current_user.admin_profile
    if not admin_profile:
        return None
    
    return {
        'level': admin_profile.permission_level,
        'can_manage_users': admin_profile.can_manage_users,
        'can_manage_forum': admin_profile.can_manage_forum,
        'can_manage_courses': admin_profile.can_manage_courses,
        'can_manage_grades': admin_profile.can_manage_grades,
        'can_manage_announcements': admin_profile.can_manage_announcements,
        'can_review_content': admin_profile.can_review_content,
        'can_ban_users': admin_profile.can_ban_users,
    }


def require_admin_permission(permission_level):
    """作为函数调用的权限检查 (非装饰器)
    
    Args:
        permission_level: 所需的权限等级
        
    Raises:
        PermissionDeniedError: 如果没有权限
    """
    if not check_admin_permission(permission_level):
        raise PermissionDeniedError(
            f"Permission level {permission_level} required",
            403
        )


def require_feature_permission(*features):
    """作为函数调用的功能权限检查 (非装饰器)
    
    Args:
        features: 功能权限名称列表
        
    Raises:
        PermissionDeniedError: 如果没有所需权限
    """
    for feature in features:
        if not check_feature_permission(feature):
            raise PermissionDeniedError(
                f"Feature permission '{feature}' required",
                403
            )


# ==================== 权限初始化和管理 ====================

def init_admin_permissions(admin_profile, role_type='content_reviewer'):
    """初始化管理员权限
    
    Args:
        admin_profile: Admin 对象
        role_type: 角色类型 - 'super_admin', 'system_admin', 'dept_admin', 'content_reviewer'
    """
    if role_type == 'super_admin':
        admin_profile.permission_level = 1
        admin_profile.can_manage_users = True
        admin_profile.can_manage_forum = True
        admin_profile.can_manage_courses = True
        admin_profile.can_manage_grades = True
        admin_profile.can_manage_announcements = True
        admin_profile.can_review_content = True
        admin_profile.can_ban_users = True
        
    elif role_type == 'system_admin':
        admin_profile.permission_level = 2
        admin_profile.can_manage_users = True
        admin_profile.can_manage_forum = True
        admin_profile.can_manage_courses = True
        admin_profile.can_manage_grades = True
        admin_profile.can_manage_announcements = True
        admin_profile.can_review_content = True
        admin_profile.can_ban_users = True
        
    elif role_type == 'dept_admin':
        admin_profile.permission_level = 3
        admin_profile.can_manage_users = False
        admin_profile.can_manage_forum = True
        admin_profile.can_manage_courses = True
        admin_profile.can_manage_grades = False
        admin_profile.can_manage_announcements = True
        admin_profile.can_review_content = True
        admin_profile.can_ban_users = False
        
    elif role_type == 'content_reviewer':
        admin_profile.permission_level = 4
        admin_profile.can_manage_users = False
        admin_profile.can_manage_forum = False
        admin_profile.can_manage_courses = False
        admin_profile.can_manage_grades = False
        admin_profile.can_manage_announcements = False
        admin_profile.can_review_content = True
        admin_profile.can_ban_users = False


def get_permission_levels():
    """获取所有权限等级定义"""
    return {
        1: {
            'name': '超级管理员',
            'description': '最高权限，可管理所有功能',
            'features': ['user_manage', 'forum_manage', 'courses_manage', 'grades_manage', 'announcements_manage', 'content_review', 'ban_users']
        },
        2: {
            'name': '系统管理员',
            'description': '系统级管理权限',
            'features': ['user_manage', 'forum_manage', 'courses_manage', 'grades_manage', 'announcements_manage', 'content_review', 'ban_users']
        },
        3: {
            'name': '部门管理员',
            'description': '部门级管理权限',
            'features': ['forum_manage', 'courses_manage', 'announcements_manage', 'content_review']
        },
        4: {
            'name': '内容审核员',
            'description': '仅内容审核权限',
            'features': ['content_review']
        }
    }
