"""在线教学支持系统 - 主应用"""

# ==================== 导入依赖 ====================
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, make_response    
from functools import wraps
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager, login_user, logout_user, current_user, login_required 
from config import DevelopmentConfig
import csv
import io
from datetime import datetime
import os
from werkzeug.utils import secure_filename  
from models import (
    Users, Admin, Student, Teacher, Course, TeachingClass, StudentClass, TeacherClass, 
    Assignment, Submission, Grade, Material, Department, db,
    # 视图模型
    VStudentMyCourses, VStudentMyAssignments, VStudentMyGrades,
    VTeacherMyClasses, VTeacherStudentList, VTeacherSubmissionStatus,
    VAdminUserStatistics, VAdminCourseStatistics
)

# ==================== 应用初始化 ====================
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# ==================== 扩展初始化 ====================
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# 确保上传目录存在
os.makedirs(app.config['MATERIALS_FOLDER'], exist_ok=True)
os.makedirs(app.config['ASSIGNMENTS_FOLDER'], exist_ok=True)

# ----------------------- 辅助函数 -----------------------

def generate_next_id(model, id_field='id'):
    """生成模型的下一个ID"""
    max_id = db.session.query(db.func.max(getattr(model, id_field))).scalar()
    return (max_id or 0) + 1

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_or_create_department(dept_name):
    """获取或创建部门，返回部门ID"""
    if not dept_name or dept_name.strip() == '':
        return None
    
    from models import Department
    dept = Department.query.filter_by(dept_name=dept_name).first()
    if dept:
        return dept.dept_id
    
    new_dept = Department(
        dept_id=generate_next_id(Department, 'dept_id'),
        dept_name=dept_name
    )
    db.session.add(new_dept)
    db.session.flush()
    return new_dept.dept_id 


# ==================== 成绩计算辅助函数 ====================

def calculate_student_grade(student_id, class_id):
    """
    实时计算学生成绩（不写入数据库）
    返回: {
        'homework_avg': float,
        'exam_avg': float, 
        'current_score': float,  # 按默认公式计算的总分
        'has_homework': bool,
        'has_exam': bool
    }
    """
    # 获取该班级的所有作业和考试
    all_homeworks = Assignment.query.filter_by(class_id=class_id, type='homework', status=1).all()
    all_exams = Assignment.query.filter_by(class_id=class_id, type='exam', status=1).all()
    
    # 计算作业平均分
    homework_avg = 0.0
    if all_homeworks:
        homework_scores = []
        for hw in all_homeworks:
            submission = Submission.query.filter_by(
                assignment_id=hw.assignment_id,
                student_id=student_id
            ).first()
            
            if submission and submission.status == 'graded' and submission.score is not None:
                homework_scores.append(float(submission.score))
            else:
                homework_scores.append(0.0)
        
        homework_avg = sum(homework_scores) / len(homework_scores) if homework_scores else 0.0
    
    # 计算考试平均分
    exam_avg = 0.0
    if all_exams:
        exam_scores = []
        for exam in all_exams:
            submission = Submission.query.filter_by(
                assignment_id=exam.assignment_id,
                student_id=student_id
            ).first()
            
            if submission and submission.status == 'graded' and submission.score is not None:
                exam_scores.append(float(submission.score))
            else:
                exam_scores.append(0.0)
        
        exam_avg = sum(exam_scores) / len(exam_scores) if exam_scores else 0.0
    
    # 按默认公式计算总分（作业30% + 考试50% + 教师评价20%）
    # 这里教师评价默认为0，实际计算时会从表单获取
    current_score = homework_avg * 0.3 + exam_avg * 0.5
    
    return {
        'homework_avg': round(homework_avg, 2),
        'exam_avg': round(exam_avg, 2),
        'current_score': round(current_score, 2),
        'has_homework': len(all_homeworks) > 0,
        'has_exam': len(all_exams) > 0
    }


def get_student_grade_display(student_id, class_id):
    """
    获取学生成绩显示（优先显示已归档成绩，否则实时计算）
    返回: {
        'homework_avg': float,
        'exam_avg': float,
        'teacher_evaluation': float,
        'final_grade': float,
        'is_finalized': bool,
        'finalized_at': datetime or None,
        'calculated_by': Teacher or None,
        'remarks': str or None
    }
    """
    # 查询数据库中的成绩记录
    grade = Grade.query.filter_by(student_id=student_id, class_id=class_id).first()
    
    if grade and grade.is_finalized:
        # 返回已归档的成绩
        return {
            'homework_avg': float(grade.homework_avg) if grade.homework_avg else 0.0,
            'exam_avg': float(grade.exam_avg) if grade.exam_avg else 0.0,
            'teacher_evaluation': float(grade.teacher_evaluation) if grade.teacher_evaluation else 0.0,
            'final_grade': float(grade.final_grade) if grade.final_grade else 0.0,
            'is_finalized': True,
            'finalized_at': grade.finalized_at,
            'calculated_by': grade.calculator if grade.calculated_by else None,
            'remarks': grade.remarks,
            'calculation_formula': grade.calculation_formula
        }
    else:
        # 实时计算临时成绩
        calc_result = calculate_student_grade(student_id, class_id)
        teacher_eval = float(grade.teacher_evaluation) if (grade and grade.teacher_evaluation) else 0.0
        
        # 计算总分
        final = calc_result['homework_avg'] * 0.3 + calc_result['exam_avg'] * 0.5 + teacher_eval * 0.2
        
        return {
            'homework_avg': calc_result['homework_avg'],
            'exam_avg': calc_result['exam_avg'],
            'teacher_evaluation': teacher_eval,
            'final_grade': round(final, 2),
            'is_finalized': False,
            'finalized_at': None,
            'calculated_by': None,
            'remarks': grade.remarks if grade else None,
            'calculation_formula': None
        }


# ==================== Flask-Login 配置 ====================

@login_manager.user_loader
def load_user(user_id):
    """加载用户对象"""
    user = db.session.get(Users, user_id)
    if user and user.status == 0:
        return None
    return user 

def role_required(role):
    """角色权限装饰器：限制特定角色访问"""
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash(f'您没有权限访问 {role} 页面。', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def admin_permission_required(level):
    """管理员权限装饰器：检查权限级别（数字越小权限越高）"""
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != 'admin':
                flash('您不是管理员，无法访问此页面。', 'danger')
                abort(403)
            admin = current_user.admin_profile
            if not admin or not admin.has_permission(level):
                flash(f'您的权限不足，需要级别 {level} 或更高权限。', 'danger')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ==================== 用户认证路由 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        
        if user is None or not user.verify_password(password):
            flash('用户名或密码错误。', 'danger')
            return redirect(url_for('login'))

        if user.status == 0:
            flash('您的账户已被禁用，无法登录。请联系管理员。', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已安全退出。', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not current_user.check_password(old_password):
            flash('旧密码不正确！', 'danger')
        elif len(new_password) < 6:
            flash('新密码长度不能少于6位！', 'danger')
        elif new_password != confirm_password:
            flash('两次输入的新密码不一致！', 'danger')
        elif new_password == old_password:
            flash('新密码不能与旧密码相同！', 'warning')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功！请使用新密码重新登录。', 'success')
            logout_user()
            return redirect(url_for('login'))
        
        return redirect(url_for('change_password'))
    
    return render_template('change_password.html', title='修改密码')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    if current_user.role == 'admin':
        flash('管理员不支持此功能！', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        if email and '@' not in email:
            flash('邮箱格式不正确！', 'danger')
            return redirect(url_for('edit_profile'))
        
        current_user.phone = phone or None
        current_user.email = email or None
        db.session.commit()
        flash('个人资料更新成功！', 'success')
        
        dashboard = 'student_dashboard' if current_user.role == 'student' else 'teacher_dashboard'
        return redirect(url_for(dashboard))
    
    return render_template('edit_profile.html', title='编辑个人资料')


@app.route('/')
@login_required
def index():
    """首页：根据角色跳转到相应的仪表板"""
    role_dashboards = {
        'student': 'student_dashboard',
        'teacher': 'teacher_dashboard',
        'admin': 'admin_dashboard'
    }
    dashboard = role_dashboards.get(current_user.role, 'logout')
    return redirect(url_for(dashboard))


# ==================== 管理员路由 ====================

@app.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    """管理员主页"""
    admin = current_user.admin_profile
    permission_level = admin.permission_level if admin else 3
    return render_template('admin_dashboard.html', 
                         user=current_user, 
                         title='管理员主页',
                         permission_level=permission_level)


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_permission_required(2)
def admin_user_management():
    """用户管理（需要中级权限）"""
    
    # 获取筛选条件
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search_name = request.args.get('search_name', '')
    search_username = request.args.get('search_username', '')
    
    # 构建查询
    query = Users.query
    
    if role_filter:
        query = query.filter(Users.role == role_filter)
    if status_filter:
        query = query.filter(Users.status == int(status_filter))
    if search_name:
        query = query.filter(Users.real_name.like(f'%{search_name}%'))
    if search_username:
        query = query.filter(Users.username.like(f'%{search_username}%'))
    
    users = query.all()
    
    # 使用视图获取统计数据（按院系统计）
    user_stats = VAdminUserStatistics.query.all()
    admin_count = sum(s.total_admin_count for s in user_stats)
    teacher_count = sum(s.total_teacher_count for s in user_stats)
    student_count = sum(s.total_student_count for s in user_stats)
    
    return render_template('admin_user_management.html', 
                           users=users,
                           admin_count=admin_count,
                           teacher_count=teacher_count,
                           student_count=student_count,
                           user_stats=user_stats,
                           role_filter=role_filter,
                           status_filter=status_filter,
                           search_name=search_name,
                           search_username=search_username,
                           title="用户管理")


@app.route('/admin/user/toggle_status/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_toggle_status(user_id):
    """切换用户状态（激活/禁用）"""
    user = db.session.get(Users, user_id)
    
    if not user:
        flash('未找到该用户。', 'danger')
    elif user.user_id == current_user.user_id:
        flash('无法禁用当前登录用户。', 'danger')
    elif user.role == 'admin' and user.admin_profile:
        # 禁止禁用系统超级管理员
        super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
        if user.admin_profile.admin_id == super_admin_id:
            flash('❌ 无法禁用系统超级管理员！', 'danger')
            return redirect(url_for('admin_user_management'))
    else:
        user.status = 1 - user.status
        db.session.commit()
        status_text = "激活" if user.status == 1 else "禁用"
        flash(f'用户 {user.username} 的状态已更新为 {status_text}。', 'success')
    
    return redirect(url_for('admin_user_management'))


@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
@admin_permission_required(2)
def admin_delete_user(user_id):
    """管理员：删除用户（真实删除，不可恢复）"""
    user = db.session.get(Users, user_id)
    
    if not user:
        flash('未找到该用户。', 'danger')
        return redirect(url_for('admin_user_management'))
    
    if user.user_id == current_user.user_id:
        flash('无法删除当前登录用户。', 'danger')
        return redirect(url_for('admin_user_management'))
    
    try:
        username = user.username
        real_name = user.real_name
        role = user.role
        
        # 根据角色删除关联数据
        if role == 'student':
            student = user.student_profile
            if student:
                # 删除学生的选课记录
                StudentClass.query.filter_by(student_id=student.student_id).delete()
                # 删除学生的提交记录
                Submission.query.filter_by(student_id=student.student_id).delete()
                # 删除学生的成绩记录
                Grade.query.filter_by(student_id=student.student_id).delete()
                # 删除学生记录
                db.session.delete(student)
        
        elif role == 'teacher':
            teacher = user.teacher_profile
            if teacher:
                # 获取教师创建的所有作业
                assignments = Assignment.query.filter_by(teacher_id=teacher.teacher_id).all()
                for assignment in assignments:
                    # 删除作业的所有提交记录
                    Submission.query.filter_by(assignment_id=assignment.assignment_id).delete()
                    # 删除作业
                    db.session.delete(assignment)
                
                # 删除教师上传的教学资料
                materials = Material.query.filter_by(teacher_id=teacher.teacher_id).all()
                for material in materials:
                    # 删除物理文件
                    if material.file_path:
                        file_path = os.path.join(app.config['MATERIALS_FOLDER'], material.file_path)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                    db.session.delete(material)
                
                # 删除教师任课记录
                TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).delete()
                
                # 将该教师计算的成绩的 calculated_by 设为 NULL
                Grade.query.filter_by(calculated_by=teacher.teacher_id).update({'calculated_by': None})
                
                # 将该教师批改的提交记录的 graded_by 设为 NULL
                Submission.query.filter_by(graded_by=teacher.teacher_id).update({'graded_by': None})
                
                # 删除教师记录
                db.session.delete(teacher)
        
        elif role == 'admin':
            admin = user.admin_profile
            if admin:
                # 禁止删除系统核心超级管理员（第一位被导入的管理员，admin_id 最小）
                super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
                if admin.admin_id == super_admin_id:
                    flash('❌ 无法删除系统超级管理员！', 'danger')
                    return redirect(url_for('admin_user_management'))
                
                # 删除管理员记录
                db.session.delete(admin)
        
        # 删除用户记录
        db.session.delete(user)
        db.session.commit()
        
        flash(f'✅ 用户「{real_name}」({username}) 及所有相关数据已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除用户失败: {e}")
        flash(f'❌ 删除失败：{e}', 'danger')
    
    return redirect(url_for('admin_user_management'))


@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_user(user_id):
    """管理员：编辑用户信息"""
    user = db.session.get(Users, user_id)
    
    if not user:
        flash('未找到该用户。', 'danger')
        return redirect(url_for('admin_user_management'))
    
    # 获取角色特定信息
    role_profile = None
    if user.role == 'admin':
        role_profile = user.admin_profile
    elif user.role == 'teacher':
        role_profile = user.teacher_profile
    elif user.role == 'student':
        role_profile = user.student_profile
    
    if request.method == 'POST':
        try:
            # 更新 Users 表基本信息
            new_username = request.form.get('username')
            
            # 检查用户名是否被其他用户占用
            if new_username != user.username:
                existing_user = Users.query.filter_by(username=new_username).first()
                if existing_user:
                    flash(f'用户名 {new_username} 已被占用。', 'danger')
                    return redirect(url_for('admin_edit_user', user_id=user_id))
            
            user.username = new_username
            user.real_name = request.form.get('real_name')
            user.phone = request.form.get('phone')
            user.email = request.form.get('email')
            
            # 如果提供了新密码，则更新密码
            new_password = request.form.get('password')
            if new_password and new_password.strip():
                user.set_password(new_password)
            
            # 更新角色特定信息
            if user.role == 'admin' and role_profile:
                new_admin_no = request.form.get('role_no')
                # 检查工号是否被占用
                if new_admin_no != role_profile.admin_no:
                    existing = Admin.query.filter_by(admin_no=new_admin_no).first()
                    if existing:
                        flash(f'管理员编号 {new_admin_no} 已被占用。', 'danger')
                        return redirect(url_for('admin_edit_user', user_id=user_id))
                
                role_profile.admin_no = new_admin_no
                # name 字段已删除，通过 user.real_name 获取
                # 处理部门
                dept_name = request.form.get('department')
                if dept_name:
                    role_profile.dept_id = get_or_create_department(dept_name)
                
            elif user.role == 'teacher' and role_profile:
                new_teacher_no = request.form.get('role_no')
                # 检查工号是否被占用
                if new_teacher_no != role_profile.teacher_no:
                    existing = Teacher.query.filter_by(teacher_no=new_teacher_no).first()
                    if existing:
                        flash(f'教师工号 {new_teacher_no} 已被占用。', 'danger')
                        return redirect(url_for('admin_edit_user', user_id=user_id))
                
                role_profile.teacher_no = new_teacher_no
                # name 字段已删除，通过 user.real_name 获取
                # 处理部门
                dept_name = request.form.get('department')
                if dept_name:
                    role_profile.dept_id = get_or_create_department(dept_name)
                role_profile.title = request.form.get('title')
                
            elif user.role == 'student' and role_profile:
                new_student_no = request.form.get('role_no')
                # 检查学号是否被占用
                if new_student_no != role_profile.student_no:
                    existing = Student.query.filter_by(student_no=new_student_no).first()
                    if existing:
                        flash(f'学号 {new_student_no} 已被占用。', 'danger')
                        return redirect(url_for('admin_edit_user', user_id=user_id))
                
                role_profile.student_no = new_student_no
                # name、grade、class_name 字段已删除
                # 处理部门
                dept_name = request.form.get('department')
                if dept_name:
                    role_profile.dept_id = get_or_create_department(dept_name)
                role_profile.major = request.form.get('major')
                # grade 和 class_name 已从 Student 表中删除
            
            db.session.commit()
            flash(f'✅ 用户 {user.username} 的信息已更新成功！', 'success')
            return redirect(url_for('admin_user_management'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"更新用户信息失败: {e}")
            flash(f'更新失败，请检查数据格式。错误详情: {e}', 'danger')
            return redirect(url_for('admin_edit_user', user_id=user_id))
    
    # GET 请求：显示编辑表单
    return render_template('admin_edit_user.html',
                          user=current_user,
                          edit_user=user,
                          role_profile=role_profile,
                          title='编辑用户信息')


@app.route('/admin/create/user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_create_user():
    """管理员创建用户账户的路由（支持创建管理员、教师、学生）"""
    title = '创建用户账户'
    
    if request.method == 'POST':
        # 1. 获取 Users 表数据
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')  # admin, teacher, student
        
        # --- 基本数据验证 ---
        if not all([username, password, real_name, role]):
            flash('用户名、密码、真实姓名和角色不能为空。', 'danger')
            return redirect(url_for('admin_create_user'))

        if Users.query.filter_by(username=username).first():
            flash(f'创建失败：用户名 {username} 已存在。', 'danger')
            return redirect(url_for('admin_create_user'))
            
        try:
            new_user_id = generate_next_id(Users, 'user_id')
            
            # 创建 Users 记录
            new_user = Users(
                user_id=new_user_id,
                username=username,
                real_name=real_name,
                phone=phone,
                email=email,
                role=role, 
                status=1 
            )
            new_user.set_password(password)
            db.session.add(new_user)

            # 根据角色创建对应的角色表记录
            if role == 'admin':
                admin_no = request.form.get('admin_no')
                permission_level = request.form.get('permission_level', 3)
                if not admin_no:
                    flash('管理员编号不能为空。', 'danger')
                    return redirect(url_for('admin_create_user'))
                if Admin.query.filter_by(admin_no=admin_no).first():
                    flash(f'创建失败：管理员编号 {admin_no} 已存在。', 'danger')
                    return redirect(url_for('admin_create_user'))
                
                dept_id = get_or_create_department(request.form.get('department')) if request.form.get('department') else None
                
                # 检查是否为系统中首个管理员
                is_first_admin = db.session.query(db.func.count(Admin.admin_id)).scalar() == 0
                
                new_admin = Admin(
                    admin_id=generate_next_id(Admin, 'admin_id'),
                    user_id=new_user_id,
                    admin_no=admin_no,
                    dept_id=dept_id,
                    permission_level=1 if is_first_admin else int(permission_level)
                )
                db.session.add(new_admin)
                if is_first_admin:
                    flash(f'✅ 系统首位管理员 {real_name} 已自动设为核心超级管理员（一级权限）。', 'success')
                else:
                    flash(f'✅ 管理员账户 {real_name} (编号: {admin_no}) 创建成功！', 'success')
                
            elif role == 'teacher':
                teacher_no = request.form.get('teacher_no')
                
                if not teacher_no:
                    flash('教师工号不能为空。', 'danger')
                    return redirect(url_for('admin_create_user'))
                if Teacher.query.filter_by(teacher_no=teacher_no).first():
                    flash(f'创建失败：教师工号 {teacher_no} 已存在。', 'danger')
                    return redirect(url_for('admin_create_user'))
                
                dept_id = get_or_create_department(request.form.get('department')) if request.form.get('department') else None
                
                new_teacher = Teacher(
                    teacher_id=generate_next_id(Teacher, 'teacher_id'),
                    user_id=new_user_id,
                    teacher_no=teacher_no,
                    dept_id=dept_id,
                    title=request.form.get('title')
                )
                db.session.add(new_teacher)
                flash(f'✅ 教师账户 {real_name} (工号: {teacher_no}) 创建成功！', 'success')
                
            elif role == 'student':
                student_no = request.form.get('student_no')
                
                if not student_no:
                    flash('学生学号不能为空。', 'danger')
                    return redirect(url_for('admin_create_user'))
                if Student.query.filter_by(student_no=student_no).first():
                    flash(f'创建失败：学生学号 {student_no} 已存在。', 'danger')
                    return redirect(url_for('admin_create_user'))
                
                dept_id = get_or_create_department(request.form.get('department')) if request.form.get('department') else None
                
                new_student = Student(
                    student_id=generate_next_id(Student, 'student_id'),
                    user_id=new_user_id,
                    student_no=student_no,
                    dept_id=dept_id,
                    major=request.form.get('major')
                )
                db.session.add(new_student)
                flash(f'✅ 学生账户 {real_name} (学号: {student_no}) 创建成功！', 'success')
            
            # 提交事务
            db.session.commit()
            return redirect(url_for('admin_user_management')) 

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"创建用户失败: {e}") 
            flash(f'创建用户失败，请检查数据格式或联系管理员。错误详情: {e}', 'danger')
            return redirect(url_for('admin_create_user'))

    # GET 请求：显示表单
    return render_template('admin_create_user.html', 
                           title=title, 
                           user=current_user)


# 保留旧路由以兼容性（重定向到新路由）
@app.route('/admin/create/teacher', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_create_teacher():
    """重定向到新的创建用户路由"""
    return redirect(url_for('admin_create_user'))


@app.route('/admin/permissions', methods=['GET', 'POST'])
@login_required
@admin_permission_required(1)
def admin_permissions():
    """管理员权限管理页面（需要最高权限）"""
    # 确定系统中的超级管理员（第一位被导入的管理员，admin_id 最小）
    super_admin_id = db.session.query(db.func.min(Admin.admin_id)).scalar()
    
    if request.method == 'POST':
        admin_id = request.form.get('admin_id', type=int)
        new_permission = request.form.get('permission_level')
        
        admin = db.session.get(Admin, admin_id)
        if admin:
            # 检查是否是超级管理员
            if admin_id == super_admin_id:
                flash('超级管理员的权限无法被修改！', 'danger')
            # 不能修改自己的权限
            elif admin.user_id == current_user.user_id:
                flash('不能修改自己的权限！', 'danger')
            else:
                old_level = admin.permission_level
                admin.permission_level = int(new_permission)
                db.session.commit()
                flash(f'已将 {admin.name} 的权限从级别 {old_level} 更改为级别 {new_permission}', 'success')
        else:
            flash('未找到该管理员', 'danger')
        
        return redirect(url_for('admin_permissions'))
    
    # GET请求：显示所有管理员及其权限
    admins = db.session.query(Admin, Users).join(Users, Admin.user_id == Users.user_id).all()
    
    return render_template('admin_permissions.html',
                         user=current_user,
                         admins=admins,
                         super_admin_id=super_admin_id,
                         title='权限管理')


@app.route('/admin/grades', methods=['GET'])
@login_required
@admin_permission_required(2)
def admin_grades():
    """管理员：查看所有成绩（需要级别2权限）"""
    # 获取筛选参数
    semester = request.args.get('semester', '')
    class_id = request.args.get('class_id', type=int)
    status = request.args.get('status', '')  # 成绩状态：finalized/temp/all
    search = request.args.get('search', '').strip()  # 学生搜索
    teacher_id = request.args.get('teacher_id', type=int)  # 教师筛选
    
    # 基础查询 - 直接关联到 Users 表获取教师姓名
    query = db.session.query(
        Grade, Student, TeachingClass, Course, Teacher, Users
    ).join(
        Student, Grade.student_id == Student.student_id
    ).join(
        TeachingClass, Grade.class_id == TeachingClass.class_id
    ).join(
        Course, TeachingClass.course_id == Course.course_id
    ).outerjoin(
        TeacherClass, db.and_(
            TeachingClass.class_id == TeacherClass.class_id,
            TeacherClass.role == 'main'
        )
    ).outerjoin(
        Teacher, TeacherClass.teacher_id == Teacher.teacher_id
    ).outerjoin(
        Users, Teacher.user_id == Users.user_id
    )
    
    # 应用筛选
    if semester:
        query = query.filter(TeachingClass.semester == semester)
    if class_id:
        query = query.filter(Grade.class_id == class_id)
    if status == 'finalized':
        query = query.filter(Grade.is_finalized == True)
    elif status == 'temp':
        query = query.filter(Grade.is_finalized == False)
    if search:
        query = query.filter(
            db.or_(
                Student.student_no.like(f'%{search}%'),
                Student.name.like(f'%{search}%')
            )
        )
    if teacher_id:
        query = query.filter(Teacher.teacher_id == teacher_id)
    
    # 排序
    grades_data = query.order_by(
        TeachingClass.semester.desc(),
        Course.course_name,
        Student.student_no
    ).all()
    
    # 获取所有学期列表（用于筛选）
    semesters = db.session.query(
        TeachingClass.semester
    ).distinct().order_by(
        TeachingClass.semester.desc()
    ).all()
    semesters = [s[0] for s in semesters]
    
    # 获取所有教学班列表（用于筛选）
    if semester:
        classes = db.session.query(
            TeachingClass, Course
        ).join(
            Course
        ).filter(
            TeachingClass.semester == semester
        ).order_by(
            Course.course_name
        ).all()
    else:
        classes = []
    
    # 获取所有教师列表（用于筛选） - 只获取主讲教师
    teachers = db.session.query(
        Teacher
    ).join(
        TeacherClass, Teacher.teacher_id == TeacherClass.teacher_id
    ).filter(
        TeacherClass.role == 'main'
    ).distinct().order_by(
        Teacher.teacher_no
    ).all()
    
    # 统计信息
    total_grades = len(grades_data)
    finalized_count = sum(1 for item in grades_data if item[0].is_finalized)
    temp_count = total_grades - finalized_count
    
    return render_template('admin_grades.html',
                         user=current_user,
                         grades_data=grades_data,
                         semesters=semesters,
                         classes=classes,
                         teachers=teachers,
                         selected_semester=semester,
                         selected_class_id=class_id,
                         selected_status=status,
                         selected_search=search,
                         selected_teacher_id=teacher_id,
                         total_grades=total_grades,
                         finalized_count=finalized_count,
                         temp_count=temp_count,
                         title='成绩管理')


@app.route('/admin/grade/unlock/<int:grade_id>', methods=['POST'])
@login_required
@admin_permission_required(1)
def admin_unlock_grade(grade_id):
    """管理员：解锁已归档的成绩（需要最高权限）"""
    grade = db.session.get(Grade, grade_id)
    
    if not grade:
        flash('❌ 成绩记录不存在', 'danger')
        return redirect(url_for('admin_grades'))
    
    if not grade.is_finalized:
        flash('⚠️ 该成绩尚未归档，无需解锁', 'warning')
        return redirect(url_for('admin_grades'))
    
    try:
        # 解锁成绩
        grade.is_finalized = False
        grade.finalized_at = None
        # 保留 calculation_formula 以便重新归档时参考
        
        db.session.commit()
        
        # 获取学生和班级信息用于日志
        student = grade.student
        teaching_class = grade.teaching_class
        
        flash(f'✅ 已解锁成绩：{student.name} - {teaching_class.course.course_name}', 'success')
        app.logger.info(f'管理员 {current_user.username} 解锁了成绩 grade_id={grade_id}')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"解锁成绩失败: {e}")
        flash(f'❌ 解锁失败：{e}', 'danger')
    
    return redirect(url_for('admin_grades'))


@app.route('/admin/class/<int:class_id>/grades/unlock_all', methods=['POST'])
@login_required
@admin_permission_required(1)
def admin_unlock_class_grades(class_id):
    """管理员：解锁整个班级的所有归档成绩（需要最高权限）"""
    teaching_class = db.session.get(TeachingClass, class_id)
    
    if not teaching_class:
        flash('❌ 教学班不存在', 'danger')
        return redirect(url_for('admin_grades'))
    
    try:
        # 查找该班级所有已归档的成绩
        finalized_grades = Grade.query.filter_by(
            class_id=class_id,
            is_finalized=True
        ).all()
        
        if not finalized_grades:
            flash('⚠️ 该班级没有已归档的成绩', 'warning')
            return redirect(url_for('admin_grades'))
        
        # 批量解锁
        count = 0
        for grade in finalized_grades:
            grade.is_finalized = False
            grade.finalized_at = None
            count += 1
        
        db.session.commit()
        
        flash(f'✅ 已解锁 {count} 条成绩记录：{teaching_class.course.course_name} - {teaching_class.class_name}', 'success')
        app.logger.info(f'管理员 {current_user.username} 批量解锁了班级 {class_id} 的 {count} 条成绩')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"批量解锁成绩失败: {e}")
        flash(f'❌ 批量解锁失败：{e}', 'danger')
    
    return redirect(url_for('admin_grades'))


@app.route('/admin/import_departments', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_import_departments():
    """管理员：批量导入院系"""
    if request.method == 'GET':
        return render_template('admin_import_departments.html', title="批量导入院系")
    
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('未选择文件或文件名为空', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        flash('文件格式错误，请上传 CSV 文件。', 'danger')
        return redirect(request.url)
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        total_rows = 0
        error_details = []
        
        for i, row in enumerate(csv_reader):
            total_rows += 1
            line_num = i + 2
            
            dept_name = row.get('dept_name', '').strip()
            
            if not dept_name:
                error_details.append(f"第 {line_num} 行导入失败：院系名称不能为空。")
                continue
            
            try:
                # 检查是否已存在
                existing_dept = Department.query.filter_by(dept_name=dept_name).first()
                if existing_dept:
                    error_details.append(f"第 {line_num} 行（{dept_name}）已存在，跳过。")
                    continue
                
                # 创建新院系
                max_dept = db.session.query(db.func.max(Department.dept_id)).scalar()
                new_dept_id = (max_dept or 0) + 1
                
                new_dept = Department(
                    dept_id=new_dept_id,
                    dept_name=dept_name
                )
                db.session.add(new_dept)
                success_count += 1
                
            except Exception as e:
                error_details.append(f"第 {line_num} 行（{dept_name}）导入失败：{e}")
                continue
        
        db.session.commit()
        
        if error_details:
            flash(f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败/跳过: {len(error_details)}。', 'warning')
        else:
            flash(f'✅ 批量导入成功！总计导入 {success_count} 个院系。', 'success')
        
        return render_template('admin_import_departments.html', 
                             title="批量导入院系",
                             error_details=error_details)
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
        return redirect(request.url)


@app.route('/admin/import_users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_batch_import():
    """管理员：批量导入用户功能"""
    
    # 假设这里是 GET 请求，显示导入页面
    if request.method == 'GET':
        return render_template('admin_batch_import.html', title="批量导入用户")

    # POST 请求：处理文件导入逻辑
    if request.method == 'POST':
        # 检查文件上传
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('未选择文件或文件名为空', 'danger')
            return redirect(request.url)
            
        file = request.files['file']

        if not file.filename.endswith('.csv'):
            flash('文件格式错误，请上传 CSV 文件。', 'danger')
            return redirect(request.url)

        try:
            # 读取文件内容
            stream = io.StringIO(file.stream.read().decode("utf-8-sig")) 
            csv_reader = csv.DictReader(stream)
            
            # 导入统计
            success_count = 0
            total_rows = 0
            error_details = []
            
            db.session.begin_nested() # 开启外部事务，确保要么全部成功，要么全部回滚 (如果未在循环内回滚)

            for i, row in enumerate(csv_reader):
                total_rows += 1
                line_num = i + 2 # 假设第一行是表头
                
                # 显式创建保存点 (Savepoint)
                savepoint = db.session.begin_nested() 
                
                # 核心字段检查
                username = (row.get('username') or '').strip()
                password = (row.get('password') or '').strip()
                real_name = (row.get('real_name') or '').strip()
                role = (row.get('role') or '').strip().lower()
                role_no = (row.get('role_no') or '').strip()
                department = (row.get('department') or '').strip()  # 院系必填

                if not all([username, password, real_name, role, role_no, department]):
                    error_details.append(f"第 {line_num} 行 (用户: {username}) 导入失败： 必填字段缺失（username, password, real_name, role, role_no, department）。")
                    savepoint.rollback()
                    continue

                if role not in ['admin', 'teacher', 'student']:
                    error_details.append(f"第 {line_num} 行 (用户: {username}) 导入失败： 角色 '{role}' 无效。")
                    savepoint.rollback()
                    continue
                
                # 检查用户名是否已存在 (简化检查)
                if Users.query.filter_by(username=username).first():
                    error_details.append(f"第 {line_num} 行 (用户: {username}) 导入失败： 用户名已存在。")
                    savepoint.rollback()
                    continue

                try:
                    new_user_id = generate_next_id(Users, 'user_id')
                    
                    # 创建 Users 记录
                    new_user = Users(
                        user_id=new_user_id,
                        username=username,
                        real_name=real_name,
                        phone=row.get('phone'),
                        email=row.get('email'),
                        role=role,
                        status=1 
                    )
                    new_user.set_password(password)
                    db.session.add(new_user)
                    
                    dept_id = get_or_create_department(department)
                    if not dept_id:
                        error_details.append(f"第 {line_num} 行 (用户: {username}) 导入失败： 院系 '{department}' 不存在或创建失败。")
                        savepoint.rollback()
                        continue
                    
                    # 创建角色特定记录
                    if role == 'admin':
                        # 检查是否为系统中首个管理员
                        is_first_admin = db.session.query(db.func.count(Admin.admin_id)).scalar() == 0
                        new_role = Admin(
                            admin_id=generate_next_id(Admin, 'admin_id'),
                            user_id=new_user_id,
                            admin_no=role_no,
                            dept_id=dept_id,
                            permission_level=1 if is_first_admin else 3
                        )
                    elif role == 'teacher':
                        new_role = Teacher(
                            teacher_id=generate_next_id(Teacher, 'teacher_id'),
                            user_id=new_user_id,
                            teacher_no=role_no,
                            dept_id=dept_id,
                            title=row.get('title')
                        )
                    elif role == 'student':
                        new_role = Student(
                            student_id=generate_next_id(Student, 'student_id'),
                            user_id=new_user_id,
                            student_no=role_no,
                            dept_id=dept_id,
                            major=row.get('major')
                        )
                    db.session.add(new_role)
                    success_count += 1
                
                except Exception as e:
                    error_details.append(f"第 {line_num} 行（用户: {username}）导入失败： {e}")
                    savepoint.rollback()
                    continue
                
            db.session.commit()
            
            status = 'warning' if error_details else 'success'
            message = f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败: {len(error_details)}。' if error_details else f'✅ 批量导入成功！总计导入 {success_count} 条记录。'
            flash(message, status)
            
            # 将错误详情传递给模板显示
            return render_template('admin_batch_import.html', 
                                   title="批量导入用户", 
                                   error_details=error_details)
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
            return redirect(request.url)


@app.route('/admin/import_courses', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_import_courses():
    """管理员：批量导入课程"""
    if request.method == 'GET':
        return render_template('admin_import_courses.html', title="批量导入课程")
    
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('未选择文件或文件名为空', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        flash('文件格式错误，请上传 CSV 文件。', 'danger')
        return redirect(request.url)
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        csv_reader = csv.DictReader(stream)
        success_count = 0
        total_rows = 0
        error_details = []
        
        for i, row in enumerate(csv_reader):
            total_rows += 1
            line_num = i + 2
            savepoint = db.session.begin_nested()
            
            course_code = row.get('course_code')
            course_name = row.get('course_name')
            
            if not all([course_code, course_name]):
                error_details.append(f"第 {line_num} 行：必填字段缺失")
                savepoint.rollback()
                continue
            
            if Course.query.filter_by(course_code=course_code).first():
                error_details.append(f"第 {line_num} 行：课程代码 {course_code} 已存在")
                savepoint.rollback()
                continue
            
            try:
                new_course = Course(
                    course_id=generate_next_id(Course, 'course_id'),
                    course_code=course_code,
                    course_name=course_name,
                    credit=float(row.get('credit')) if row.get('credit') else None,
                    hours=int(row.get('hours')) if row.get('hours') else None,
                    course_type=row.get('course_type'),
                    description=row.get('description')
                )
                db.session.add(new_course)
                success_count += 1
            except Exception as e:
                error_details.append(f"第 {line_num} 行：{e}")
                savepoint.rollback()
                continue
        
        db.session.commit()
        
        if error_details:
            flash(f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败: {len(error_details)}。', 'warning')
        else:
            flash(f'✅ 批量导入成功！总计导入 {success_count} 条记录。', 'success')
        
        return render_template('admin_import_courses.html', title="批量导入课程", error_details=error_details)
    
    except Exception as e:
        db.session.rollback()
        flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
        return redirect(request.url)


@app.route('/admin/import_teaching_classes', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_import_teaching_classes():
    """管理员：批量导入教学班"""
    if request.method == 'GET':
        return render_template('admin_import_teaching_classes.html', title="批量导入教学班")
    
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('未选择文件或文件名为空', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        flash('文件格式错误，请上传 CSV 文件。', 'danger')
        return redirect(request.url)
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        csv_reader = csv.DictReader(stream)
        success_count = 0
        total_rows = 0
        error_details = []
        
        for i, row in enumerate(csv_reader):
            total_rows += 1
            line_num = i + 2
            savepoint = db.session.begin_nested()
            
            course_code = row.get('course_code')
            class_name = row.get('class_name')
            semester = row.get('semester')
            
            if not all([course_code, class_name, semester]):
                error_details.append(f"第 {line_num} 行：必填字段缺失")
                savepoint.rollback()
                continue
            
            course = Course.query.filter_by(course_code=course_code).first()
            if not course:
                error_details.append(f"第 {line_num} 行：课程代码 {course_code} 不存在")
                savepoint.rollback()
                continue
            
            try:
                max_id = db.session.query(db.func.max(TeachingClass.class_id)).scalar()
                new_id = (max_id or 0) + 1
                
                new_class = TeachingClass(
                    class_id=new_id,
                    course_id=course.course_id,
                    class_name=class_name,
                    semester=semester,
                    class_time=row.get('class_time'),
                    classroom=row.get('classroom'),
                    capacity=int(row.get('capacity')) if row.get('capacity') else None,
                    status=1
                )
                db.session.add(new_class)
                success_count += 1
            except Exception as e:
                error_details.append(f"第 {line_num} 行：{e}")
                savepoint.rollback()
                continue
        
        db.session.commit()
        
        if error_details:
            flash(f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败: {len(error_details)}。', 'warning')
        else:
            flash(f'✅ 批量导入成功！总计导入 {success_count} 条记录。', 'success')
        
        return render_template('admin_import_teaching_classes.html', title="批量导入教学班", error_details=error_details)
    
    except Exception as e:
        db.session.rollback()
        flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
        return redirect(request.url)


@app.route('/admin/import_student_classes', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_import_student_classes():
    """管理员：批量导入学生选课关系"""
    if request.method == 'GET':
        return render_template('admin_import_student_classes.html', title="批量导入学生选课")
    
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('未选择文件或文件名为空', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        flash('文件格式错误，请上传 CSV 文件。', 'danger')
        return redirect(request.url)
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        csv_reader = csv.DictReader(stream)
        success_count = 0
        total_rows = 0
        error_details = []
        
        for i, row in enumerate(csv_reader):
            total_rows += 1
            line_num = i + 2
            savepoint = db.session.begin_nested()
            
            student_no = row.get('student_no')
            class_name = row.get('class_name')
            semester = row.get('semester')
            
            if not all([student_no, class_name, semester]):
                error_details.append(f"第 {line_num} 行：必填字段缺失")
                savepoint.rollback()
                continue
            
            student = Student.query.filter_by(student_no=student_no).first()
            if not student:
                error_details.append(f"第 {line_num} 行：学号 {student_no} 不存在")
                savepoint.rollback()
                continue
            
            teaching_class = TeachingClass.query.filter_by(class_name=class_name, semester=semester).first()
            if not teaching_class:
                error_details.append(f"第 {line_num} 行：教学班 {class_name} (学期:{semester}) 不存在")
                savepoint.rollback()
                continue
            
            if StudentClass.query.filter_by(student_id=student.student_id, class_id=teaching_class.class_id).first():
                error_details.append(f"第 {line_num} 行：该学生已选此课")
                savepoint.rollback()
                continue
            
            try:
                max_id = db.session.query(db.func.max(StudentClass.id)).scalar()
                new_id = (max_id or 0) + 1
                
                new_enrollment = StudentClass(
                    id=new_id,
                    student_id=student.student_id,
                    class_id=teaching_class.class_id,
                    status=1
                )
                db.session.add(new_enrollment)
                success_count += 1
            except Exception as e:
                error_details.append(f"第 {line_num} 行：{e}")
                savepoint.rollback()
                continue
        
        db.session.commit()
        
        if error_details:
            flash(f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败: {len(error_details)}。', 'warning')
        else:
            flash(f'✅ 批量导入成功！总计导入 {success_count} 条记录。', 'success')
        
        return render_template('admin_import_student_classes.html', title="批量导入学生选课", error_details=error_details)
    
    except Exception as e:
        db.session.rollback()
        flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
        return redirect(request.url)


@app.route('/admin/import_teacher_classes', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_import_teacher_classes():
    """管理员：批量导入教师任课关系"""
    if request.method == 'GET':
        return render_template('admin_import_teacher_classes.html', title="批量导入教师任课")
    
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('未选择文件或文件名为空', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        flash('文件格式错误，请上传 CSV 文件。', 'danger')
        return redirect(request.url)
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        csv_reader = csv.DictReader(stream)
        success_count = 0
        total_rows = 0
        error_details = []
        
        for i, row in enumerate(csv_reader):
            total_rows += 1
            line_num = i + 2
            savepoint = db.session.begin_nested()
            
            teacher_no = row.get('teacher_no')
            class_name = row.get('class_name')
            semester = row.get('semester')
            role = row.get('role', 'main').lower()
            
            if not all([teacher_no, class_name, semester]):
                error_details.append(f"第 {line_num} 行：必填字段缺失")
                savepoint.rollback()
                continue
            
            if role not in ['main', 'assistant']:
                error_details.append(f"第 {line_num} 行：角色必须是 main 或 assistant")
                savepoint.rollback()
                continue
            
            teacher = Teacher.query.filter_by(teacher_no=teacher_no).first()
            if not teacher:
                error_details.append(f"第 {line_num} 行：教师工号 {teacher_no} 不存在")
                savepoint.rollback()
                continue
            
            teaching_class = TeachingClass.query.filter_by(class_name=class_name, semester=semester).first()
            if not teaching_class:
                error_details.append(f"第 {line_num} 行：教学班 {class_name} (学期:{semester}) 不存在")
                savepoint.rollback()
                continue
            
            if TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=teaching_class.class_id).first():
                error_details.append(f"第 {line_num} 行：该教师已任教此班")
                savepoint.rollback()
                continue
            
            try:
                max_id = db.session.query(db.func.max(TeacherClass.id)).scalar()
                new_id = (max_id or 0) + 1
                
                new_assignment = TeacherClass(
                    id=new_id,
                    teacher_id=teacher.teacher_id,
                    class_id=teaching_class.class_id,
                    role=role
                )
                db.session.add(new_assignment)
                success_count += 1
            except Exception as e:
                error_details.append(f"第 {line_num} 行：{e}")
                savepoint.rollback()
                continue
        
        db.session.commit()
        
        if error_details:
            flash(f'⚠️ 批量导入完成。总行数: {total_rows}，成功: {success_count}，失败: {len(error_details)}。', 'warning')
        else:
            flash(f'✅ 批量导入成功！总计导入 {success_count} 条记录。', 'success')
        
        return render_template('admin_import_teacher_classes.html', title="批量导入教师任课", error_details=error_details)
    
    except Exception as e:
        db.session.rollback()
        flash(f'❌ 导入过程发生致命错误: {e}', 'danger')
        return redirect(request.url)

            
# ==================== 学生模块路由 ====================

@app.route('/student_dashboard')
@login_required
@role_required('student')
def student_dashboard():
    """学生仪表板 - 显示选课列表（使用视图优化）"""
    student = current_user.student_profile
    
    # 使用视图获取我的课程（简化查询）
    my_courses = VStudentMyCourses.query.filter_by(student_id=student.student_id).all()
    
    # 统计数据初始化
    total_pending_assignments = 0
    total_courses = len(my_courses)
    grades_list = []
    
    # 构建课程信息列表
    courses_info = []
    now = datetime.now()
    
    for course_view in my_courses:
        # 获取该课程未提交且未截止的作业
        pending_assignments_data = VStudentMyAssignments.query.filter(
            VStudentMyAssignments.student_id == student.student_id,
            VStudentMyAssignments.class_id == course_view.class_id,
            VStudentMyAssignments.submission_id == None,
            VStudentMyAssignments.deadline > now
        ).all()
        
        pending_assignments = [{
            'assignment_id': a.assignment_id,
            'title': a.assignment_title,
            'type': a.assignment_type,
            'deadline': a.deadline
        } for a in pending_assignments_data]
        
        total_pending_assignments += len(pending_assignments)
        
        # 获取成绩（使用视图）
        grade_view = VStudentMyGrades.query.filter_by(
            student_id=student.student_id,
            class_id=course_view.class_id
        ).first()
        
        if grade_view and grade_view.final_grade is not None:
            grades_list.append(float(grade_view.final_grade))
        
        courses_info.append({
            'class_id': course_view.class_id,
            'course_name': course_view.course_name,
            'class_name': course_view.class_name,
            'semester': course_view.semester,
            'classroom': course_view.classroom,
            'class_time': course_view.class_time,
            'credit': float(course_view.credit) if course_view.credit else None,
            'pending_assignments': pending_assignments,
            'final_grade': float(grade_view.final_grade) if grade_view and grade_view.final_grade else None
        })
    
    # 计算平均成绩
    average_grade = sum(grades_list) / len(grades_list) if grades_list else 0
    
    # 统计信息
    stats = {
        'total_courses': total_courses,
        'total_pending_assignments': total_pending_assignments,
        'average_grade': round(average_grade, 1),
        'graded_courses': len(grades_list)
    }
    
    return render_template('student_dashboard.html', 
                         user=current_user,
                         student=student,
                         courses_info=courses_info,
                         stats=stats,
                         title='学生仪表板')


@app.route('/student/class/<int:class_id>')
@login_required
@role_required('student')
def student_class_detail(class_id):
    """学生查看课程详情（使用视图优化）"""
    student = current_user.student_profile
    
    # 验证学生是否选修该课程
    enrollment = StudentClass.query.filter_by(student_id=student.student_id, class_id=class_id).first()
    if not enrollment:
        flash('您没有选修该课程', 'danger')
        return redirect(url_for('student_dashboard'))
    
    teaching_class = enrollment.teaching_class
    course = teaching_class.course
    
    # 使用视图获取作业列表及提交状态（一次查询获取所有信息）
    assignments_view = VStudentMyAssignments.query.filter_by(
        student_id=student.student_id,
        class_id=class_id
    ).order_by(VStudentMyAssignments.deadline.desc()).all()
    
    assignments_info = []
    for av in assignments_view:
        # 构建assignment对象（用于兼容现有模板）
        assignment_obj = type('obj', (object,), {
            'assignment_id': av.assignment_id,
            'title': av.assignment_title,
            'type': av.assignment_type,
            'description': av.description,
            'total_score': av.total_score,
            'deadline': av.deadline,
            'publish_time': av.publish_time
        })
        
        # 构建submission对象（如果有）
        submission_obj = None
        if av.submission_id:
            submission_obj = type('obj', (object,), {
                'submission_id': av.submission_id,
                'submit_time': av.submit_time,
                'score': av.score,
                'feedback': av.feedback,
                'status': av.submission_status
            })
        
        assignments_info.append({
            'assignment': assignment_obj,
            'submission': submission_obj,
            'status': av.status_display
        })
    
    # 获取教学资料列表
    materials = Material.query.filter_by(class_id=class_id).order_by(Material.publish_time.desc()).all()
    
    # 获取成绩
    grade = Grade.query.filter_by(student_id=student.student_id, class_id=class_id).first()
    
    return render_template('student_class_detail.html',
                         user=current_user,
                         student=student,
                         teaching_class=teaching_class,
                         course=course,
                         assignments_info=assignments_info,
                         materials=materials,
                         grade=grade,
                         title=f'{course.course_name} - {teaching_class.class_name}')


@app.route('/student/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_submit_assignment(assignment_id):
    """学生提交作业"""
    student = current_user.student_profile
    
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash('作业不存在', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # 验证学生是否选修该课程
    enrollment = StudentClass.query.filter_by(student_id=student.student_id, class_id=assignment.class_id).first()
    if not enrollment:
        flash('您没有权限提交该作业', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # 检查是否已提交
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student.student_id
    ).first()
    
    if request.method == 'POST':
        try:
            content = request.form.get('content', '').strip()
            file = request.files.get('file')
            
            # 变量初始化
            file_name = None
            file_path = None
            
            # 处理文件上传
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('不支持的文件格式', 'danger')
                    return redirect(request.url)
                
                # 生成安全的文件名
                original_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{student.student_no}_{assignment_id}_{timestamp}_{original_filename}"
                
                # 保存文件
                file_path_full = os.path.join(app.config['ASSIGNMENTS_FOLDER'], filename)
                file.save(file_path_full)
                
                file_name = original_filename
                file_path = filename  # 只存储相对路径
            
            if not content and not file_path:
                flash('请填写提交内容或上传文件', 'danger')
                return redirect(request.url)
            
            # 检查截止时间
            if datetime.now() > assignment.deadline:
                flash('⚠️ 已超过截止时间，提交可能不被接受', 'warning')
            
            if existing_submission:
                # 更新现有提交
                existing_submission.content = content
                if file_path:  # 只有上传了新文件才更新文件信息
                    existing_submission.file_name = file_name
                    existing_submission.file_path = file_path
                existing_submission.submit_time = db.func.now()
                existing_submission.status = 'submitted'
                # 重新提交时清除之前的评分
                existing_submission.score = None
                existing_submission.feedback = None
                existing_submission.graded_by = None
                existing_submission.graded_time = None
                flash('✅ 重新提交成功！', 'success')
            else:
                # 创建新提交
                max_id = db.session.query(db.func.max(Submission.submission_id)).scalar()
                new_id = (max_id or 0) + 1
                
                new_submission = Submission(
                    submission_id=new_id,
                    assignment_id=assignment_id,
                    student_id=student.student_id,
                    content=content,
                    file_name=file_name,
                    file_path=file_path,
                    status='submitted'
                )
                db.session.add(new_submission)
                flash('✅ 提交成功！', 'success')
            
            db.session.commit()
            return redirect(url_for('student_class_detail', class_id=assignment.class_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"提交失败: {e}")
            flash(f'提交失败：{e}', 'danger')
            return redirect(request.url)
    
    teaching_class = assignment.teaching_class
    course = teaching_class.course
    
    return render_template('student_submit_assignment.html',
                         user=current_user,
                         student=student,
                         assignment=assignment,
                         existing_submission=existing_submission,
                         course=course,
                         title=f'提交 - {assignment.title}')


@app.route('/student/class/<int:class_id>/grades')
@login_required
@role_required('student')
def student_view_grades(class_id):
    """学生查看成绩详情"""
    student = current_user.student_profile
    
    # 验证选课权限
    enrollment = StudentClass.query.filter_by(student_id=student.student_id, class_id=class_id).first()
    if not enrollment:
        flash('您没有选修该课程', 'danger')
        return redirect(url_for('student_dashboard'))
    
    teaching_class = enrollment.teaching_class
    course = teaching_class.course
    
    # 使用辅助函数获取成绩（优先显示归档成绩）
    grade_display = get_student_grade_display(student.student_id, class_id)
    grade_record = Grade.query.filter_by(student_id=student.student_id, class_id=class_id).first()
    
    # 获取所有作业提交及成绩
    homework_submissions = db.session.query(Submission, Assignment).join(Assignment).filter(
        Assignment.class_id == class_id,
        Assignment.type == 'homework',
        Submission.student_id == student.student_id
    ).order_by(Assignment.publish_time.desc()).all()
    
    # 获取所有考试提交及成绩
    exam_submissions = db.session.query(Submission, Assignment).join(Assignment).filter(
        Assignment.class_id == class_id,
        Assignment.type == 'exam',
        Submission.student_id == student.student_id
    ).order_by(Assignment.publish_time.desc()).all()
    
    return render_template('student_view_grades.html',
                         user=current_user,
                         student=student,
                         teaching_class=teaching_class,
                         course=course,
                         grade_record=grade_record,
                         grade_display=grade_display,
                         homework_submissions=homework_submissions,
                         exam_submissions=exam_submissions,
                         title=f'{course.course_name} - 成绩详情')


# ==================== 教师模块路由 ====================

@app.route('/teacher_dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    """教师仪表板 - 显示任教班级列表（使用视图优化）"""
    teacher = current_user.teacher_profile
    
    # 使用视图获取教师的所有教学班（包含学生人数）
    my_classes = VTeacherMyClasses.query.filter_by(teacher_id=teacher.teacher_id).all()
    
    # 统计数据
    total_classes = len(my_classes)
    total_students = sum(c.enrolled_count for c in my_classes)
    class_ids = [c.class_id for c in my_classes]
    
    # 构建班级信息列表
    classes_info = []
    for class_view in my_classes:
        classes_info.append({
            'class_id': class_view.class_id,
            'course_name': class_view.course_name,
            'class_name': class_view.class_name,
            'semester': class_view.semester,
            'classroom': class_view.classroom,
            'class_time': class_view.class_time,
            'student_count': class_view.enrolled_count,
            'role': class_view.my_role
        })
    
    # 统计待批改作业数
    total_pending_grading = 0
    if class_ids:
        total_pending_grading = Submission.query.join(
            Assignment, Submission.assignment_id == Assignment.assignment_id
        ).filter(
            Assignment.class_id.in_(class_ids),
            Submission.status == 'submitted'
        ).count()
    
    # 统计信息
    stats = {
        'total_classes': total_classes,
        'total_students': total_students,
        'total_pending_grading': total_pending_grading
    }
    
    return render_template('teacher_dashboard.html', 
                         user=current_user, 
                         teacher=teacher,
                         classes_info=classes_info,
                         stats=stats,
                         title='教师仪表板')


@app.route('/teacher/class/<int:class_id>')
@login_required
@role_required('teacher')
def teacher_class_detail(class_id):
    """教师查看教学班详情"""
    teacher = current_user.teacher_profile
    
    # 验证教师是否任教该班级
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限访问该教学班', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    teaching_class = tc.teaching_class
    course = teaching_class.course
    
    # 获取学生名单
    enrollments = StudentClass.query.filter_by(class_id=class_id).all()
    students = [{'student': e.student, 'enroll_time': e.enroll_time} for e in enrollments]
    
    # 获取作业/考试列表，并统计待批改数量
    assignments = Assignment.query.filter_by(class_id=class_id).order_by(Assignment.publish_time.desc()).all()
    
    # 为每个作业/考试添加统计信息
    assignments_with_stats = []
    for assignment in assignments:
        # 统计已提交但未批改的数量
        pending_count = Submission.query.filter_by(
            assignment_id=assignment.assignment_id,
            status='submitted'
        ).count()
        
        # 统计总提交数
        total_submissions = Submission.query.filter_by(
            assignment_id=assignment.assignment_id
        ).count()
        
        # 统计已批改数
        graded_count = Submission.query.filter_by(
            assignment_id=assignment.assignment_id,
            status='graded'
        ).count()
        
        assignments_with_stats.append({
            'assignment': assignment,
            'pending_count': pending_count,
            'total_submissions': total_submissions,
            'graded_count': graded_count
        })
    
    # 获取教学资料列表
    materials = Material.query.filter_by(class_id=class_id).order_by(Material.publish_time.desc()).all()
    
    return render_template('teacher_class_detail.html',
                         user=current_user,
                         teacher=teacher,
                         teaching_class=teaching_class,
                         course=course,
                         students=students,
                         assignments=assignments_with_stats,
                         materials=materials,
                         title=f'{course.course_name} - {teaching_class.class_name}')


@app.route('/teacher/class/<int:class_id>/create_assignment', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_create_assignment(class_id):
    """教师创建作业/考试"""
    teacher = current_user.teacher_profile
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限在该班级发布作业', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    # 从URL参数获取预设类型
    preset_type = request.args.get('type', '')
    
    if request.method == 'POST':
        try:
            assignment_type = request.form.get('type')
            title = request.form.get('title')
            description = request.form.get('description')
            total_score = float(request.form.get('total_score', 100))
            deadline = request.form.get('deadline')
            
            if not all([assignment_type, title, deadline]):
                flash('请填写所有必填字段', 'danger')
                return redirect(request.url)
            
            if assignment_type not in ['homework', 'exam']:
                flash('作业类型无效', 'danger')
                return redirect(request.url)
            
            # 生成新ID
            max_id = db.session.query(db.func.max(Assignment.assignment_id)).scalar()
            new_id = (max_id or 0) + 1
            
            # 转换日期时间
            from datetime import datetime
            deadline_dt = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
            
            new_assignment = Assignment(
                assignment_id=new_id,
                class_id=class_id,
                teacher_id=teacher.teacher_id,
                type=assignment_type,
                title=title,
                description=description,
                total_score=total_score,
                deadline=deadline_dt,
                status=1
            )
            
            # 如果是考试，添加考试特有字段
            if assignment_type == 'exam':
                start_time = request.form.get('start_time')
                duration = request.form.get('duration')
                if start_time:
                    new_assignment.start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
                if duration:
                    new_assignment.duration = int(duration)
            
            db.session.add(new_assignment)
            db.session.commit()
            
            flash(f'✅ {"作业" if assignment_type == "homework" else "考试"} "{title}" 发布成功！', 'success')
            return redirect(url_for('teacher_class_detail', class_id=class_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"创建作业失败: {e}")
            flash(f'发布失败：{e}', 'danger')
            return redirect(request.url)
    
    teaching_class = tc.teaching_class
    return render_template('teacher_create_assignment.html',
                         user=current_user,
                         teaching_class=teaching_class,
                         class_id=class_id,
                         preset_type=preset_type,
                         title='发布作业/考试')


@app.route('/teacher/assignment/<int:assignment_id>')
@login_required
@role_required('teacher')
def teacher_assignment_detail(assignment_id):
    """教师查看作业/考试提交情况（使用视图优化）"""
    teacher = current_user.teacher_profile
    
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash('作业不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=assignment.class_id).first()
    if not tc:
        flash('您没有权限查看该作业', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
    
    # 使用视图获取统计数据（一次查询获取所有统计）
    stats_view = VTeacherSubmissionStatus.query.filter_by(
        teacher_id=teacher.teacher_id,
        assignment_id=assignment_id
    ).first()
    
    # 获取所有应该提交的学生
    enrollments = StudentClass.query.filter_by(class_id=assignment.class_id).all()
    
    # 构建提交情况列表
    submission_list = []
    for enrollment in enrollments:
        student = enrollment.student
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student.student_id
        ).first()
        
        submission_list.append({
            'student': student,
            'submission': submission,
            'status': '已批改' if submission and submission.status == 'graded' else ('已提交' if submission else '未提交')
        })
    
    # 从视图获取统计信息（如果视图查询成功）
    if stats_view:
        total_students = stats_view.total_students
        submitted_count = stats_view.submitted_count
        graded_count = stats_view.graded_count
        unsubmitted_count = stats_view.unsubmitted_count
        submission_rate = stats_view.submission_rate
    else:
        # 回退到传统统计方式
        total_students = len(submission_list)
        submitted_count = sum(1 for s in submission_list if s['submission'])
        graded_count = sum(1 for s in submission_list if s['submission'] and s['submission'].status == 'graded')
        unsubmitted_count = total_students - submitted_count
        submission_rate = (submitted_count / total_students * 100) if total_students > 0 else 0
    
    return render_template('teacher_assignment_detail.html',
                         user=current_user,
                         assignment=assignment,
                         submission_list=submission_list,
                         total_students=total_students,
                         submitted_count=submitted_count,
                         graded_count=graded_count,
                         unsubmitted_count=unsubmitted_count,
                         submission_rate=round(submission_rate, 1),
                         title=f'{assignment.title} - 提交情况')


@app.route('/teacher/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_grade_submission(submission_id):
    """教师批改作业"""
    teacher = current_user.teacher_profile
    
    submission = db.session.get(Submission, submission_id)
    if not submission:
        flash('提交记录不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    assignment = submission.assignment
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=assignment.class_id).first()
    if not tc:
        flash('您没有权限批改该作业', 'danger')
        return redirect(url_for('teacher_assignment_detail', assignment_id=assignment.assignment_id))
    
    if request.method == 'POST':
        try:
            score = float(request.form.get('score'))
            feedback = request.form.get('feedback', '')
            
            if score < 0 or score > float(assignment.total_score):
                flash(f'分数必须在 0 到 {assignment.total_score} 之间', 'danger')
                return redirect(request.url)
            
            submission.score = score
            submission.feedback = feedback
            submission.graded_by = teacher.teacher_id
            submission.graded_time = db.func.now()
            submission.status = 'graded'
            
            db.session.commit()
            flash('✅ 批改成功！', 'success')
            return redirect(url_for('teacher_assignment_detail', assignment_id=assignment.assignment_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"批改失败: {e}")
            flash(f'批改失败：{e}', 'danger')
            return redirect(request.url)
    
    student = submission.student
    assignment = submission.assignment
    
    return render_template('teacher_grade_submission.html',
                         user=current_user,
                         submission=submission,
                         student=student,
                         assignment=assignment,
                         title=f'批改 - {student.name}')


@app.route('/teacher/class/<int:class_id>/calculate_grades', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_calculate_grades(class_id):
    """教师计算成绩（临时成绩，未归档）"""
    teacher = current_user.teacher_profile
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限操作该班级', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    # 检查是否要归档成绩
    finalize = request.form.get('finalize') == 'true'
    
    try:
        # 获取该班级的所有学生
        enrollments = StudentClass.query.filter_by(class_id=class_id).all()
        
        # 获取该班级的所有作业和考试
        all_homeworks = Assignment.query.filter_by(class_id=class_id, type='homework', status=1).all()
        all_exams = Assignment.query.filter_by(class_id=class_id, type='exam', status=1).all()
        
        success_count = 0
        finalized_count = 0
        formula = 'hw*0.3+exam*0.5+eval*0.2'  # 成绩计算公式
        
        for enrollment in enrollments:
            student_id = enrollment.student_id
            
            # 使用辅助函数计算成绩
            calc_result = calculate_student_grade(student_id, class_id)
            homework_avg = calc_result['homework_avg']
            exam_avg = calc_result['exam_avg']
            
            # 获取教师评价分（从表单中获取，处理空值）
            teacher_eval_key = f'teacher_eval_{student_id}'
            teacher_eval_str = request.form.get(teacher_eval_key, '').strip()
            
            # 查找或创建成绩记录
            grade = Grade.query.filter_by(student_id=student_id, class_id=class_id).first()
            
            if grade:
                # 检查是否已归档且未请求重新归档
                if grade.is_finalized and not finalize:
                    continue  # 跳过已归档的成绩
                
                # 如果表单中没有提供评价分（例如禁用的输入框），则保留原值
                if teacher_eval_str:
                    teacher_evaluation = float(teacher_eval_str)
                else:
                    # 保留原有评价分，如果没有则为0
                    teacher_evaluation = float(grade.teacher_evaluation) if grade.teacher_evaluation else 0.0
                
                # 计算最终成绩：作业30% + 考试50% + 教师评价20%
                final_grade = homework_avg * 0.3 + exam_avg * 0.5 + teacher_evaluation * 0.2
                
                # 更新现有记录
                grade.homework_avg = homework_avg
                grade.exam_avg = exam_avg
                grade.teacher_evaluation = teacher_evaluation
                grade.final_grade = final_grade
                grade.calculated_by = teacher.teacher_id
                grade.calculated_at = db.func.now()
                
                # 如果需要归档
                if finalize:
                    grade.finalize(teacher.teacher_id, formula)
                    finalized_count += 1
                
                success_count += 1
            else:
                # 创建新记录 - 新学生必须输入评价分
                teacher_evaluation = float(teacher_eval_str) if teacher_eval_str else 0.0
                final_grade = homework_avg * 0.3 + exam_avg * 0.5 + teacher_evaluation * 0.2
                
                max_id = db.session.query(db.func.max(Grade.grade_id)).scalar()
                new_id = (max_id or 0) + 1
                
                grade = Grade(
                    grade_id=new_id,
                    student_id=student_id,
                    class_id=class_id,
                    homework_avg=homework_avg,
                    exam_avg=exam_avg,
                    teacher_evaluation=teacher_evaluation,
                    final_grade=final_grade,
                    calculated_by=teacher.teacher_id,
                    calculated_at=db.func.now()
                )
                
                # 如果需要归档
                if finalize:
                    grade.finalize(teacher.teacher_id, formula)
                    finalized_count += 1
                    
                db.session.add(grade)
            
            success_count += 1
        
        db.session.commit()
        
        if finalize:
            flash(f'✅ 成绩已归档！共归档 {finalized_count} 名学生的成绩，成绩已锁定。', 'success')
        else:
            flash(f'✅ 成绩计算成功！已为 {success_count} 名学生计算临时成绩。', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"计算成绩失败: {e}")
        flash(f'❌ 操作失败：{e}', 'danger')
    
    return redirect(url_for('teacher_class_grades', class_id=class_id))


@app.route('/teacher/class/<int:class_id>/grades')
@login_required
@role_required('teacher')
def teacher_class_grades(class_id):
    """教师查看班级成绩"""
    teacher = current_user.teacher_profile
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限查看该班级成绩', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    teaching_class = tc.teaching_class
    course = teaching_class.course
    
    # 获取所有学生和成绩
    enrollments = StudentClass.query.filter_by(class_id=class_id).all()
    
    grades_list = []
    has_finalized = False  # 是否有已归档的成绩
    all_finalized = True   # 是否所有成绩都已归档
    
    for enrollment in enrollments:
        student = enrollment.student
        
        # 获取成绩显示数据（优先显示归档成绩）
        grade_display = get_student_grade_display(student.student_id, class_id)
        grade_record = Grade.query.filter_by(student_id=student.student_id, class_id=class_id).first()
        
        if grade_display['is_finalized']:
            has_finalized = True
        else:
            all_finalized = False
        
        grades_list.append({
            'student': student,
            'grade_record': grade_record,  # 数据库记录
            'homework_avg': grade_display['homework_avg'],
            'exam_avg': grade_display['exam_avg'],
            'teacher_evaluation': grade_display['teacher_evaluation'],
            'final_grade': grade_display['final_grade'],
            'is_finalized': grade_display['is_finalized'],
            'finalized_at': grade_display['finalized_at'],
            'calculated_by': grade_display['calculated_by'],
            'calculation_formula': grade_display.get('calculation_formula')
        })
    
    return render_template('teacher_class_grades.html',
                         user=current_user,
                         teaching_class=teaching_class,
                         course=course,
                         grades_list=grades_list,
                         class_id=class_id,
                         has_finalized=has_finalized,
                         all_finalized=all_finalized,
                         title=f'{course.course_name} - 成绩管理')


@app.route('/teacher/class/<int:class_id>/grades_statistics')
@login_required
@role_required('teacher')
def teacher_class_grades_statistics(class_id):
    """教师查看班级成绩统计（全班平均分、排名等）"""
    teacher = current_user.teacher_profile
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限查看该班级成绩统计', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    teaching_class = tc.teaching_class
    course = teaching_class.course
    
    # 获取所有学生和成绩
    enrollments = StudentClass.query.filter_by(class_id=class_id).all()
    
    grades_data = []
    for enrollment in enrollments:
        student = enrollment.student
        grade_display = get_student_grade_display(student.student_id, class_id)
        
        grades_data.append({
            'student': student,
            'homework_avg': grade_display['homework_avg'],
            'exam_avg': grade_display['exam_avg'],
            'teacher_evaluation': grade_display['teacher_evaluation'],
            'final_grade': grade_display['final_grade'],
            'is_finalized': grade_display['is_finalized']
        })
    
    # 计算统计数据
    if grades_data:
        # 按最终成绩排序
        sorted_grades = sorted(grades_data, key=lambda x: x['final_grade'], reverse=True)
        
        # 添加排名
        for idx, item in enumerate(sorted_grades, 1):
            item['rank'] = idx
        
        # 计算平均分
        final_grades = [g['final_grade'] for g in grades_data]
        homework_avgs = [g['homework_avg'] for g in grades_data]
        exam_avgs = [g['exam_avg'] for g in grades_data]
        teacher_evals = [g['teacher_evaluation'] for g in grades_data if g['teacher_evaluation'] > 0]
        
        class_avg_final = sum(final_grades) / len(final_grades) if final_grades else 0
        class_avg_homework = sum(homework_avgs) / len(homework_avgs) if homework_avgs else 0
        class_avg_exam = sum(exam_avgs) / len(exam_avgs) if exam_avgs else 0
        class_avg_teacher_eval = sum(teacher_evals) / len(teacher_evals) if teacher_evals else 0
        
        # 计算最高分、最低分、及格率
        max_grade = max(final_grades) if final_grades else 0
        min_grade = min(final_grades) if final_grades else 0
        pass_count = len([g for g in final_grades if g >= 60])
        pass_rate = (pass_count / len(final_grades) * 100) if final_grades else 0
        
        # 计算分数段统计
        score_ranges = {
            '90-100': len([g for g in final_grades if 90 <= g <= 100]),
            '80-89': len([g for g in final_grades if 80 <= g < 90]),
            '70-79': len([g for g in final_grades if 70 <= g < 80]),
            '60-69': len([g for g in final_grades if 60 <= g < 70]),
            '0-59': len([g for g in final_grades if 0 <= g < 60])
        }
        
        statistics = {
            'class_avg_final': round(class_avg_final, 2),
            'class_avg_homework': round(class_avg_homework, 2),
            'class_avg_exam': round(class_avg_exam, 2),
            'class_avg_teacher_eval': round(class_avg_teacher_eval, 2),
            'max_grade': round(max_grade, 2),
            'min_grade': round(min_grade, 2),
            'pass_rate': round(pass_rate, 2),
            'pass_count': pass_count,
            'total_count': len(final_grades),
            'score_ranges': score_ranges
        }
    else:
        statistics = {
            'class_avg_final': 0,
            'class_avg_homework': 0,
            'class_avg_exam': 0,
            'class_avg_teacher_eval': 0,
            'max_grade': 0,
            'min_grade': 0,
            'pass_rate': 0,
            'pass_count': 0,
            'total_count': 0,
            'score_ranges': {}
        }
        sorted_grades = []
    
    return render_template('teacher_class_grades_statistics.html',
                         user=current_user,
                         teaching_class=teaching_class,
                         course=course,
                         sorted_grades=sorted_grades,
                         statistics=statistics,
                         class_id=class_id,
                         title=f'{course.course_name} - 成绩统计')


@app.route('/teacher/class/<int:class_id>/upload_material', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_upload_material(class_id):
    """教师上传教学资料"""
    teacher = current_user.teacher_profile
    
    # 验证教师是否任教该班级
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not tc:
        flash('您没有权限为该教学班上传资料', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    teaching_class = tc.teaching_class
    course = teaching_class.course
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        file = request.files.get('file')
        
        if not title:
            flash('请填写资料标题', 'danger')
            return redirect(request.url)
        
        if not file or file.filename == '':
            flash('请选择要上传的文件', 'danger')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('不支持的文件格式', 'danger')
            return redirect(request.url)
        
        try:
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{original_filename}"
            
            # 保存文件
            file_path = os.path.join(app.config['MATERIALS_FOLDER'], filename)
            file.save(file_path)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_type = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'unknown'
            
            # 获取下一个 material_id
            max_id = db.session.query(db.func.max(Material.material_id)).scalar() or 0
            new_material_id = max_id + 1
            
            # 创建教学资料记录
            material = Material(
                material_id=new_material_id,
                class_id=class_id,
                teacher_id=teacher.teacher_id,
                title=title,
                description=description,
                file_name=original_filename,
                file_path=filename,  # 只存储相对路径
                file_size=file_size,
                file_type=file_type,
                download_count=0,
                publish_time=datetime.now()
            )
            
            db.session.add(material)
            db.session.commit()
            
            flash(f'✅ 教学资料「{title}」上传成功！', 'success')
            return redirect(url_for('teacher_class_detail', class_id=class_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"上传教学资料失败: {e}")
            flash(f'❌ 上传失败：{e}', 'danger')
            return redirect(request.url)
    
    return render_template('teacher_upload_material.html',
                         user=current_user,
                         teacher=teacher,
                         teaching_class=teaching_class,
                         course=course,
                         title=f'上传教学资料 - {course.course_name}')


@app.route('/material/<int:material_id>/download')
@login_required
def download_material(material_id):
    """下载教学资料（学生和教师均可）"""
    material = db.session.get(Material, material_id)
    if not material:
        flash('教学资料不存在', 'danger')
        return redirect(url_for('index'))
    
    # 权限验证：学生需选修该课程，教师需任教该课程
    if current_user.role == 'student':
        student = current_user.student_profile
        enrollment = StudentClass.query.filter_by(
            student_id=student.student_id,
            class_id=material.class_id
        ).first()
        if not enrollment:
            flash('您没有权限下载该资料', 'danger')
            return redirect(url_for('student_dashboard'))
    elif current_user.role == 'teacher':
        teacher = current_user.teacher_profile
        tc = TeacherClass.query.filter_by(
            teacher_id=teacher.teacher_id,
            class_id=material.class_id
        ).first()
        if not tc:
            flash('您没有权限下载该资料', 'danger')
            return redirect(url_for('teacher_class_detail', class_id=material.class_id))
    else:
        # 管理员可以下载所有资料
        pass
    
    try:
        # 构建完整文件路径
        file_path = os.path.join(app.config['MATERIALS_FOLDER'], material.file_path)
        
        if not os.path.exists(file_path):
            flash('文件不存在', 'danger')
            return redirect(request.referrer or url_for('index'))
        
        # 增加下载次数
        material.download_count += 1
        db.session.commit()
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=material.file_name
        )
        
    except Exception as e:
        app.logger.error(f"下载文件失败: {e}")
        flash(f'下载失败：{e}', 'danger')
        return redirect(request.referrer or url_for('index'))


@app.route('/submission/<int:submission_id>/download')
@login_required
def download_submission_file(submission_id):
    """下载学生提交的作业文件（学生本人和教师可下载）"""
    submission = db.session.get(Submission, submission_id)
    if not submission:
        flash('提交记录不存在', 'danger')
        return redirect(url_for('index'))
    
    # 权限验证
    if current_user.role == 'student':
        student = current_user.student_profile
        if submission.student_id != student.student_id:
            flash('您没有权限下载该文件', 'danger')
            return redirect(url_for('student_dashboard'))
    elif current_user.role == 'teacher':
        teacher = current_user.teacher_profile
        assignment = submission.assignment
        tc = TeacherClass.query.filter_by(
            teacher_id=teacher.teacher_id,
            class_id=assignment.class_id
        ).first()
        if not tc:
            flash('您没有权限下载该文件', 'danger')
            return redirect(url_for('teacher_assignment_detail', assignment_id=submission.assignment_id))
    else:
        # 管理员可以下载所有文件
        pass
    
    if not submission.file_path:
        flash('该提交没有上传文件', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    try:
        # 构建完整文件路径
        file_path = os.path.join(app.config['ASSIGNMENTS_FOLDER'], submission.file_path)
        
        if not os.path.exists(file_path):
            flash('文件不存在', 'danger')
            return redirect(request.referrer or url_for('index'))
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=submission.file_name
        )
        
    except Exception as e:
        app.logger.error(f"下载作业文件失败: {e}")
        flash(f'下载失败：{e}', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    try:
        # 构建完整文件路径
        file_path = os.path.join(app.config['MATERIALS_FOLDER'], material.file_path)
        
        if not os.path.exists(file_path):
            flash('文件不存在', 'danger')
            return redirect(request.referrer or url_for('index'))
        
        # 增加下载次数
        material.download_count += 1
        db.session.commit()
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=material.file_name
        )
        
    except Exception as e:
        app.logger.error(f"下载文件失败: {e}")
        flash(f'下载失败：{e}', 'danger')
        return redirect(request.referrer or url_for('index'))


@app.route('/teacher/assignment/<int:assignment_id>/delete', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_delete_assignment(assignment_id):
    """教师删除作业/考试"""
    teacher = current_user.teacher_profile
    
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash('作业不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=assignment.class_id).first()
    if not tc:
        flash('您没有权限删除该作业', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
    
    try:
        class_id = assignment.class_id
        # 删除相关的提交记录
        Submission.query.filter_by(assignment_id=assignment_id).delete()
        # 删除作业
        db.session.delete(assignment)
        db.session.commit()
        flash(f'✅ 作业「{assignment.title}」及所有相关提交已成功删除', 'success')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除作业失败: {e}")
        flash(f'❌ 删除失败：{e}', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=class_id))


@app.route('/teacher/assignment/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_edit_assignment(assignment_id):
    """教师编辑作业/考试"""
    teacher = current_user.teacher_profile
    
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash('作业不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=assignment.class_id).first()
    if not tc:
        flash('您没有权限编辑该作业', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
    
    teaching_class = tc.teaching_class
    course = teaching_class.course
    
    if request.method == 'POST':
        try:
            assignment.title = request.form.get('title', '').strip()
            assignment.description = request.form.get('description', '').strip()
            assignment.total_score = request.form.get('total_score')
            
            deadline_str = request.form.get('deadline')
            if deadline_str:
                assignment.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            
            # 考试特有字段
            if assignment.type == 'exam':
                start_time_str = request.form.get('start_time')
                if start_time_str:
                    assignment.start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
                
                duration = request.form.get('duration')
                if duration:
                    assignment.duration = int(duration)
            
            if not assignment.title or not assignment.deadline:
                flash('标题和截止时间不能为空', 'danger')
                return redirect(request.url)
            
            db.session.commit()
            flash(f'✅ 作业「{assignment.title}」已成功更新', 'success')
            return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"编辑作业失败: {e}")
            flash(f'❌ 编辑失败：{e}', 'danger')
            return redirect(request.url)
    
    return render_template('teacher_edit_assignment.html',
                         user=current_user,
                         teacher=teacher,
                         assignment=assignment,
                         teaching_class=teaching_class,
                         course=course,
                         title=f'编辑作业 - {assignment.title}')


@app.route('/teacher/assignment/<int:assignment_id>/reopen', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_reopen_assignment(assignment_id):
    """教师重新开放已截止的作业/考试"""
    teacher = current_user.teacher_profile
    
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash('作业不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=assignment.class_id).first()
    if not tc:
        flash('您没有权限操作该作业', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
    
    if request.method == 'POST':
        try:
            new_deadline_str = request.form.get('new_deadline')
            if not new_deadline_str:
                flash('请设置新的截止时间', 'danger')
                return redirect(request.url)
            
            new_deadline = datetime.strptime(new_deadline_str, '%Y-%m-%dT%H:%M')
            
            # 验证新截止时间必须晚于当前时间
            if new_deadline <= datetime.now():
                flash('新的截止时间必须晚于当前时间', 'danger')
                return redirect(request.url)
            
            assignment.deadline = new_deadline
            db.session.commit()
            
            flash(f'✅ 作业「{assignment.title}」已重新开放，新截止时间：{new_deadline.strftime("%Y-%m-%d %H:%M")}', 'success')
            return redirect(url_for('teacher_class_detail', class_id=assignment.class_id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"重新开放作业失败: {e}")
            flash(f'❌ 操作失败：{e}', 'danger')
            return redirect(request.url)
    
    teaching_class = tc.teaching_class
    return render_template('teacher_reopen_assignment.html',
                         user=current_user,
                         assignment=assignment,
                         teaching_class=teaching_class,
                         title=f'重新开放 - {assignment.title}')


@app.route('/teacher/material/<int:material_id>/delete', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_delete_material(material_id):
    """教师删除教学资料"""
    teacher = current_user.teacher_profile
    
    material = db.session.get(Material, material_id)
    if not material:
        flash('教学资料不存在', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证权限
    tc = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=material.class_id).first()
    if not tc:
        flash('您没有权限删除该资料', 'danger')
        return redirect(url_for('teacher_class_detail', class_id=material.class_id))
    
    try:
        class_id = material.class_id
        # 删除文件
        if material.file_path:
            file_path = os.path.join(app.config['MATERIALS_FOLDER'], material.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 删除数据库记录
        db.session.delete(material)
        db.session.commit()
        flash(f'✅ 教学资料「{material.title}」已成功删除', 'success')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除教学资料失败: {e}")
        flash(f'❌ 删除失败：{e}', 'danger')
        return redirect(request.referrer or url_for('teacher_dashboard'))


# ==================== 查询模块路由 ====================

@app.route('/admin/query', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_query():
    """管理员综合查询"""
    results = []
    query_type = request.args.get('type', 'user')
    show_details = False
    
    if request.method == 'POST' or request.args.get('search'):
        query_type = request.form.get('query_type') or request.args.get('type', 'user')
        
        if query_type == 'user':
            # 用户查询
            username = request.form.get('username') or request.args.get('username', '')
            real_name = request.form.get('real_name') or request.args.get('real_name', '')
            role = request.form.get('role') or request.args.get('role', '')
            status = request.form.get('status') or request.args.get('status', '')
            
            query = Users.query
            if username:
                query = query.filter(Users.username.like(f'%{username}%'))
            if real_name:
                query = query.filter(Users.real_name.like(f'%{real_name}%'))
            if role:
                query = query.filter(Users.role == role)
            if status:
                query = query.filter(Users.status == int(status))
            
            results = query.all()
            
        elif query_type == 'course':
            # 课程查询
            course_code = request.form.get('course_code') or request.args.get('course_code', '')
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            course_type = request.form.get('course_type') or request.args.get('course_type', '')
            
            query = Course.query
            if course_code:
                query = query.filter(Course.course_code.like(f'%{course_code}%'))
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if course_type:
                query = query.filter(Course.course_type.like(f'%{course_type}%'))
            
            results = query.all()
            
        elif query_type == 'class':
            # 教学班查询
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            class_name = request.form.get('class_name') or request.args.get('class_name', '')
            semester = request.form.get('semester') or request.args.get('semester', '')
            
            query = db.session.query(TeachingClass, Course).join(Course)
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if class_name:
                query = query.filter(TeachingClass.class_name.like(f'%{class_name}%'))
            if semester:
                query = query.filter(TeachingClass.semester.like(f'%{semester}%'))
            
            results = query.all()
            
        elif query_type == 'department':
            # 系部查询
            dept_name = request.form.get('dept_name') or request.args.get('dept_name', '')
            
            query = Department.query
            if dept_name:
                query = query.filter(Department.dept_name.like(f'%{dept_name}%'))
            
            departments = query.all()
            
            # 统计每个系部的人员数量
            results = []
            for dept in departments:
                teacher_count = Teacher.query.filter_by(dept_id=dept.dept_id).count()
                student_count = Student.query.filter_by(dept_id=dept.dept_id).count()
                admin_count = Admin.query.filter_by(dept_id=dept.dept_id).count()
                
                results.append({
                    'dept': dept,
                    'teacher_count': teacher_count,
                    'student_count': student_count,
                    'admin_count': admin_count
                })
            
        elif query_type == 'grade':
            # 成绩查询（增强版）
            student_no = request.form.get('student_no') or request.args.get('student_no', '')
            student_name = request.form.get('student_name') or request.args.get('student_name', '')
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            min_grade = request.form.get('min_grade') or request.args.get('min_grade', '')
            max_grade = request.form.get('max_grade') or request.args.get('max_grade', '')
            show_details = bool(request.form.get('show_details') == '1' or request.args.get('show_details') == '1')
            
            query = db.session.query(Grade, Student, TeachingClass, Course).join(
                Student, Grade.student_id == Student.student_id
            ).join(
                TeachingClass, Grade.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            )
            
            if student_no:
                query = query.filter(Student.student_no.like(f'%{student_no}%'))
            if student_name:
                query = query.filter(Student.name.like(f'%{student_name}%'))
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if min_grade:
                query = query.filter(Grade.final_grade >= float(min_grade))
            if max_grade:
                query = query.filter(Grade.final_grade <= float(max_grade))
            
            grade_records = query.all()
            
            # 如果需要显示详细信息，计算作业考试缺交情况
            if show_details:
                results = []
                for grade, student, teaching_class, course in grade_records:
                    # 获取该班级的所有作业和考试
                    all_homeworks = Assignment.query.filter_by(
                        class_id=teaching_class.class_id, 
                        type='homework', 
                        status=1
                    ).all()
                    all_exams = Assignment.query.filter_by(
                        class_id=teaching_class.class_id, 
                        type='exam', 
                        status=1
                    ).all()
                    
                    # 统计已提交的作业和考试
                    homework_submitted = 0
                    exam_submitted = 0
                    
                    for hw in all_homeworks:
                        submission = Submission.query.filter_by(
                            assignment_id=hw.assignment_id,
                            student_id=student.student_id
                        ).first()
                        if submission and submission.status in ['submitted', 'graded']:
                            homework_submitted += 1
                    
                    for exam in all_exams:
                        submission = Submission.query.filter_by(
                            assignment_id=exam.assignment_id,
                            student_id=student.student_id
                        ).first()
                        if submission and submission.status in ['submitted', 'graded']:
                            exam_submitted += 1
                    
                    homework_total = len(all_homeworks)
                    exam_total = len(all_exams)
                    homework_missing = homework_total - homework_submitted
                    exam_missing = exam_total - exam_submitted
                    
                    results.append({
                        'grade': grade,
                        'student': student,
                        'teaching_class': teaching_class,
                        'course': course,
                        'homework_submitted': homework_submitted,
                        'homework_total': homework_total,
                        'homework_missing': homework_missing,
                        'exam_submitted': exam_submitted,
                        'exam_total': exam_total,
                        'exam_missing': exam_missing
                    })
            else:
                results = [{'grade': g, 'student': s, 'teaching_class': tc, 'course': c} 
                          for g, s, tc, c in grade_records]
    
    return render_template('admin_query.html',
                         user=current_user,
                         query_type=query_type,
                         results=results,
                         show_details=show_details,
                         title='综合查询')


@app.route('/teacher/query', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_query():
    """教师查询 - 查询自己任教班级的信息"""
    teacher = current_user.teacher_profile
    results = []
    query_type = request.args.get('type', 'student')
    
    # 获取教师任教的班级ID列表
    teaching_class_ids = [tc.class_id for tc in TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()]
    
    if request.method == 'POST' or request.args.get('search'):
        query_type = request.form.get('query_type') or request.args.get('type', 'student')
        
        if query_type == 'student':
            # 学生查询（限制在任教班级内）
            student_no = request.form.get('student_no') or request.args.get('student_no', '')
            student_name = request.form.get('student_name') or request.args.get('student_name', '')
            class_id = request.form.get('class_id') or request.args.get('class_id', '')
            
            query = db.session.query(Student, StudentClass, TeachingClass, Course).join(
                StudentClass, Student.student_id == StudentClass.student_id
            ).join(
                TeachingClass, StudentClass.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            ).filter(
                StudentClass.class_id.in_(teaching_class_ids)
            )
            
            if student_no:
                query = query.filter(Student.student_no.like(f'%{student_no}%'))
            if student_name:
                query = query.filter(Student.name.like(f'%{student_name}%'))
            if class_id:
                query = query.filter(StudentClass.class_id == int(class_id))
            
            results = query.all()
            
        elif query_type == 'submission':
            # 作业提交情况查询
            class_id = request.form.get('class_id') or request.args.get('class_id', '')
            assignment_title = request.form.get('assignment_title') or request.args.get('assignment_title', '')
            status = request.form.get('status') or request.args.get('status', '')
            
            query = db.session.query(Submission, Assignment, Student).join(
                Assignment, Submission.assignment_id == Assignment.assignment_id
            ).join(
                Student, Submission.student_id == Student.student_id
            ).filter(
                Assignment.class_id.in_(teaching_class_ids)
            )
            
            if class_id:
                query = query.filter(Assignment.class_id == int(class_id))
            if assignment_title:
                query = query.filter(Assignment.title.like(f'%{assignment_title}%'))
            if status:
                query = query.filter(Submission.status == status)
            
            results = query.all()
            
        elif query_type == 'grade':
            # 成绩查询（限制在任教班级内）
            student_no = request.form.get('student_no') or request.args.get('student_no', '')
            student_name = request.form.get('student_name') or request.args.get('student_name', '')
            class_id = request.form.get('class_id') or request.args.get('class_id', '')
            min_grade = request.form.get('min_grade') or request.args.get('min_grade', '')
            max_grade = request.form.get('max_grade') or request.args.get('max_grade', '')
            
            query = db.session.query(Grade, Student, TeachingClass, Course).join(
                Student, Grade.student_id == Student.student_id
            ).join(
                TeachingClass, Grade.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            ).filter(
                Grade.class_id.in_(teaching_class_ids)
            )
            
            if student_no:
                query = query.filter(Student.student_no.like(f'%{student_no}%'))
            if student_name:
                query = query.filter(Student.name.like(f'%{student_name}%'))
            if class_id:
                query = query.filter(Grade.class_id == int(class_id))
            if min_grade:
                query = query.filter(Grade.final_grade >= float(min_grade))
            if max_grade:
                query = query.filter(Grade.final_grade <= float(max_grade))
            
            results = query.all()
    
    # 获取教师任教的班级列表用于下拉选择
    teaching_classes = db.session.query(TeachingClass, Course).join(Course).filter(
        TeachingClass.class_id.in_(teaching_class_ids)
    ).all()
    
    return render_template('teacher_query.html',
                         user=current_user,
                         teacher=teacher,
                         query_type=query_type,
                         results=results,
                         teaching_classes=teaching_classes,
                         title='信息查询')


@app.route('/student/query', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_query():
    """学生查询 - 查询自己的课程、作业、成绩"""
    student = current_user.student_profile
    results = []
    query_type = request.args.get('type', 'course')
    
    if request.method == 'POST' or request.args.get('search'):
        query_type = request.form.get('query_type') or request.args.get('type', 'course')
        
        if query_type == 'course':
            # 课程查询（只能查自己选修的）
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            semester = request.form.get('semester') or request.args.get('semester', '')
            
            query = db.session.query(StudentClass, TeachingClass, Course).join(
                TeachingClass, StudentClass.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            ).filter(
                StudentClass.student_id == student.student_id
            )
            
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if semester:
                query = query.filter(TeachingClass.semester.like(f'%{semester}%'))
            
            results = query.all()
            
        elif query_type == 'assignment':
            # 作业查询（只能查自己的）
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            assignment_type = request.form.get('assignment_type') or request.args.get('assignment_type', '')
            status = request.form.get('status') or request.args.get('status', '')
            
            # 获取学生选修的班级ID
            class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=student.student_id).all()]
            
            query = db.session.query(Assignment, TeachingClass, Course).join(
                TeachingClass, Assignment.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            ).filter(
                Assignment.class_id.in_(class_ids)
            )
            
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if assignment_type:
                query = query.filter(Assignment.type == assignment_type)
            
            # 获取所有作业并附加提交状态
            assignments = query.all()
            for assignment, teaching_class, course in assignments:
                submission = Submission.query.filter_by(
                    assignment_id=assignment.assignment_id,
                    student_id=student.student_id
                ).first()
                
                if status:
                    if status == 'not_submitted' and submission:
                        continue
                    if status == 'submitted' and (not submission or submission.status == 'graded'):
                        continue
                    if status == 'graded' and (not submission or submission.status != 'graded'):
                        continue
                
                results.append({
                    'assignment': assignment,
                    'teaching_class': teaching_class,
                    'course': course,
                    'submission': submission
                })
            
        elif query_type == 'grade':
            # 成绩查询（只能查自己的）
            course_name = request.form.get('course_name') or request.args.get('course_name', '')
            min_grade = request.form.get('min_grade') or request.args.get('min_grade', '')
            max_grade = request.form.get('max_grade') or request.args.get('max_grade', '')
            
            query = db.session.query(Grade, TeachingClass, Course).join(
                TeachingClass, Grade.class_id == TeachingClass.class_id
            ).join(
                Course, TeachingClass.course_id == Course.course_id
            ).filter(
                Grade.student_id == student.student_id
            )
            
            if course_name:
                query = query.filter(Course.course_name.like(f'%{course_name}%'))
            if min_grade:
                query = query.filter(Grade.final_grade >= float(min_grade))
            if max_grade:
                query = query.filter(Grade.final_grade <= float(max_grade))
            
            results = query.all()
    
    return render_template('student_query.html',
                         user=current_user,
                         student=student,
                         query_type=query_type,
                         results=results,
                         title='信息查询')


# ==================== 查询导出功能 ====================

@app.route('/admin/query/export')
@login_required
@role_required('admin')
def admin_query_export():
    """管理员查询结果导出为CSV"""
    query_type = request.args.get('type', 'user')
    
    # 创建CSV输出
    output = io.StringIO()
    writer = csv.writer(output)
    
    if query_type == 'user':
        username = request.args.get('username', '')
        real_name = request.args.get('real_name', '')
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        
        query = Users.query
        if username:
            query = query.filter(Users.username.like(f'%{username}%'))
        if real_name:
            query = query.filter(Users.real_name.like(f'%{real_name}%'))
        if role:
            query = query.filter(Users.role == role)
        if status:
            query = query.filter(Users.status == int(status))
        
        users = query.all()
        
        # 写入CSV头部
        writer.writerow(['用户ID', '用户名', '真实姓名', '角色', '工号/学号', '学院/部门', '职称', '专业', '手机号', '邮箱', '状态', '创建时间'])
        # 写入数据
        for user in users:
            role_name = {'admin': '管理员', 'teacher': '教师', 'student': '学生'}.get(user.role, user.role)
            status_name = '激活' if user.status == 1 else '禁用'
            
            # 获取工号/学号
            role_no = '-'
            if user.role == 'admin' and user.admin_profile:
                role_no = user.admin_profile.admin_no
            elif user.role == 'teacher' and user.teacher_profile:
                role_no = user.teacher_profile.teacher_no
            elif user.role == 'student' and user.student_profile:
                role_no = user.student_profile.student_no
            
            # 获取学院/部门
            department = '-'
            if user.role == 'admin' and user.admin_profile and user.admin_profile.department:
                department = user.admin_profile.department.dept_name
            elif user.role == 'teacher' and user.teacher_profile and user.teacher_profile.department:
                department = user.teacher_profile.department.dept_name
            elif user.role == 'student' and user.student_profile and user.student_profile.department:
                department = user.student_profile.department.dept_name
            
            # 获取职称（仅教师）
            title = '-'
            if user.role == 'teacher' and user.teacher_profile:
                title = user.teacher_profile.title or '-'
            
            # 获取专业（仅学生）
            major = '-'
            if user.role == 'student' and user.student_profile:
                major = user.student_profile.major or '-'
            
            writer.writerow([
                user.user_id,
                user.username,
                user.real_name or '-',
                role_name,
                role_no,
                department,
                title,
                major,
                user.phone or '-',
                user.email or '-',
                status_name,
                user.created_at.strftime('%Y-%m-%d') if user.created_at else '-'
            ])
        
        filename = f'用户查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'course':
        course_code = request.args.get('course_code', '')
        course_name = request.args.get('course_name', '')
        course_type = request.args.get('course_type', '')
        
        query = Course.query
        if course_code:
            query = query.filter(Course.course_code.like(f'%{course_code}%'))
        if course_name:
            query = query.filter(Course.course_name.like(f'%{course_name}%'))
        if course_type:
            query = query.filter(Course.course_type.like(f'%{course_type}%'))
        
        courses = query.all()
        
        writer.writerow(['课程代码', '课程名称', '课程类型', '学分', '学时', '课程描述'])
        for course in courses:
            writer.writerow([
                course.course_code,
                course.course_name,
                course.course_type or '-',
                course.credit,
                course.hours or '-',
                (course.description[:50] + '...') if course.description and len(course.description) > 50 else (course.description or '-')
            ])
        
        filename = f'课程查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'class':
        course_name = request.args.get('course_name', '')
        class_name = request.args.get('class_name', '')
        semester = request.args.get('semester', '')
        
        query = db.session.query(TeachingClass, Course).join(Course)
        if course_name:
            query = query.filter(Course.course_name.like(f'%{course_name}%'))
        if class_name:
            query = query.filter(TeachingClass.class_name.like(f'%{class_name}%'))
        if semester:
            query = query.filter(TeachingClass.semester.like(f'%{semester}%'))
        
        results = query.all()
        
        writer.writerow(['教学班ID', '教学班名称', '课程名称', '学期', '上课时间', '上课地点', '容量'])
        for tc, course in results:
            writer.writerow([
                tc.class_id,
                tc.class_name,
                course.course_name,
                tc.semester,
                tc.schedule or '-',
                tc.location or '-',
                tc.capacity or '-'
            ])
        
        filename = f'教学班查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'department':
        # 系部查询导出
        dept_name = request.args.get('dept_name', '')
        
        query = Department.query
        if dept_name:
            query = query.filter(Department.dept_name.like(f'%{dept_name}%'))
        
        departments = query.all()
        
        writer.writerow(['系部ID', '系部名称', '教师人数', '学生人数', '管理员人数', '创建时间'])
        for dept in departments:
            teacher_count = Teacher.query.filter_by(dept_id=dept.dept_id).count()
            student_count = Student.query.filter_by(dept_id=dept.dept_id).count()
            admin_count = Admin.query.filter_by(dept_id=dept.dept_id).count()
            
            writer.writerow([
                dept.dept_id,
                dept.dept_name,
                teacher_count,
                student_count,
                admin_count,
                dept.created_at.strftime('%Y-%m-%d') if dept.created_at else '-'
            ])
        
        filename = f'系部查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'grade':
        student_no = request.args.get('student_no', '')
        student_name = request.args.get('student_name', '')
        course_name = request.args.get('course_name', '')
        min_grade = request.args.get('min_grade', '')
        max_grade = request.args.get('max_grade', '')
        show_details = request.args.get('show_details') == '1'
        
        query = db.session.query(Grade, Student, TeachingClass, Course).join(
            Student, Grade.student_id == Student.student_id
        ).join(
            TeachingClass, Grade.class_id == TeachingClass.class_id
        ).join(
            Course, TeachingClass.course_id == Course.course_id
        )
        
        if student_no:
            query = query.filter(Student.student_no.like(f'%{student_no}%'))
        if student_name:
            query = query.filter(Student.name.like(f'%{student_name}%'))
        if course_name:
            query = query.filter(Course.course_name.like(f'%{course_name}%'))
        if min_grade:
            query = query.filter(Grade.final_grade >= float(min_grade))
        if max_grade:
            query = query.filter(Grade.final_grade <= float(max_grade))
        
        results = query.all()
        
        if show_details:
            writer.writerow(['学号', '姓名', '课程名称', '教学班', '作业平均', '考试平均', '教师评价', '最终成绩', 
                           '已交作业', '缺交作业', '已交考试', '缺交考试', '作业完成率'])
            for grade, student, tc, course in results:
                # 计算作业考试缺交情况
                all_homeworks = Assignment.query.filter_by(class_id=tc.class_id, type='homework', status=1).all()
                all_exams = Assignment.query.filter_by(class_id=tc.class_id, type='exam', status=1).all()
                
                homework_submitted = sum(1 for hw in all_homeworks 
                                       if Submission.query.filter_by(assignment_id=hw.assignment_id, student_id=student.student_id)
                                       .filter(Submission.status.in_(['submitted', 'graded'])).first())
                exam_submitted = sum(1 for exam in all_exams 
                                   if Submission.query.filter_by(assignment_id=exam.assignment_id, student_id=student.student_id)
                                   .filter(Submission.status.in_(['submitted', 'graded'])).first())
                
                homework_total = len(all_homeworks)
                exam_total = len(all_exams)
                homework_missing = homework_total - homework_submitted
                exam_missing = exam_total - exam_submitted
                completion_rate = (homework_submitted / homework_total * 100) if homework_total > 0 else 0
                
                writer.writerow([
                    student.student_no,
                    student.name,
                    course.course_name,
                    tc.class_name,
                    f'{float(grade.homework_avg):.1f}' if grade.homework_avg else '-',
                    f'{float(grade.exam_avg):.1f}' if grade.exam_avg else '-',
                    f'{float(grade.teacher_evaluation):.1f}' if grade.teacher_evaluation else '-',
                    f'{float(grade.final_grade):.1f}' if grade.final_grade else '-',
                    homework_submitted,
                    homework_missing,
                    exam_submitted,
                    exam_missing,
                    f'{completion_rate:.1f}%'
                ])
        else:
            writer.writerow(['学号', '姓名', '课程名称', '教学班', '作业平均', '考试平均', '教师评价', '最终成绩'])
            for grade, student, tc, course in results:
                writer.writerow([
                    student.student_no,
                    student.name,
                    course.course_name,
                    tc.class_name,
                    f'{float(grade.homework_avg):.1f}' if grade.homework_avg else '-',
                    f'{float(grade.exam_avg):.1f}' if grade.exam_avg else '-',
                    f'{float(grade.teacher_evaluation):.1f}' if grade.teacher_evaluation else '-',
                    f'{float(grade.final_grade):.1f}' if grade.final_grade else '-'
                ])
        
        filename = f'成绩查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    else:
        flash('无效的查询类型', 'danger')
        return redirect(url_for('admin_query'))
    
    # 创建响应
    output.seek(0)
    response = make_response(output.getvalue().encode('utf-8-sig'))  # 使用utf-8-sig支持Excel打开中文
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response


@app.route('/teacher/query/export')
@login_required
@role_required('teacher')
def teacher_query_export():
    """教师查询结果导出为CSV"""
    teacher_id = db.session.query(Teacher.teacher_id).filter(
        Teacher.user_id == current_user.user_id
    ).scalar()
    
    if not teacher_id:
        flash('无法找到教师信息', 'danger')
        return redirect(url_for('teacher_query'))
    
    teaching_class_ids = db.session.query(TeacherClass.class_id).filter(
        TeacherClass.teacher_id == teacher_id
    ).all()
    teaching_class_ids = [tc[0] for tc in teaching_class_ids]
    
    query_type = request.args.get('type', 'student')
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if query_type == 'student':
        class_id = request.args.get('class_id', '')
        student_no = request.args.get('student_no', '')
        student_name = request.args.get('student_name', '')
        
        query = db.session.query(Student, StudentClass, TeachingClass, Course).join(
            StudentClass, Student.student_id == StudentClass.student_id
        ).join(
            TeachingClass, StudentClass.class_id == TeachingClass.class_id
        ).join(
            Course, TeachingClass.course_id == Course.course_id
        ).filter(TeachingClass.class_id.in_(teaching_class_ids))
        
        if class_id:
            query = query.filter(TeachingClass.class_id == class_id)
        if student_no:
            query = query.filter(Student.student_no.like(f'%{student_no}%'))
        if student_name:
            query = query.filter(Student.name.like(f'%{student_name}%'))
        
        results = query.all()
        
        writer.writerow(['学号', '姓名', '专业', '年级', '课程名称', '教学班'])
        for student, sc, tc, course in results:
            writer.writerow([
                student.student_no,
                student.name,
                student.major or '-',
                student.grade or '-',
                course.course_name,
                tc.class_name
            ])
        
        filename = f'学生查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'submission':
        class_id = request.args.get('class_id', '')
        assignment_id = request.args.get('assignment_id', '')
        status = request.args.get('status', '')
        
        query = db.session.query(Submission, Student, Assignment, TeachingClass).join(
            Student, Submission.student_id == Student.student_id
        ).join(
            Assignment, Submission.assignment_id == Assignment.assignment_id
        ).join(
            TeachingClass, Assignment.class_id == TeachingClass.class_id
        ).filter(TeachingClass.class_id.in_(teaching_class_ids))
        
        if class_id:
            query = query.filter(TeachingClass.class_id == class_id)
        if assignment_id:
            query = query.filter(Assignment.assignment_id == assignment_id)
        if status:
            query = query.filter(Submission.status == status)
        
        results = query.all()
        
        writer.writerow(['学号', '姓名', '作业标题', '教学班', '提交时间', '成绩', '状态'])
        for submission, student, assignment, tc in results:
            status_name = {'submitted': '已提交', 'graded': '已评分', 'late': '迟交'}.get(submission.status, submission.status)
            writer.writerow([
                student.student_no,
                student.name,
                assignment.title,
                tc.class_name,
                submission.submit_time.strftime('%Y-%m-%d %H:%M') if submission.submit_time else '-',
                f'{submission.score:.1f}' if submission.score else '-',
                status_name
            ])
        
        filename = f'作业提交查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'grade':
        class_id = request.args.get('class_id', '')
        student_no = request.args.get('student_no', '')
        min_grade = request.args.get('min_grade', '')
        max_grade = request.args.get('max_grade', '')
        
        query = db.session.query(Grade, Student, TeachingClass, Course).join(
            Student, Grade.student_id == Student.student_id
        ).join(
            TeachingClass, Grade.class_id == TeachingClass.class_id
        ).join(
            Course, TeachingClass.course_id == Course.course_id
        ).filter(TeachingClass.class_id.in_(teaching_class_ids))
        
        if class_id:
            query = query.filter(TeachingClass.class_id == class_id)
        if student_no:
            query = query.filter(Student.student_no.like(f'%{student_no}%'))
        if min_grade:
            query = query.filter(Grade.final_grade >= float(min_grade))
        if max_grade:
            query = query.filter(Grade.final_grade <= float(max_grade))
        
        results = query.all()
        
        writer.writerow(['学号', '姓名', '课程名称', '教学班', '平时成绩', '期末成绩', '教师评分', '最终成绩'])
        for grade, student, tc, course in results:
            writer.writerow([
                student.student_no,
                student.name,
                course.course_name,
                tc.class_name,
                f'{grade.regular_grade:.1f}' if grade.regular_grade else '-',
                f'{grade.exam_grade:.1f}' if grade.exam_grade else '-',
                f'{grade.teacher_score:.1f}' if grade.teacher_score else '-',
                f'{grade.final_grade:.1f}' if grade.final_grade else '-'
            ])
        
        filename = f'成绩查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    else:
        flash('无效的查询类型', 'danger')
        return redirect(url_for('teacher_query'))
    
    output.seek(0)
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response


@app.route('/student/query/export')
@login_required
@role_required('student')
def student_query_export():
    """学生查询结果导出为CSV"""
    student_id = db.session.query(Student.student_id).filter(
        Student.user_id == current_user.user_id
    ).scalar()
    
    if not student_id:
        flash('无法找到学生信息', 'danger')
        return redirect(url_for('student_query'))
    
    query_type = request.args.get('type', 'course')
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if query_type == 'course':
        course_name = request.args.get('course_name', '')
        semester = request.args.get('semester', '')
        
        query = db.session.query(Course, TeachingClass, StudentClass).join(
            TeachingClass, Course.course_id == TeachingClass.course_id
        ).join(
            StudentClass, TeachingClass.class_id == StudentClass.class_id
        ).filter(StudentClass.student_id == student_id)
        
        if course_name:
            query = query.filter(Course.course_name.like(f'%{course_name}%'))
        if semester:
            query = query.filter(TeachingClass.semester.like(f'%{semester}%'))
        
        results = query.all()
        
        writer.writerow(['课程代码', '课程名称', '学分', '教学班', '学期', '上课时间', '上课地点'])
        for course, tc, sc in results:
            writer.writerow([
                course.course_code,
                course.course_name,
                course.credit,
                tc.class_name,
                tc.semester,
                tc.schedule or '-',
                tc.location or '-'
            ])
        
        filename = f'我的课程_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'assignment':
        class_id = request.args.get('class_id', '')
        assignment_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # 先获取学生的所有教学班
        class_ids = db.session.query(StudentClass.class_id).filter(
            StudentClass.student_id == student_id
        ).all()
        class_ids = [c[0] for c in class_ids]
        
        query = db.session.query(Assignment, TeachingClass, Course).join(
            TeachingClass, Assignment.class_id == TeachingClass.class_id
        ).join(
            Course, TeachingClass.course_id == Course.course_id
        ).filter(Assignment.class_id.in_(class_ids))
        
        if class_id:
            query = query.filter(Assignment.class_id == class_id)
        if assignment_type:
            query = query.filter(Assignment.type == assignment_type)
        
        results = query.all()
        
        # 如果需要过滤提交状态，需要额外查询
        filtered_results = []
        for assignment, tc, course in results:
            submission = Submission.query.filter_by(
                assignment_id=assignment.assignment_id,
                student_id=student_id
            ).first()
            
            if status == 'submitted' and not submission:
                continue
            elif status == 'unsubmitted' and submission:
                continue
            
            filtered_results.append((assignment, tc, course, submission))
        
        writer.writerow(['作业标题', '类型', '课程名称', '教学班', '发布时间', '截止时间', '提交状态', '成绩'])
        for assignment, tc, course, submission in filtered_results:
            type_name = '📝 作业' if assignment.type == 'homework' else '📄 考试'
            submit_status = '已提交' if submission else '未提交'
            score = f'{submission.score:.1f}' if submission and submission.score else '-'
            
            writer.writerow([
                assignment.title,
                type_name,
                course.course_name,
                tc.class_name,
                assignment.create_time.strftime('%Y-%m-%d %H:%M'),
                assignment.deadline.strftime('%Y-%m-%d %H:%M'),
                submit_status,
                score
            ])
        
        filename = f'作业考试查询_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
    elif query_type == 'grade':
        course_name = request.args.get('course_name', '')
        semester = request.args.get('semester', '')
        
        query = db.session.query(Grade, TeachingClass, Course).join(
            TeachingClass, Grade.class_id == TeachingClass.class_id
        ).join(
            Course, TeachingClass.course_id == Course.course_id
        ).filter(Grade.student_id == student_id)
        
        if course_name:
            query = query.filter(Course.course_name.like(f'%{course_name}%'))
        if semester:
            query = query.filter(TeachingClass.semester.like(f'%{semester}%'))
        
        results = query.all()
        
        writer.writerow(['课程名称', '教学班', '学期', '平时成绩', '期末成绩', '教师评分', '最终成绩'])
        for grade, tc, course in results:
            writer.writerow([
                course.course_name,
                tc.class_name,
                tc.semester,
                f'{grade.regular_grade:.1f}' if grade.regular_grade else '-',
                f'{grade.exam_grade:.1f}' if grade.exam_grade else '-',
                f'{grade.teacher_score:.1f}' if grade.teacher_score else '-',
                f'{grade.final_grade:.1f}' if grade.final_grade else '-'
            ])
        
        filename = f'我的成绩_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    else:
        flash('无效的查询类型', 'danger')
        return redirect(url_for('student_query'))
    
    output.seek(0)
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response


# ==================== 应用启动和数据库初始化 -----------------------
if __name__ == '__main__':
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库连接并初始化完成。")

        # --- 新增：检查并创建初始管理员 ---
        admin_user = Users.query.filter_by(username='admin').first()
        if not admin_user:
            print("正在创建初始管理员账户 'admin'...")
            try:
                # 初始管理员信息
                admin_username = 'admin'
                admin_password = 'admin_password' # 🚨 请务必替换为您的实际初始密码！
                admin_realname = '系统管理员'
                
                # 查找可用的admin_no
                admin_no = 'A001'
                counter = 1
                while Admin.query.filter_by(admin_no=admin_no).first():
                    counter += 1
                    admin_no = f'A{counter:03d}'
                
                # 生成新的 user_id 和 admin_id
                max_user = db.session.query(db.func.max(Users.user_id)).scalar()
                new_user_id = (max_user or 0) + 1
                max_admin = db.session.query(db.func.max(Admin.admin_id)).scalar()
                new_admin_id = (max_admin or 0) + 1
                
                new_user = Users(
                    user_id=new_user_id,
                    username=admin_username,
                    real_name=admin_realname,
                    role='admin',
                    status=1 
                )
                new_user.set_password(admin_password)
                db.session.add(new_user)
                
                # 创建系统管理部部门
                dept_id = get_or_create_department('系统管理部')
                
                new_admin = Admin(
                    admin_id=new_admin_id,
                    user_id=new_user_id,
                    admin_no=admin_no,
                    dept_id=dept_id,
                    permission_level=1  # 初始管理员拥有最高权限
                )
                db.session.add(new_admin)
                db.session.commit()
                print(f"✅ 初始管理员 {admin_username} 创建成功，密码：{admin_password}。")
            
            except Exception as e:
                db.session.rollback()
                print(f"❌ 初始管理员创建失败: {e}")
        else:
            # 如果Users表中有admin用户，检查Admin表中是否有对应记录
            admin_record = Admin.query.filter_by(user_id=admin_user.user_id).first()
            if not admin_record:
                print("检测到admin用户缺少Admin表记录，正在修复...")
                try:
                    max_admin = db.session.query(db.func.max(Admin.admin_id)).scalar()
                    new_admin_id = (max_admin or 0) + 1
                    
                    # 查找可用的admin_no
                    admin_no = 'A001'
                    counter = 1
                    while Admin.query.filter_by(admin_no=admin_no).first():
                        counter += 1
                        admin_no = f'A{counter:03d}'
                    
                    new_admin = Admin(
                        admin_id=new_admin_id,
                        user_id=admin_user.user_id,
                        admin_no=admin_no,
                        name=admin_user.real_name or '系统管理员',
                        department='系统管理部',
                        permission_level=1  # 修复时也给予最高权限
                    )
                    db.session.add(new_admin)
                    db.session.commit()
                    print(f"✅ Admin表记录修复成功，管理员编号: {admin_no}")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Admin表记录修复失败: {e}")
            else:
                print("管理员账户 'admin' 已存在，跳过创建。")
        # ------------------------------------
    
    # 启动Flask应用
    app.run(debug=True)