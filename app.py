"""在线教学支持系统 - 主应用"""

# ==================== 导入依赖 ====================
from flask import Flask, redirect, url_for, request, flash, abort, send_file, make_response
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
    Assignment, Submission, Grade, Material, Department, Announcement, Attendance, AttendanceRecord, db,
    # 新成绩系统
    GradeCategory, GradeItem, StudentGradeScore, StudentFinalGrade,
    # 视图模型
    VStudentMyCourses, VStudentMyAssignments, VStudentMyGrades,
    VTeacherMyClasses, VTeacherStudentList, VTeacherSubmissionStatus,
    VAdminUserStatistics, VAdminCourseStatistics,
    generate_next_id # Import utility function
)

# ==================== 应用初始化 ====================
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# ==================== Blueprint Registration ====================
from api.v1 import api_v1
from api.v1.classes import classes_bp
from api.v1.assignments import assignments_bp
from api.v1.attendance import attendance_bp
from api.v1.grades import grades_bp
from api.v1.admin import admin_bp
from api.v1.forum_management import forum_mgmt_bp

app.register_blueprint(api_v1)
app.register_blueprint(classes_bp, url_prefix='/api/v1/classes')
app.register_blueprint(assignments_bp, url_prefix='/api/v1/assignments')
app.register_blueprint(attendance_bp, url_prefix='/api/v1/attendance')
app.register_blueprint(grades_bp)
app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
app.register_blueprint(forum_mgmt_bp)

# ==================== 扩展初始化 ====================
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Session配置
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境使用HTTP
app.config['SESSION_COOKIE_HTTPONLY'] = True

# 确保上传目录存在
os.makedirs(app.config['MATERIALS_FOLDER'], exist_ok=True)
os.makedirs(app.config['ASSIGNMENTS_FOLDER'], exist_ok=True)

# ----------------------- 辅助函数 -----------------------

# generate_next_id check moved to models.py

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
                abort(403)
            admin = current_user.admin_profile
            if not admin or not admin.has_permission(level):
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ==================== 用户认证路由 ====================

if __name__ == '__main__':
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        # 确保默认部门存在
        get_or_create_department('系统管理部')
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
    
    # 启动前端并运行 Flask 应用
    import threading
    import subprocess
    import socket
    import time
    import webbrowser
    import os

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def start_frontend_and_open_browser():
        vue_port = 5173
        frontend_started = False
        
        if not is_port_in_use(vue_port):
            print(f"⏳ 检测到前端未启动 (端口 {vue_port} 空闲)，正在启动 Vue 前端...")
            frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
            # 兼容 Windows 
            npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
            
            try:
                subprocess.Popen([npm_cmd, 'run', 'dev'], cwd=frontend_dir, shell=True)
                print("✅ Vue 前端启动指令已发送，正在等待启动...")
                frontend_started = True
                
                # 等待几秒让它启动
                for _ in range(15):
                    if is_port_in_use(vue_port):
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"❌ 启动 Vue 前端失败: {e}")
        else:
             print(f"✅ 检测到前端已在端口 {vue_port} 运行")
             frontend_started = True

        if frontend_started:
            frontend_url = f'http://localhost:{vue_port}'
            print("\n" + "="*60)
            print(" 🚀 后端服务已启动 (Backend running on port 5000)")
            print(f" 🌐 前端访问地址 (Vue Frontend): {frontend_url}")
            print("="*60 + "\n")
            # 尝试打开浏览器
            try:
                webbrowser.open(frontend_url)
            except:
                pass

    # 仅在主进程中检查/启动前端 (避免 Reload 时重复启动)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # 使用线程启动，以免阻塞 Flask 启动
        threading.Thread(target=start_frontend_and_open_browser).start()

    app.run(debug=True, port=5000)
