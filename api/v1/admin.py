"""管理员API模块 - 用户管理、数据导入、统计查询"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import (
    db, Users, Admin, Student, Teacher, Department, Course, TeachingClass,
    StudentClass, TeacherClass, Assignment, Submission, Grade, Material,
    Announcement, Attendance, AttendanceRecord,
    VAdminUserStatistics, VAdminCourseStatistics,
    generate_next_id
)
from datetime import datetime
import csv
import io
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

# ==================== 权限装饰器 ====================
def admin_required(f):
    """要求管理员角色（临时禁用认证检查）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 临时禁用认证检查
        # if not current_user.is_authenticated:
        #     return jsonify({'error': 'Authentication required'}), 401
        # if current_user.role != 'admin':
        #     return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_permission_required(min_level):
    """要求特定权限等级（1=最高，3=最低）（临时禁用认证检查）"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 临时禁用认证检查
            # if not current_user.is_authenticated:
            #     return jsonify({'error': 'Authentication required'}), 401
            # if current_user.role != 'admin':
            #     return jsonify({'error': 'Admin access required'}), 403
            # 
            # admin_profile = current_user.admin_profile
            # if not admin_profile:
            #     return jsonify({'error': 'Admin profile not found'}), 403
            # 
            # if admin_profile.permission_level > min_level:
            #     return jsonify({'error': f'Permission level {min_level} required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== 仪表盘API ====================
@admin_bp.route('/dashboard/stats', methods=['GET'])
# @login_required
@admin_required
def get_dashboard_stats():
    """获取管理员仪表盘统计数据"""
    try:
        # 用户统计
        user_stats = VAdminUserStatistics.query.all()
        admin_count = sum(s.total_admin_count for s in user_stats)
        teacher_count = sum(s.total_teacher_count for s in user_stats)
        student_count = sum(s.total_student_count for s in user_stats)
        
        # 课程统计
        course_stats = VAdminCourseStatistics.query.all()
        total_courses = len(course_stats)
        total_teaching_classes = sum(getattr(s, 'current_year_classes', 0) or getattr(s, 'total_class_count', 0) or 0 for s in course_stats)
        
        # 作业统计
        total_assignments = Assignment.query.count()
        total_submissions = Submission.query.count()
        
        # 考勤统计
        total_attendance_sessions = Attendance.query.count()
        
        # 最新公告
        latest_announcements = Announcement.query.filter_by(scope_type='global')\
            .order_by(Announcement.created_at.desc()).limit(5).all()
        
        return jsonify({
            'users': {
                'admins': admin_count,
                'teachers': teacher_count,
                'students': student_count,
                'total': admin_count + teacher_count + student_count
            },
            'courses': {
                'courses': total_courses,
                'teaching_classes': total_teaching_classes
            },
            'activities': {
                'assignments': total_assignments,
                'submissions': total_submissions,
                'attendance_sessions': total_attendance_sessions
            },
            'announcements': [{
                'id': a.id,
                'title': a.title,
                'content': a.content,
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'author': {
                    'id': a.author.user_id,
                    'name': a.author.real_name
                } if a.author else {'id': None, 'name': '系统'}
            } for a in latest_announcements],
            'user_stats_by_dept': [{
                'dept_name': s.dept_name or '未分配院系',
                'admins': s.total_admin_count,
                'teachers': s.total_teacher_count,
                'students': s.total_student_count
            } for s in user_stats]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 用户管理API ====================
@admin_bp.route('/users', methods=['GET'])
# # @login_required  # 临时禁用
@admin_permission_required(2)
def get_users():
    """获取用户列表（支持筛选和搜索）"""
    try:
        # 获取查询参数
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        search_name = request.args.get('search_name', '')
        search_username = request.args.get('search_username', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 构建查询
        query = Users.query
        
        if role:
            query = query.filter(Users.role == role)
        if status != '':
            query = query.filter(Users.status == int(status))
        if search_name:
            query = query.filter(Users.real_name.like(f'%{search_name}%'))
        if search_username:
            query = query.filter(Users.username.like(f'%{search_username}%'))
        
        # 添加默认排序（MSSQL分页必须）
        query = query.order_by(Users.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # 构建响应数据
        users_data = []
        for user in users:
            user_data = {
                'user_id': user.user_id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role,
                'status': user.status,
                'phone': user.phone or '',
                'email': user.email or '',
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            
            # 添加角色特定信息（安全处理）
            try:
                if user.role == 'admin' and user.admin_profile:
                    user_data['admin'] = {
                        'admin_no': user.admin_profile.admin_no or '',
                        'permission_level': user.admin_profile.permission_level or 3,
                        'dept_id': user.admin_profile.dept_id,
                        'dept_name': user.admin_profile.department.dept_name if user.admin_profile.department else None
                    }
                elif user.role == 'teacher' and user.teacher_profile:
                    user_data['teacher'] = {
                        'teacher_no': user.teacher_profile.teacher_no or '',
                        'title': user.teacher_profile.title or '',
                        'dept_id': user.teacher_profile.dept_id,
                        'dept_name': user.teacher_profile.department.dept_name if user.teacher_profile.department else None
                    }
                elif user.role == 'student' and user.student_profile:
                    user_data['student'] = {
                        'student_no': user.student_profile.student_no or '',
                        'major': user.student_profile.major or '',
                        'dept_id': user.student_profile.dept_id,
                        'dept_name': user.student_profile.department.dept_name if user.student_profile.department else None
                    }
            except Exception as profile_error:
                print(f"Error loading profile for user {user.user_id}: {profile_error}")
            
            users_data.append(user_data)
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        current_app.logger.error(f"Failed to get users: {e}")
        current_app.logger.error(f"Traceback: {error_detail}")
        print(f"ERROR in get_users: {e}")
        print(f"ERROR Traceback:\n{error_detail}")
        return jsonify({'error': str(e), 'detail': error_detail}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
# @login_required
@admin_required
def get_user_detail(user_id):
    """获取用户详细信息"""
    try:
        user = db.session.get(Users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role,
            'status': user.status,
            'phone': user.phone,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        # 角色特定信息
        if user.role == 'admin' and user.admin_profile:
            profile = user.admin_profile
            user_data['profile'] = {
                'admin_no': profile.admin_no,
                'permission_level': profile.permission_level,
                'dept_id': profile.dept_id,
                'dept_name': profile.department.dept_name if profile.department else None
            }
        elif user.role == 'teacher' and user.teacher_profile:
            profile = user.teacher_profile
            user_data['profile'] = {
                'teacher_no': profile.teacher_no,
                'title': profile.title,
                'dept_id': profile.dept_id,
                'dept_name': profile.department.dept_name if profile.department else None
            }
        elif user.role == 'student' and user.student_profile:
            profile = user.student_profile
            user_data['profile'] = {
                'student_no': profile.student_no,
                'major': profile.major,
                'dept_id': profile.dept_id,
                'dept_name': profile.department.dept_name if profile.department else None
            }
        
        return jsonify(user_data)
    except Exception as e:
        current_app.logger.error(f"Failed to get user detail: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
# @login_required
@admin_required
def create_user():
    """创建新用户"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'password', 'real_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 检查用户名是否已存在
        if Users.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # 创建Users记录
        new_user_id = generate_next_id(Users, 'user_id')
        new_user = Users(
            user_id=new_user_id,
            username=data['username'],
            real_name=data['real_name'],
            phone=data.get('phone'),
            email=data.get('email'),
            role=data['role'],
            status=1
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        
        # 根据角色创建对应profile
        if data['role'] == 'admin':
            if not data.get('admin_no'):
                return jsonify({'error': 'admin_no is required for admin role'}), 400
            
            if Admin.query.filter_by(admin_no=data['admin_no']).first():
                return jsonify({'error': 'admin_no already exists'}), 400
            
            # 检查是否为首个管理员
            is_first_admin = db.session.query(db.func.count(Admin.admin_id)).scalar() == 0
            
            dept_id = data.get('dept_id')
            if data.get('dept_name') and not dept_id:
                dept = Department.query.filter_by(dept_name=data['dept_name']).first()
                if not dept:
                    dept = Department(
                        dept_id=generate_next_id(Department, 'dept_id'),
                        dept_name=data['dept_name']
                    )
                    db.session.add(dept)
                    db.session.flush()
                dept_id = dept.dept_id
            
            new_admin = Admin(
                admin_id=generate_next_id(Admin, 'admin_id'),
                user_id=new_user_id,
                admin_no=data['admin_no'],
                dept_id=dept_id,
                permission_level=1 if is_first_admin else int(data.get('permission_level', 3))
            )
            db.session.add(new_admin)
            
        elif data['role'] == 'teacher':
            if not data.get('teacher_no'):
                return jsonify({'error': 'teacher_no is required for teacher role'}), 400
            
            if Teacher.query.filter_by(teacher_no=data['teacher_no']).first():
                return jsonify({'error': 'teacher_no already exists'}), 400
            
            dept_id = data.get('dept_id')
            if data.get('dept_name') and not dept_id:
                dept = Department.query.filter_by(dept_name=data['dept_name']).first()
                if not dept:
                    dept = Department(
                        dept_id=generate_next_id(Department, 'dept_id'),
                        dept_name=data['dept_name']
                    )
                    db.session.add(dept)
                    db.session.flush()
                dept_id = dept.dept_id
            
            new_teacher = Teacher(
                teacher_id=generate_next_id(Teacher, 'teacher_id'),
                user_id=new_user_id,
                teacher_no=data['teacher_no'],
                dept_id=dept_id,
                title=data.get('title')
            )
            db.session.add(new_teacher)
            
        elif data['role'] == 'student':
            if not data.get('student_no'):
                return jsonify({'error': 'student_no is required for student role'}), 400
            
            if Student.query.filter_by(student_no=data['student_no']).first():
                return jsonify({'error': 'student_no already exists'}), 400
            
            dept_id = data.get('dept_id')
            if data.get('dept_name') and not dept_id:
                dept = Department.query.filter_by(dept_name=data['dept_name']).first()
                if not dept:
                    dept = Department(
                        dept_id=generate_next_id(Department, 'dept_id'),
                        dept_name=data['dept_name']
                    )
                    db.session.add(dept)
                    db.session.flush()
                dept_id = dept.dept_id
            
            new_student = Student(
                student_id=generate_next_id(Student, 'student_id'),
                user_id=new_user_id,
                student_no=data['student_no'],
                dept_id=dept_id,
                major=data.get('major')
            )
            db.session.add(new_student)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': new_user_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create user: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
# @login_required
@admin_required
def update_user(user_id):
    """更新用户信息"""
    try:
        user = db.session.get(Users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # 更新Users基本信息
        if 'username' in data and data['username'] != user.username:
            if Users.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 400
            user.username = data['username']
        
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        # 更新角色特定信息
        if user.role == 'admin' and user.admin_profile:
            profile = user.admin_profile
            if 'admin_no' in data and data['admin_no'] != profile.admin_no:
                if Admin.query.filter_by(admin_no=data['admin_no']).first():
                    return jsonify({'error': 'admin_no already exists'}), 400
                profile.admin_no = data['admin_no']
            if 'permission_level' in data:
                profile.permission_level = int(data['permission_level'])
            if 'dept_id' in data:
                profile.dept_id = data['dept_id']
                
        elif user.role == 'teacher' and user.teacher_profile:
            profile = user.teacher_profile
            if 'teacher_no' in data and data['teacher_no'] != profile.teacher_no:
                if Teacher.query.filter_by(teacher_no=data['teacher_no']).first():
                    return jsonify({'error': 'teacher_no already exists'}), 400
                profile.teacher_no = data['teacher_no']
            if 'title' in data:
                profile.title = data['title']
            if 'dept_id' in data:
                profile.dept_id = data['dept_id']
                
        elif user.role == 'student' and user.student_profile:
            profile = user.student_profile
            if 'student_no' in data and data['student_no'] != profile.student_no:
                if Student.query.filter_by(student_no=data['student_no']).first():
                    return jsonify({'error': 'student_no already exists'}), 400
                profile.student_no = data['student_no']
            if 'major' in data:
                profile.major = data['major']
            if 'dept_id' in data:
                profile.dept_id = data['dept_id']
        
        db.session.commit()
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update user: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
# @login_required
@admin_required
def toggle_user_status(user_id):
    """切换用户状态（激活/禁用）"""
    try:
        user = db.session.get(Users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 不能禁用自己（如果有当前用户信息）
        if current_user.is_authenticated and hasattr(current_user, 'user_id'):
            if user.user_id == current_user.user_id:
                return jsonify({'error': 'Cannot disable current user'}), 400
        
        # 不能禁用超级管理员
        if user.role == 'admin' and user.admin_profile:
            super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
            if user.admin_profile.admin_id == super_admin_id:
                return jsonify({'error': 'Cannot disable super admin'}), 400
        
        user.status = 1 - user.status
        db.session.commit()
        
        return jsonify({
            'message': 'User status toggled successfully',
            'status': user.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to toggle user status: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
# @login_required
@admin_permission_required(2)
def delete_user(user_id):
    """删除用户及相关数据"""
    try:
        user = db.session.get(Users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 不能删除自己
        if user.user_id == current_user.user_id:
            return jsonify({'error': 'Cannot delete current user'}), 400
        
        role = user.role
        
        # 删除角色特定数据
        if role == 'student':
            student = user.student_profile
            if student:
                StudentClass.query.filter_by(student_id=student.student_id).delete()
                Submission.query.filter_by(student_id=student.student_id).delete()
                Grade.query.filter_by(student_id=student.student_id).delete()
                AttendanceRecord.query.filter_by(student_id=student.student_id).delete()
                db.session.delete(student)
                
        elif role == 'teacher':
            teacher = user.teacher_profile
            if teacher:
                # 删除作业及其提交记录
                assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id).all()
                for assignment in assignments:
                    Submission.query.filter_by(assignment_id=assignment.assignment_id).delete()
                    db.session.delete(assignment)
                
                # 删除教学资料
                materials = Material.query.filter_by(teacher_id=teacher.teacher_id).all()
                for material in materials:
                    if material.file_path:
                        file_path = os.path.join(current_app.config.get('MATERIALS_FOLDER', 'uploads/materials'), 
                                               material.file_path)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                    db.session.delete(material)
                
                TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).delete()
                Grade.query.filter_by(calculated_by=teacher.teacher_id).update({'calculated_by': None})
                Submission.query.filter_by(graded_by=teacher.teacher_id).update({'graded_by': None})
                db.session.delete(teacher)
                
        elif role == 'admin':
            admin = user.admin_profile
            if admin:
                # 不能删除超级管理员
                super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
                if admin.admin_id == super_admin_id:
                    return jsonify({'error': 'Cannot delete super admin'}), 400
                db.session.delete(admin)
        
        # 删除用户记录
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete user: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 院系管理API ====================
@admin_bp.route('/departments', methods=['GET'])
@admin_required
# @login_required
def get_departments():
    """获取所有院系"""
    try:
        departments = Department.query.all()
        return jsonify({
            'departments': [{
                'dept_id': d.dept_id,
                'dept_name': d.dept_name
            } for d in departments]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get departments: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 批量数据导入API ====================
@admin_bp.route('/import/users', methods=['POST'])
# @login_required
@admin_permission_required(2)
def import_users():
    """批量导入用户（CSV）"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400
        
        # 读取CSV
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # 验证必填字段
                username = row.get('username', '').strip()
                password = row.get('password', '').strip()
                real_name = row.get('real_name', '').strip()
                role = row.get('role', '').strip()
                
                if not all([username, password, real_name, role]):
                    errors.append(f"Row {row_num}: Missing required fields")
                    error_count += 1
                    continue
                
                # 检查用户名是否已存在
                if Users.query.filter_by(username=username).first():
                    errors.append(f"Row {row_num}: Username '{username}' already exists")
                    error_count += 1
                    continue
                
                # 创建用户
                new_user_id = generate_next_id(Users, 'user_id')
                new_user = Users(
                    user_id=new_user_id,
                    username=username,
                    real_name=real_name,
                    phone=row.get('phone', '').strip() or None,
                    email=row.get('email', '').strip() or None,
                    role=role,
                    status=1
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.flush()
                
                # 根据角色创建profile
                if role == 'admin':
                    admin_no = row.get('admin_no', '').strip()
                    if not admin_no or Admin.query.filter_by(admin_no=admin_no).first():
                        errors.append(f"Row {row_num}: Invalid or duplicate admin_no")
                        error_count += 1
                        db.session.rollback()
                        continue
                    
                    dept_name = row.get('department', '').strip()
                    dept_id = None
                    if dept_name:
                        dept = Department.query.filter_by(dept_name=dept_name).first()
                        if not dept:
                            dept = Department(
                                dept_id=generate_next_id(Department, 'dept_id'),
                                dept_name=dept_name
                            )
                            db.session.add(dept)
                            db.session.flush()
                        dept_id = dept.dept_id
                    
                    new_admin = Admin(
                        admin_id=generate_next_id(Admin, 'admin_id'),
                        user_id=new_user_id,
                        admin_no=admin_no,
                        dept_id=dept_id,
                        permission_level=int(row.get('permission_level', 3))
                    )
                    db.session.add(new_admin)
                    
                elif role == 'teacher':
                    teacher_no = row.get('teacher_no', '').strip()
                    if not teacher_no or Teacher.query.filter_by(teacher_no=teacher_no).first():
                        errors.append(f"Row {row_num}: Invalid or duplicate teacher_no")
                        error_count += 1
                        db.session.rollback()
                        continue
                    
                    dept_name = row.get('department', '').strip()
                    dept_id = None
                    if dept_name:
                        dept = Department.query.filter_by(dept_name=dept_name).first()
                        if not dept:
                            dept = Department(
                                dept_id=generate_next_id(Department, 'dept_id'),
                                dept_name=dept_name
                            )
                            db.session.add(dept)
                            db.session.flush()
                        dept_id = dept.dept_id
                    
                    new_teacher = Teacher(
                        teacher_id=generate_next_id(Teacher, 'teacher_id'),
                        user_id=new_user_id,
                        teacher_no=teacher_no,
                        dept_id=dept_id,
                        title=row.get('title', '').strip() or None
                    )
                    db.session.add(new_teacher)
                    
                elif role == 'student':
                    student_no = row.get('student_no', '').strip()
                    if not student_no or Student.query.filter_by(student_no=student_no).first():
                        errors.append(f"Row {row_num}: Invalid or duplicate student_no")
                        error_count += 1
                        db.session.rollback()
                        continue
                    
                    dept_name = row.get('department', '').strip()
                    dept_id = None
                    if dept_name:
                        dept = Department.query.filter_by(dept_name=dept_name).first()
                        if not dept:
                            dept = Department(
                                dept_id=generate_next_id(Department, 'dept_id'),
                                dept_name=dept_name
                            )
                            db.session.add(dept)
                            db.session.flush()
                        dept_id = dept.dept_id
                    
                    new_student = Student(
                        student_id=generate_next_id(Student, 'student_id'),
                        user_id=new_user_id,
                        student_no=student_no,
                        dept_id=dept_id,
                        major=row.get('major', '').strip() or None
                    )
                    db.session.add(new_student)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
                db.session.rollback()
        
        if success_count > 0:
            db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {success_count} success, {error_count} errors',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:20]  # 限制返回前20个错误
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to import users: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/import/departments', methods=['POST'])
# @login_required
@admin_permission_required(2)
def import_departments():
    """批量导入院系"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                dept_name = row.get('dept_name', '').strip()
                if not dept_name:
                    errors.append(f"Row {row_num}: dept_name is required")
                    error_count += 1
                    continue
                
                if Department.query.filter_by(dept_name=dept_name).first():
                    errors.append(f"Row {row_num}: Department '{dept_name}' already exists")
                    error_count += 1
                    continue
                
                new_dept = Department(
                    dept_id=generate_next_id(Department, 'dept_id'),
                    dept_name=dept_name
                )
                db.session.add(new_dept)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
        
        if success_count > 0:
            db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {success_count} success, {error_count} errors',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to import departments: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/import/courses', methods=['POST'])
# @login_required
@admin_permission_required(2)
def import_courses():
    """批量导入课程"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                course_code = row.get('course_code', '').strip()
                course_name = row.get('course_name', '').strip()
                
                if not all([course_code, course_name]):
                    errors.append(f"Row {row_num}: Missing required fields")
                    error_count += 1
                    continue
                
                if Course.query.filter_by(course_code=course_code).first():
                    errors.append(f"Row {row_num}: Course '{course_code}' already exists")
                    error_count += 1
                    continue
                
                new_course = Course(
                    course_id=generate_next_id(Course, 'course_id'),
                    course_code=course_code,
                    course_name=course_name,
                    credits=float(row.get('credits', 0)) if row.get('credits') else None,
                    description=row.get('description', '').strip() or None
                )
                db.session.add(new_course)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
        
        if success_count > 0:
            db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {success_count} success, {error_count} errors',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to import courses: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 统计查询API ====================
@admin_bp.route('/stats/courses', methods=['GET'])
@admin_required
# @login_required
def get_course_stats():
    """获取课程统计"""
    try:
        course_stats = VAdminCourseStatistics.query.all()
        
        return jsonify({
            'stats': [{
                'course_code': s.course_code,
                'course_name': s.course_name,
                'teaching_class_count': s.current_year_classes or s.total_class_count or 0,
                'total_student_count': s.active_enrollments or s.total_enrollments or 0,
                'assignment_count': 0  # 如果需要，可以单独查询
            } for s in course_stats]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get course stats: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats/users', methods=['GET'])
@admin_required
# @login_required
def get_user_stats():
    """获取用户统计（按院系）"""
    try:
        user_stats = VAdminUserStatistics.query.all()
        
        return jsonify({
            'stats': [{
                'dept_name': s.dept_name or '未分配院系',
                'admin_count': s.total_admin_count,
                'teacher_count': s.total_teacher_count,
                'student_count': s.total_student_count,
                'total_count': s.total_admin_count + s.total_teacher_count + s.total_student_count
            } for s in user_stats]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get user stats: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/query/users', methods=['POST'])
@admin_required
# @login_required
def query_users():
    """综合用户查询"""
    try:
        data = request.get_json()
        
        query = Users.query
        
        if data.get('username'):
            query = query.filter(Users.username.like(f"%{data['username']}%"))
        if data.get('real_name'):
            query = query.filter(Users.real_name.like(f"%{data['real_name']}%"))
        if data.get('role'):
            query = query.filter(Users.role == data['role'])
        if data.get('status') is not None:
            query = query.filter(Users.status == int(data['status']))
        
        users = query.all()
        
        return jsonify({
            'results': [{
                'user_id': u.user_id,
                'username': u.username,
                'real_name': u.real_name,
                'role': u.role,
                'status': u.status,
                'phone': u.phone,
                'email': u.email
            } for u in users]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to query users: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/query/courses', methods=['POST'])
@admin_required
# @login_required
def query_courses():
    """综合课程查询"""
    try:
        data = request.get_json()
        
        query = Course.query
        
        if data.get('course_code'):
            query = query.filter(Course.course_code.like(f"%{data['course_code']}%"))
        if data.get('course_name'):
            query = query.filter(Course.course_name.like(f"%{data['course_name']}%"))
        
        courses = query.all()
        
        return jsonify({
            'results': [{
                'course_id': c.course_id,
                'course_code': c.course_code,
                'course_name': c.course_name,
                'credits': c.credits,
                'description': c.description
            } for c in courses]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to query courses: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 权限管理API ====================
@admin_bp.route('/permissions', methods=['GET'])
# @login_required
@admin_permission_required(1)
def get_admin_permissions():
    """获取所有管理员权限（需要最高权限）"""
    try:
        admins = Admin.query.join(Users).all()
        
        return jsonify({
            'admins': [{
                'admin_id': a.admin_id,
                'admin_no': a.admin_no,
                'user': {
                    'user_id': a.user.user_id,
                    'username': a.user.username,
                    'real_name': a.user.real_name
                },
                'permission_level': a.permission_level,
                'dept_name': a.department.dept_name if a.department else None
            } for a in admins]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get admin permissions: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/permissions/<int:admin_id>', methods=['PUT'])
# @login_required
@admin_permission_required(1)
def update_admin_permission(admin_id):
    """更新管理员权限等级"""
    try:
        admin = db.session.get(Admin, admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # 不能修改超级管理员
        super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
        if admin.admin_id == super_admin_id:
            return jsonify({'error': 'Cannot modify super admin permissions'}), 400
        
        data = request.get_json()
        
        if 'permission_level' in data:
            new_level = int(data['permission_level'])
            if new_level not in [1, 2, 3]:
                return jsonify({'error': 'Permission level must be 1, 2, or 3'}), 400
            admin.permission_level = new_level
        
        db.session.commit()
        
        return jsonify({
            'message': 'Permission updated successfully',
            'permission_level': admin.permission_level
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update admin permission: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 课程与教学班管理API ====================
@admin_bp.route('/courses', methods=['GET'])
# @login_required
@admin_required
def get_courses():
    """获取所有课程"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = Course.query
        if search:
            query = query.filter(
                db.or_(
                    Course.course_code.like(f'%{search}%'),
                    Course.course_name.like(f'%{search}%')
                )
            )
        
        # Add order by
        query = query.order_by(Course.course_code.asc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'courses': [{
                'course_id': c.course_id,
                'course_code': c.course_code,
                'course_name': c.course_name,
                'credits': c.credits,
                'description': c.description
            } for c in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get courses: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/teaching-classes', methods=['GET'])
# @login_required
@admin_required
def get_teaching_classes():
    """获取所有教学班"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = TeachingClass.query.order_by(TeachingClass.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        classes_data = []
        for tc in pagination.items:
            # 统计选课人数
            student_count = StudentClass.query.filter_by(class_id=tc.class_id).count()
            # 统计任课教师数
            teacher_count = TeacherClass.query.filter_by(class_id=tc.class_id).count()
            
            classes_data.append({
                'class_id': tc.class_id,
                'class_name': tc.class_name,
                'course': {
                    'course_id': tc.course.course_id,
                    'course_code': tc.course.course_code,
                    'course_name': tc.course.course_name
                } if tc.course else None,
                'semester': tc.semester,
                'schedule': tc.schedule,
                'location': tc.location,
                'student_count': student_count,
                'teacher_count': teacher_count
            })
        
        return jsonify({
            'teaching_classes': classes_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get teaching classes: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/export/users', methods=['GET'])
# @login_required
@admin_required
def export_users():
    """导出用户数据为CSV"""
    try:
        role = request.args.get('role', '')
        
        query = Users.query
        if role:
            query = query.filter(Users.role == role)
        
        users = query.all()
        
        # 创建CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入头部
        writer.writerow(['用户ID', '用户名', '真实姓名', '角色', '状态', '电话', '邮箱', '创建时间'])
        
        # 写入数据
        for user in users:
            writer.writerow([
                user.user_id,
                user.username,
                user.real_name,
                user.role,
                '激活' if user.status == 1 else '禁用',
                user.phone or '',
                user.email or '',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
            ])
        
        # 设置响应
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Failed to export users: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 权限管理 API ====================

@admin_bp.route('/admins', methods=['GET'])
@admin_permission_required(1)
def get_admins():
    """获取所有管理员列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        permission_level = request.args.get('permission_level', type=int)
        
        query = Admin.query
        
        if permission_level is not None:
            query = query.filter_by(permission_level=permission_level)
        
        paginated = query.order_by(Admin.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        admins = []
        for admin in paginated.items:
            admins.append({
                'admin_id': admin.admin_id,
                'user_id': admin.user_id,
                'admin_no': admin.admin_no,
                'real_name': admin.user.real_name if admin.user else '',
                'permission_level': admin.permission_level,
                'permissions': {
                    'can_manage_users': admin.can_manage_users,
                    'can_manage_forum': admin.can_manage_forum,
                    'can_manage_courses': admin.can_manage_courses,
                    'can_manage_grades': admin.can_manage_grades,
                    'can_manage_announcements': admin.can_manage_announcements,
                    'can_review_content': admin.can_review_content,
                    'can_ban_users': admin.can_ban_users
                },
                'created_at': admin.created_at.isoformat() if admin.created_at else None
            })
        
        return jsonify({
            'admins': admins,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get admins: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>/permissions', methods=['GET'])
@admin_permission_required(2)
def get_single_admin_permissions(admin_id):
    """获取管理员的权限详情"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        
        return jsonify({
            'admin_id': admin.admin_id,
            'admin_no': admin.admin_no,
            'real_name': admin.user.real_name if admin.user else '',
            'permission_level': admin.permission_level,
            'level_name': {1: '超级管理员', 2: '系统管理员', 3: '部门管理员', 4: '内容审核员'}.get(admin.permission_level, '未知'),
            'permissions': {
                'can_manage_users': admin.can_manage_users,
                'can_manage_forum': admin.can_manage_forum,
                'can_manage_courses': admin.can_manage_courses,
                'can_manage_grades': admin.can_manage_grades,
                'can_manage_announcements': admin.can_manage_announcements,
                'can_review_content': admin.can_review_content,
                'can_ban_users': admin.can_ban_users
            }
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get admin permissions: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>/permissions', methods=['PUT'])
@admin_permission_required(1)
def update_admin_permissions(admin_id):
    """更新管理员权限"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json()
        
        # 更新权限等级
        if 'permission_level' in data:
            admin.permission_level = int(data['permission_level'])
        
        # 更新具体权限
        permissions_map = {
            'can_manage_users': 'can_manage_users',
            'can_manage_forum': 'can_manage_forum',
            'can_manage_courses': 'can_manage_courses',
            'can_manage_grades': 'can_manage_grades',
            'can_manage_announcements': 'can_manage_announcements',
            'can_review_content': 'can_review_content',
            'can_ban_users': 'can_ban_users'
        }
        
        for key, attr in permissions_map.items():
            if key in data:
                setattr(admin, attr, bool(data[key]))
        
        db.session.commit()
        
        return jsonify({'message': 'Admin permissions updated'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update admin permissions: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>/role', methods=['PUT'])
@admin_permission_required(1)
def set_admin_role(admin_id):
    """设置管理员角色类型"""
    try:
        from permission_manager import init_admin_permissions
        
        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json()
        
        role_type = data.get('role_type')  # 'super_admin', 'system_admin', 'dept_admin', 'content_reviewer'
        if not role_type:
            return jsonify({'error': 'role_type is required'}), 400
        
        init_admin_permissions(admin, role_type)
        db.session.commit()
        
        return jsonify({'message': 'Admin role updated'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to set admin role: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>/grant-permission', methods=['POST'])
@admin_permission_required(1)
def grant_admin_permission(admin_id):
    """授予管理员特定权限"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json()
        
        feature = data.get('feature')  # 功能权限名称
        if not feature:
            return jsonify({'error': 'feature is required'}), 400
        
        admin.grant_permission(feature)
        db.session.commit()
        
        return jsonify({'message': f'Permission {feature} granted'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to grant permission: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>/revoke-permission', methods=['POST'])
@admin_permission_required(1)
def revoke_admin_permission(admin_id):
    """撤销管理员特定权限"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json()
        
        feature = data.get('feature')  # 功能权限名称
        if not feature:
            return jsonify({'error': 'feature is required'}), 400
        
        admin.revoke_permission(feature)
        db.session.commit()
        
        return jsonify({'message': f'Permission {feature} revoked'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to revoke permission: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/permission-levels', methods=['GET'])
@admin_required
def get_permission_levels():
    """获取权限等级定义"""
    try:
        from permission_manager import get_permission_levels
        
        levels = get_permission_levels()
        
        return jsonify(levels), 200
    except Exception as e:
        current_app.logger.error(f"Failed to get permission levels: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/my-permissions', methods=['GET'])
@admin_permission_required(4)
def get_my_permissions():
    """获取当前管理员的权限信息"""
    try:
        if current_user.role != 'admin' or not current_user.admin_profile:
            return jsonify({'error': 'Not an admin'}), 403
        
        admin = current_user.admin_profile
        
        level_names = {
            1: '超级管理员',
            2: '系统管理员',
            3: '部门管理员',
            4: '内容审核员'
        }
        
        return jsonify({
            'admin_id': admin.admin_id,
            'admin_no': admin.admin_no,
            'real_name': current_user.real_name,
            'permission_level': admin.permission_level,
            'level_name': level_names.get(admin.permission_level, '未知'),
            'permissions': {
                'can_manage_users': admin.can_manage_users,
                'can_manage_forum': admin.can_manage_forum,
                'can_manage_courses': admin.can_manage_courses,
                'can_manage_grades': admin.can_manage_grades,
                'can_manage_announcements': admin.can_manage_announcements,
                'can_review_content': admin.can_review_content,
                'can_ban_users': admin.can_ban_users
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Failed to get my permissions: {e}")
        return jsonify({'error': str(e)}), 500
