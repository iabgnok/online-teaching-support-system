from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_login import UserMixin   # type: ignore
from sqlalchemy.sql import func  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash   # type: ignore

db = SQLAlchemy()

def generate_next_id(model, id_field='id'):
    """生成模型的下一个ID"""
    max_id = db.session.query(db.func.max(getattr(model, id_field))).scalar()
    return (max_id or 0) + 1

# ==================== 基础数据模块 ====================

class Department(db.Model):
    """部门表：统一管理所有部门信息"""
    __tablename__ = 'Department'

    dept_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系：Department -> Student/Teacher/Admin (一对多)
    students = db.relationship('Student', backref='department', lazy='dynamic')
    teachers = db.relationship('Teacher', backref='department', lazy='dynamic')
    admins = db.relationship('Admin', backref='department', lazy='dynamic')

# ==================== 用户管理模块 ====================

class Users(db.Model, UserMixin):
    """用户表：统一存放所有用户（管理员、教师、学生）的基本信息"""
    __tablename__ = 'Users'

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column('password', db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))  # 用户头像URL
    role = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'teacher', 'student'
    status = db.Column(db.SmallInteger, default=1, index=True)  # 0=禁用, 1=激活
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 密码管理
    @property
    def password(self):
        """防止直接读取密码哈希值"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """设置密码时自动加密"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def check_password(self, password):
        """验证密码（别名）"""
        return self.verify_password(password)

    def set_password(self, raw_password):
        """设置密码（兼容明文和哈希密码）"""
        if raw_password is None:
            return
        if self.is_hashed_password(raw_password):
            self.password_hash = raw_password
        else:
            self.password_hash = generate_password_hash(raw_password)

    @staticmethod
    def is_hashed_password(value):
        """判断是否为哈希密码"""
        if not value or not isinstance(value, str):
            return False
        return value.startswith(('pbkdf2:', 'scrypt:', 'argon2:'))

    def get_id(self):
        """返回Flask-Login需要的用户ID"""
        return str(self.user_id)

    # 关系：User -> Admin/Student/Teacher (一对一)
    admin_profile = db.relationship('Admin', backref='user', uselist=False)
    student_profile = db.relationship('Student', backref='user', uselist=False)
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)


class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'Admin'

    admin_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id', name='FK_Admin_User'), unique=True, nullable=False)
    admin_no = db.Column(db.String(20), unique=True, nullable=False)
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id', name='FK_Admin_Department'))
    
    # 权限等级: 1=超级管理员, 2=系统管理员, 3=部门管理员, 4=内容审核员
    permission_level = db.Column(db.SmallInteger, default=4)
    
    # 权限范围标记 (逗号分隔)
    permissions = db.Column(db.String(500), default='')  # 如: 'user_manage,forum_manage,announcement_manage'
    
    # 审核权限特定字段
    can_manage_users = db.Column(db.Boolean, default=False)  # 用户管理
    can_manage_forum = db.Column(db.Boolean, default=False)  # 论坛管理
    can_manage_courses = db.Column(db.Boolean, default=False)  # 课程管理
    can_manage_grades = db.Column(db.Boolean, default=False)  # 成绩管理
    can_manage_announcements = db.Column(db.Boolean, default=False)  # 公告管理
    can_review_content = db.Column(db.Boolean, default=False)  # 内容审核
    can_ban_users = db.Column(db.Boolean, default=False)  # 禁用用户
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def has_permission(self, level):
        """检查是否有指定级别的权限（数字越小权限越高）"""
        return self.permission_level <= level
    
    def has_feature_permission(self, feature):
        """检查是否有特定功能权限"""
        feature_map = {
            'user_manage': 'can_manage_users',
            'forum_manage': 'can_manage_forum',
            'courses_manage': 'can_manage_courses',
            'grades_manage': 'can_manage_grades',
            'announcements_manage': 'can_manage_announcements',
            'content_review': 'can_review_content',
            'ban_users': 'can_ban_users'
        }
        attr = feature_map.get(feature)
        return getattr(self, attr, False) if attr else False
    
    def grant_permission(self, feature):
        """授予权限"""
        attr = {
            'user_manage': 'can_manage_users',
            'forum_manage': 'can_manage_forum',
            'courses_manage': 'can_manage_courses',
            'grades_manage': 'can_manage_grades',
            'announcements_manage': 'can_manage_announcements',
            'content_review': 'can_review_content',
            'ban_users': 'can_ban_users'
        }.get(feature)
        if attr:
            setattr(self, attr, True)
    
    def revoke_permission(self, feature):
        """撤销权限"""
        attr = {
            'user_manage': 'can_manage_users',
            'forum_manage': 'can_manage_forum',
            'courses_manage': 'can_manage_courses',
            'grades_manage': 'can_manage_grades',
            'announcements_manage': 'can_manage_announcements',
            'content_review': 'can_review_content',
            'ban_users': 'can_ban_users'
        }.get(feature)
        if attr:
            setattr(self, attr, False)
    
    @property
    def name(self):
        """获取管理员姓名"""
        return self.user.real_name if self.user else None




class Student(db.Model):
    """学生表"""
    __tablename__ = 'Student'

    student_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id', name='FK_Student_User'), unique=True, nullable=False)
    student_no = db.Column(db.CHAR(10), unique=True, nullable=False)
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id', name='FK_Student_Department'))
    major = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系：Student -> StudentClass/Submission/Grade (一对多)
    enrollments = db.relationship('StudentClass', backref='student', lazy='dynamic')
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')
    grades = db.relationship('Grade', backref='student', lazy='dynamic')
    
    @property
    def name(self):
        """获取学生姓名"""
        return self.user.real_name if self.user else None


class Teacher(db.Model):
    """教师表"""
    __tablename__ = 'Teacher'

    teacher_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id', name='FK_Teacher_User'), unique=True, nullable=False)
    teacher_no = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(50))
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id', name='FK_Teacher_Department'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系：Teacher -> TeacherClass/Material/Assignment/Grade/Submission (一对多)
    teaching_assignments = db.relationship('TeacherClass', backref='teacher', lazy='dynamic')
    materials = db.relationship('Material', backref='teacher', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='teacher', lazy='dynamic')
    calculated_grades = db.relationship('Grade', backref='calculator', lazy='dynamic', foreign_keys='Grade.calculated_by')
    graded_submissions = db.relationship('Submission', backref='grader', lazy='dynamic', foreign_keys='Submission.graded_by')
    
    @property
    def name(self):
        """获取教师姓名"""
        return self.user.real_name if self.user else None
 
# -----------------------------------------------------------
# 2. 教学基础模块
# -----------------------------------------------------------

class Course(db.Model):
    """课程表 (dbo.Course)"""
    __tablename__ = 'Course'

    # 字段定义 [cite: 8]
    course_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    course_code = db.Column(db.String(50), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    credit = db.Column(db.Numeric(3, 1))
    hours = db.Column(db.Integer)
    course_type = db.Column(db.String(50))
    # NVARCHAR(MAX) 对应 Text
    description = db.Column(db.Text) 
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系定义：Course -> TeachingClass (一对多)
    teaching_classes = db.relationship('TeachingClass', backref='course', lazy='dynamic')


class TeachingClass(db.Model):
    """教学班表"""
    __tablename__ = 'TeachingClass'

    class_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    course_id = db.Column(db.BigInteger, db.ForeignKey('Course.course_id', name='FK_TeachingClass_Course'), nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False, index=True)
    class_time = db.Column(db.String(200))
    classroom = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    status = db.Column(db.SmallInteger, default=1, index=True)  # 0=禁用, 1=激活
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系：TeachingClass -> StudentClass/TeacherClass/Material/Assignment/Grade (一对多)
    enrollments = db.relationship('StudentClass', backref='teaching_class', lazy='dynamic')
    teachers = db.relationship('TeacherClass', backref='teaching_class', lazy='dynamic')
    materials = db.relationship('Material', backref='teaching_class', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='teaching_class', lazy='dynamic')
    grades = db.relationship('Grade', backref='teaching_class', lazy='dynamic')


class StudentClass(db.Model):
    """学生选课关系表"""
    __tablename__ = 'StudentClass'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id', name='FK_StudentClass_Student'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_StudentClass_Class'), nullable=False)
    enroll_time = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.SmallInteger, default=1)  # 0=退课, 1=正常

    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_StudentClass_Student_Class'),
    )


class TeacherClass(db.Model):
    """教师任课关系表"""
    __tablename__ = 'TeacherClass'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_TeacherClass_Teacher'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_TeacherClass_Class'), nullable=False)
    role = db.Column(db.String(20), default='main')  # 'main'=主讲, 'assistant'=助教
    assign_time = db.Column(db.DateTime(timezone=True), default=func.now())

    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'class_id', name='UK_TeacherClass_Teacher_Class'),
    )

# ==================== 教学资源模块 ====================

class Material(db.Model):
    """教学资料表"""
    __tablename__ = 'Material'

    material_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_Material_Class'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_Material_Teacher'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    file_type = db.Column(db.String(50))
    download_count = db.Column(db.Integer, default=0)
    publish_time = db.Column(db.DateTime(timezone=True), default=func.now())


# ==================== 作业考试模块 ====================

class Assignment(db.Model):
    """作业/考试表"""
    __tablename__ = 'Assignment'

    assignment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_Assignment_Class'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_Assignment_Teacher'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'homework'=作业, 'exam'=考试
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_score = db.Column(db.Numeric(5, 2), nullable=False, default=100.00)
    deadline = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    start_time = db.Column(db.DateTime(timezone=True))  # 考试特有
    duration = db.Column(db.Integer)  # 考试时长(分钟)
    publish_time = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.SmallInteger, default=1, index=True)  # 0=关闭, 1=开放

    # 关系：Assignment -> Submission (一对多)
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic')


class Submission(db.Model):
    """作业提交记录表"""
    __tablename__ = 'Submission'

    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    assignment_id = db.Column(db.BigInteger, db.ForeignKey('Assignment.assignment_id', name='FK_Submission_Assignment'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id', name='FK_Submission_Student'), nullable=False)
    content = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    submit_time = db.Column(db.DateTime(timezone=True), default=func.now())
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    graded_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_Submission_Grader'))
    graded_time = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='submitted', index=True)  # 'submitted'=已提交, 'graded'=已批改

    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='UK_Submission_Assignment_Student'),
    )

# ==================== 成绩管理模块 ====================

class Grade(db.Model):
    """成绩表：存储最终归档的成绩（保留用于兼容）"""
    __tablename__ = 'Grade'

    grade_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id', name='FK_Grade_Student'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_Grade_Class'), nullable=False)
    
    # 归档的最终成绩（教师确认后不再变动）
    homework_avg = db.Column(db.Numeric(5, 2), comment='最终作业平均分（归档值）')
    exam_avg = db.Column(db.Numeric(5, 2), comment='最终考试平均分（归档值）')
    teacher_evaluation = db.Column(db.Numeric(5, 2), comment='最终教师评价分（归档值）')
    final_grade = db.Column(db.Numeric(5, 2), comment='最终总评成绩（归档值）')
    
    # 成绩归档状态
    is_finalized = db.Column(db.Boolean, default=False, nullable=False, index=True, comment='是否已确定归档')
    finalized_at = db.Column(db.DateTime(timezone=True), comment='成绩确定时间')
    calculation_formula = db.Column(db.String(200), comment='成绩计算公式，如: hw*0.3+exam*0.5+eval*0.2')
    
    # 审计字段
    calculated_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_Grade_Calculator'))
    calculated_at = db.Column(db.DateTime(timezone=True))
    remarks = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_Grade_Student_Class'),
    )
    
    def is_locked(self):
        """成绩是否已锁定"""
        return self.is_finalized
    
    def finalize(self, teacher_id, formula='hw*0.3+exam*0.5+eval*0.2'):
        """归档并锁定成绩"""
        from datetime import datetime
        self.is_finalized = True
        self.finalized_at = datetime.now()
        self.calculated_by = teacher_id
        self.calculated_at = datetime.now()
        self.calculation_formula = formula


class GradeCategory(db.Model):
    """成绩分类/组别表"""
    __tablename__ = 'GradeCategory'
    
    id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, comment='分类名称，如：平时成绩、作业、考试')
    weight = db.Column(db.Numeric(5, 2), nullable=False, default=0, comment='权重（百分比），如30表示30%')
    description = db.Column(db.String(200), comment='说明')
    order = db.Column(db.Integer, default=0, comment='排序')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    items = db.relationship('GradeItem', backref='category', lazy='dynamic', cascade='all, delete-orphan')


class GradeItem(db.Model):
    """成绩项表（可自定义的成绩项）"""
    __tablename__ = 'GradeItem'
    
    id = db.Column(db.BigInteger, primary_key=True)
    category_id = db.Column(db.BigInteger, db.ForeignKey('GradeCategory.id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False, comment='成绩项名称，如：期中考试、实验报告1')
    item_type = db.Column(db.String(20), nullable=False, comment='类型：assignment, exam, attendance, manual')
    weight = db.Column(db.Numeric(5, 2), comment='在分类内的权重')
    max_score = db.Column(db.Numeric(5, 2), default=100, comment='满分')
    
    # 关联字段
    related_assignment_id = db.Column(db.BigInteger, db.ForeignKey('Assignment.assignment_id'), comment='关联的作业/考试ID')
    
    # 配置
    auto_calculate = db.Column(db.Boolean, default=False, comment='是否自动计算（如考勤）')
    is_published = db.Column(db.Boolean, default=False, comment='是否对学生公开')
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    created_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    
    # 关系
    scores = db.relationship('StudentGradeScore', backref='grade_item', lazy='dynamic', cascade='all, delete-orphan')


class StudentGradeScore(db.Model):
    """学生成绩明细表"""
    __tablename__ = 'StudentGradeScore'
    
    id = db.Column(db.BigInteger, primary_key=True)
    grade_item_id = db.Column(db.BigInteger, db.ForeignKey('GradeItem.id'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    
    score = db.Column(db.Numeric(5, 2), comment='得分')
    percentage = db.Column(db.Numeric(5, 2), comment='得分率（百分制）')
    
    # 审计
    graded_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    graded_at = db.Column(db.DateTime(timezone=True))
    remarks = db.Column(db.String(500))
    
    __table_args__ = (
        db.UniqueConstraint('grade_item_id', 'student_id', name='UK_GradeScore_Item_Student'),
    )


class StudentFinalGrade(db.Model):
    """学生总评成绩表"""
    __tablename__ = 'StudentFinalGrade'
    
    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    
    # 各分类得分
    category_scores = db.Column(db.JSON, comment='各分类得分详情，JSON格式')
    
    # 总评
    total_score = db.Column(db.Numeric(5, 2), comment='总评成绩')
    rank = db.Column(db.Integer, comment='班级排名')
    rank_percentage = db.Column(db.Numeric(5, 2), comment='排名百分位')
    
    # 状态
    is_finalized = db.Column(db.Boolean, default=False, comment='是否已归档')
    is_published = db.Column(db.Boolean, default=False, comment='是否对学生公开')
    
    calculated_at = db.Column(db.DateTime(timezone=True))
    finalized_at = db.Column(db.DateTime(timezone=True))
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_FinalGrade_Student_Class'),
    )


# ==================== 教学计划与任务日历模块 ====================

class TeachingPlan(db.Model):
    """教学计划表 - 教师创建的教学进度计划"""
    __tablename__ = 'TeachingPlan'
    
    plan_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id', name='FK_TeachingPlan_Teacher'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id', name='FK_TeachingPlan_Class'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)  # 计划标题，如"第1章 绪论"
    description = db.Column(db.Text)  # 详细描述
    
    planned_date = db.Column(db.DateTime(timezone=True), nullable=False, index=True)  # 计划日期
    duration_minutes = db.Column(db.Integer, default=60)  # 预计时长（分钟）
    
    # 同步到学生端的开关
    sync_to_students = db.Column(db.Boolean, default=False)  # 是否同步到学生端
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系
    teaching_class = db.relationship('TeachingClass', backref='teaching_plans')
    teacher = db.relationship('Teacher', backref='teaching_plans')


class PersonalTask(db.Model):
    """个人任务表 - 学生自己添加的学习计划"""
    __tablename__ = 'PersonalTask'
    
    task_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id', name='FK_PersonalTask_Student'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)  # 任务标题
    description = db.Column(db.Text)  # 任务描述
    
    planned_date = db.Column(db.DateTime(timezone=True), nullable=False, index=True)  # 计划完成日期
    duration_minutes = db.Column(db.Integer, default=60)  # 预计时长（分钟）
    
    is_completed = db.Column(db.Boolean, default=False)  # 是否完成
    completed_at = db.Column(db.DateTime(timezone=True))  # 完成时间
    
    priority = db.Column(db.String(20), default='normal')  # 优先级: low, normal, high
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系
    student = db.relationship('Student', backref='personal_tasks')


# ==================== Phase 1: 增强功能模块 ====================

class Announcement(db.Model):
    """系统公告与通知"""
    __tablename__ = 'Announcement'

    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    # Scope: 'global' (全站) 或 'class' (班级)
    scope_type = db.Column(db.String(20), nullable=False, default='global', index=True) 
    # 如果是班级通知，关联班级ID
    target_class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Relationships
    author = db.relationship('Users', backref='announcements')
    target_class = db.relationship('TeachingClass', backref='announcements')

class Attendance(db.Model):
    """考勤记录主表"""
    __tablename__ = 'Attendance'

    id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 签到模式字段
    is_self_checkin = db.Column(db.Boolean, default=False) # 是否为学生自签模式
    start_time = db.Column(db.DateTime(timezone=True))     # 签到开始时间
    end_time = db.Column(db.DateTime(timezone=True))       # 正常签到截止时间 (超过此时间算迟到)
    close_time = db.Column(db.DateTime(timezone=True))     # 签到关闭时间 (超过此时间无法签到)

    # Relationships
    teaching_class = db.relationship('TeachingClass', backref='attendances')
    records = db.relationship('AttendanceRecord', backref='attendance', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_status(self):
        """获取当前签到状态"""
        from datetime import datetime
        now = datetime.now()
        if not self.is_self_checkin:
            return 'manual' # 手动录入
        if now <= self.end_time:
            return 'active' # 正在进行
        elif now <= self.close_time:
            return 'late'   # 迟到阶段
        else:
            return 'closed' # 已结束

class AttendanceRecord(db.Model):
    """学生考勤详情表"""
    __tablename__ = 'AttendanceRecord'
    
    id = db.Column(db.BigInteger, primary_key=True)
    attendance_id = db.Column(db.BigInteger, db.ForeignKey('Attendance.id'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present') # 'present', 'absent', 'late', 'leave'
    remarks = db.Column(db.String(200)) # 备注，例如迟到原因

    # Relationship
    student = db.relationship('Student', backref='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('attendance_id', 'student_id', name='UK_AttendanceRecord_Student'),
    )


# ==================== Phase 2: 互动与沟通模块 ====================

class ForumPost(db.Model):
    """课程讨论区帖子"""
    __tablename__ = 'ForumPost'

    id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 状态字段
    is_pinned = db.Column(db.Boolean, default=False) # 置顶
    is_solved = db.Column(db.Boolean, default=False) # 已解决 (如果是提问)
    view_count = db.Column(db.Integer, default=0)
    
    # 附件字段
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))

    # Relationships
    teaching_class = db.relationship('TeachingClass', backref='forum_posts')
    author = db.relationship('Users', backref='posts')
    comments = db.relationship('ForumComment', backref='post', lazy='dynamic', cascade='all, delete-orphan')


class ForumComment(db.Model):
    """帖子回复/评论"""
    __tablename__ = 'ForumComment'

    id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(db.BigInteger, db.ForeignKey('ForumPost.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    parent_id = db.Column(db.BigInteger, db.ForeignKey('ForumComment.id'), nullable=True) # 支持楼中楼
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    is_accepted_answer = db.Column(db.Boolean, default=False) # 标记为标准/最佳答案

    # Relationships
    author = db.relationship('Users', backref='comments')
    replies = db.relationship('ForumComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')


class Message(db.Model):
    """站内信 (私信)"""
    __tablename__ = 'Message'

    id = db.Column(db.BigInteger, primary_key=True)
    sender_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    recipient_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    read_at = db.Column(db.DateTime(timezone=True), nullable=True) # 读取时间，为空则未读
    
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False)

    # Relationships
    sender = db.relationship('Users', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('Users', foreign_keys=[recipient_id], backref='received_messages')


class ForumModeration(db.Model):
    """论坛内容审核日志"""
    __tablename__ = 'ForumModeration'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    
    # 审核对象：帖子或评论
    content_type = db.Column(db.String(20), nullable=False)  # 'post' 或 'comment'
    post_id = db.Column(db.BigInteger, db.ForeignKey('ForumPost.id'), nullable=True)
    comment_id = db.Column(db.BigInteger, db.ForeignKey('ForumComment.id'), nullable=True)
    
    # 操作信息
    admin_id = db.Column(db.BigInteger, db.ForeignKey('Admin.admin_id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'pin', 'unpin', 'delete', 'hide', 'unhide', 'warn', 'lock', 'unlock'
    reason = db.Column(db.Text)  # 操作原因
    
    # 内容快照（用于记录被删除的内容）
    content_snapshot = db.Column(db.Text)  # 操作前的内容备份
    
    # 状态
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'reversed'
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    reversed_at = db.Column(db.DateTime(timezone=True), nullable=True)  # 撤销时间
    reversed_by = db.Column(db.BigInteger, db.ForeignKey('Admin.admin_id'), nullable=True)  # 谁撤销的
    
    # Relationships
    post = db.relationship('ForumPost', backref='moderation_records')
    comment = db.relationship('ForumComment', backref='moderation_records')
    reverser = db.relationship('Admin', foreign_keys=[reversed_by], backref='reversed_moderations')


class ForumPostStatus(db.Model):
    """论坛帖子状态追踪（隐藏、锁定等）"""
    __tablename__ = 'ForumPostStatus'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    post_id = db.Column(db.BigInteger, db.ForeignKey('ForumPost.id'), nullable=False, unique=True)
    
    # 状态标记
    is_hidden = db.Column(db.Boolean, default=False)  # 隐藏（仅管理员和作者可见）
    is_locked = db.Column(db.Boolean, default=False)  # 锁定（禁止评论）
    is_flagged = db.Column(db.Boolean, default=False)  # 被标记为需要审核
    
    # 隐藏/锁定原因
    hide_reason = db.Column(db.String(255))  # 隐藏原因
    lock_reason = db.Column(db.String(255))  # 锁定原因
    
    # 警告信息
    warning_level = db.Column(db.SmallInteger, default=0)  # 0=无警告, 1=轻度, 2=中度, 3=严重
    warning_message = db.Column(db.Text)  # 警告信息
    
    # 审核人员
    hidden_by = db.Column(db.BigInteger, db.ForeignKey('Admin.admin_id'), nullable=True)
    locked_by = db.Column(db.BigInteger, db.ForeignKey('Admin.admin_id'), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    post = db.relationship('ForumPost', backref='status_tracking')
    hider = db.relationship('Admin', foreign_keys=[hidden_by], backref='hidden_posts')
    locker = db.relationship('Admin', foreign_keys=[locked_by], backref='locked_posts')


# ==================== 子模式视图（只读） ====================

class VStudentMyCourses(db.Model):
    """学生选课视图 - 只读"""
    __tablename__ = 'V_Student_MyCourses'
    __table_args__ = {'info': {'is_view': True}}
    
    student_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, primary_key=True)
    course_id = db.Column(db.BigInteger)
    course_name = db.Column(db.String(100))
    course_code = db.Column(db.String(50))
    credit = db.Column(db.Numeric(3, 1))
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    class_time = db.Column(db.String(200))
    classroom = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    teacher_name = db.Column(db.String(50))
    teacher_no = db.Column(db.String(20))
    enroll_time = db.Column(db.DateTime(timezone=True))
    enrollment_status = db.Column(db.SmallInteger)


class VStudentMyAssignments(db.Model):
    """学生作业视图 - 只读"""
    __tablename__ = 'V_Student_MyAssignments'
    __table_args__ = {'info': {'is_view': True}}
    
    student_id = db.Column(db.BigInteger, primary_key=True)
    assignment_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger)
    assignment_title = db.Column(db.String(200))
    assignment_type = db.Column(db.String(20))
    description = db.Column(db.Text)
    total_score = db.Column(db.Numeric(5, 2))
    deadline = db.Column(db.DateTime(timezone=True))
    publish_time = db.Column(db.DateTime(timezone=True))
    course_name = db.Column(db.String(100))
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    submission_id = db.Column(db.BigInteger)
    submit_time = db.Column(db.DateTime(timezone=True))
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    submission_status = db.Column(db.String(20))
    status_display = db.Column(db.String(50))
    is_overdue = db.Column(db.Integer)


class VStudentMyGrades(db.Model):
    """学生成绩视图 - 只读"""
    __tablename__ = 'V_Student_MyGrades'
    __table_args__ = {'info': {'is_view': True}}
    
    student_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, primary_key=True)
    course_id = db.Column(db.BigInteger)
    course_name = db.Column(db.String(100))
    course_code = db.Column(db.String(50))
    credit = db.Column(db.Numeric(3, 1))
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    homework_avg = db.Column(db.Numeric(5, 2))
    exam_avg = db.Column(db.Numeric(5, 2))
    teacher_evaluation = db.Column(db.Numeric(5, 2))
    final_grade = db.Column(db.Numeric(5, 2))
    remarks = db.Column(db.Text)
    is_finalized = db.Column(db.Boolean)
    finalized_at = db.Column(db.DateTime(timezone=True))
    calculation_formula = db.Column(db.String(200))
    calculator_name = db.Column(db.String(50))


class VTeacherMyClasses(db.Model):
    """教师教学班视图 - 只读"""
    __tablename__ = 'V_Teacher_MyClasses'
    __table_args__ = {'info': {'is_view': True}}
    
    teacher_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, primary_key=True)
    course_id = db.Column(db.BigInteger)
    course_name = db.Column(db.String(100))
    course_code = db.Column(db.String(50))
    credit = db.Column(db.Numeric(3, 1))
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    class_time = db.Column(db.String(200))
    classroom = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    my_role = db.Column(db.String(20))
    enrolled_count = db.Column(db.Integer)
    class_status = db.Column(db.SmallInteger)


class VTeacherStudentList(db.Model):
    """教师学生名单视图 - 只读"""
    __tablename__ = 'V_Teacher_StudentList'
    __table_args__ = {'info': {'is_view': True}}
    
    teacher_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.BigInteger, primary_key=True)
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    course_name = db.Column(db.String(100))
    student_no = db.Column(db.String(10))
    student_name = db.Column(db.String(50))
    dept_name = db.Column(db.String(100))
    major = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    enroll_time = db.Column(db.DateTime(timezone=True))


class VTeacherSubmissionStatus(db.Model):
    """作业提交统计视图 - 只读"""
    __tablename__ = 'V_Teacher_SubmissionStatus'
    __table_args__ = {'info': {'is_view': True}}
    
    teacher_id = db.Column(db.BigInteger, primary_key=True)
    assignment_id = db.Column(db.BigInteger, primary_key=True)
    class_id = db.Column(db.BigInteger)
    class_name = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    course_name = db.Column(db.String(100))
    assignment_title = db.Column(db.String(200))
    assignment_type = db.Column(db.String(20))
    deadline = db.Column(db.DateTime(timezone=True))
    total_score = db.Column(db.Numeric(5, 2))
    total_students = db.Column(db.Integer)
    submitted_count = db.Column(db.Integer)
    graded_count = db.Column(db.Integer)
    unsubmitted_count = db.Column(db.Integer)
    submission_rate = db.Column(db.Float)


class VAdminUserStatistics(db.Model):
    """管理员用户统计视图 - 只读"""
    __tablename__ = 'V_Admin_UserStatistics'
    __table_args__ = {'info': {'is_view': True}}
    
    dept_id = db.Column(db.BigInteger, primary_key=True)
    dept_name = db.Column(db.String(100))
    active_student_count = db.Column(db.Integer)
    active_teacher_count = db.Column(db.Integer)
    active_admin_count = db.Column(db.Integer)
    total_student_count = db.Column(db.Integer)
    total_teacher_count = db.Column(db.Integer)
    total_admin_count = db.Column(db.Integer)
    total_user_count = db.Column(db.Integer)


class VAdminCourseStatistics(db.Model):
    """管理员课程统计视图 - 只读"""
    __tablename__ = 'V_Admin_CourseStatistics'
    __table_args__ = {'info': {'is_view': True}}
    
    course_id = db.Column(db.BigInteger, primary_key=True)
    course_name = db.Column(db.String(100))
    course_code = db.Column(db.String(50))
    credit = db.Column(db.Numeric(3, 1))
    hours = db.Column(db.Integer)
    course_type = db.Column(db.String(50))
    total_class_count = db.Column(db.Integer)
    current_year_classes = db.Column(db.Integer)
    active_class_count = db.Column(db.Integer)
    total_enrollments = db.Column(db.Integer)
    active_enrollments = db.Column(db.Integer)

# ==================== 线上授课模块 ====================

class LiveClass(db.Model):
    """线上课堂表"""
    __tablename__ = 'LiveClass'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    lesson_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 课堂唯一标识
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)  # 课堂标题
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='active')  # active, ended
    participants_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系
    teacher = db.relationship('Users', backref='live_classes')
    teaching_class = db.relationship('TeachingClass', backref='live_classes')
    drawings = db.relationship('DrawingData', backref='live_class', lazy='dynamic')
    messages = db.relationship('ChatMessage', backref='live_class', lazy='dynamic')
    participants = db.relationship('LiveParticipant', backref='live_class', lazy='dynamic')


class DrawingData(db.Model):
    """画板绘制数据表"""
    __tablename__ = 'DrawingData'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    x_percent = db.Column(db.Float, nullable=False)  # 百分比坐标X
    y_percent = db.Column(db.Float, nullable=False)  # 百分比坐标Y
    color = db.Column(db.String(7), nullable=False)  # 颜色 #RRGGBB
    brush_size = db.Column(db.Float, default=2.0)  # 笔刷大小
    action = db.Column(db.String(20), default='draw')  # draw, erase
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)
    
    # 关系
    user = db.relationship('Users', backref='drawings')


class ChatMessage(db.Model):
    """课堂聊天消息表"""
    __tablename__ = 'ChatMessage'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, emoji, system
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)
    
    # 关系
    user = db.relationship('Users', backref='chat_messages')


class LiveParticipant(db.Model):
    """课堂参与者表"""
    __tablename__ = 'LiveParticipant'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=func.now())
    left_at = db.Column(db.DateTime(timezone=True))
    role = db.Column(db.String(20), default='student')  # teacher, student
    
    # 关系
    user = db.relationship('Users', backref='live_participations')


class ClassNote(db.Model):
    """课堂笔记表"""
    __tablename__ = 'ClassNote'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)  # 自动生成的笔记内容
    is_published = db.Column(db.Boolean, default=False)  # 是否发布给学生
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系
    live_class = db.relationship('LiveClass', backref='notes')
    teacher = db.relationship('Users', backref='class_notes')


# ==================== 即时通讯模块 (IM System) ====================

class Conversation(db.Model):
    """对话表 - 支持一对一、群聊、班级群组、课程群组和直播课堂"""
    __tablename__ = 'Conversation'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    conversation_type = db.Column(db.String(20), nullable=False, index=True)  # 'private', 'group', 'class_group', 'course_group', 'live_class'
    title = db.Column(db.String(200))  # 对话标题（群组名称，私聊时为空）
    avatar = db.Column(db.String(500))  # 群组头像URL
    description = db.Column(db.Text)  # 群组描述
    
    # Telegram 式群组功能
    group_subtype = db.Column(db.String(20), nullable=False, default='normal', index=True)  # 'normal', 'channel', 'discussion'
    conversation_subtype = db.Column(db.String(50), nullable=True, index=True)  # 对话子类型标签，如 'live_class_discussion'（课堂讨论区，只能由线上授课功能创建）
    linked_discussion_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=True)  # 频道绑定的讨论组ID
    linked_channel_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=True)  # 讨论组关联的频道ID
    
    # 关联信息
    created_by = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=True)  # 课程班级关联
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=True)  # 直播课堂关联
    
    # 状态
    is_archived = db.Column(db.Boolean, default=False)  # 是否归档
    is_active = db.Column(db.Boolean, default=True)  # 是否活跃
    
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now(), index=True)
    last_message_at = db.Column(db.DateTime(timezone=True))  # 最后一条消息时间
    
    # 关系
    creator = db.relationship('Users', foreign_keys=[created_by], backref='created_conversations')
    teaching_class = db.relationship('TeachingClass', foreign_keys=[class_id], backref='conversations')
    live_class_rel = db.relationship('LiveClass', foreign_keys=[live_class_id], backref='conversation', uselist=False)
    members = db.relationship('ConversationMember', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('IMMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan', order_by='IMMessage.created_at')


class ConversationMember(db.Model):
    """对话成员关系表"""
    __tablename__ = 'ConversationMember'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    
    # 角色和权限
    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member'
    
    # 个性化设置
    is_muted = db.Column(db.Boolean, default=False)  # 是否静音
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    custom_alias = db.Column(db.String(100))  # 自定义备注名
    
    # 阅读状态
    last_read_message_id = db.Column(db.BigInteger)  # 最后已读消息ID
    last_read_at = db.Column(db.DateTime(timezone=True))  # 最后阅读时间
    unread_count = db.Column(db.Integer, default=0)  # 未读计数
    
    # 草稿
    draft_content = db.Column(db.Text)  # 草稿内容
    draft_updated_at = db.Column(db.DateTime(timezone=True))
    
    # 时间戳
    joined_at = db.Column(db.DateTime(timezone=True), default=func.now())
    left_at = db.Column(db.DateTime(timezone=True))  # 退出时间（为空表示还在群组中）
    
    # 关系
    user = db.relationship('Users', backref='conversation_memberships')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('conversation_id', 'user_id', name='uq_conversation_member'),
        db.Index('idx_conversation_member_user', 'user_id', 'conversation_id'),
    )


class ChatFolder(db.Model):
    """聊天文件夹 - 用户自定义分组"""
    __tablename__ = 'ChatFolder'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50))  # 图标标识
    filter_type = db.Column(db.String(20), default='custom')  # 'all', 'unread', 'private', 'group', 'class', 'custom'
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    user = db.relationship('Users', backref='chat_folders')
    items = db.relationship('ChatFolderItem', backref='folder', lazy='dynamic', cascade='all, delete-orphan')


class ChatFolderItem(db.Model):
    """聊天文件夹成员"""
    __tablename__ = 'ChatFolderItem'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    folder_id = db.Column(db.BigInteger, db.ForeignKey('ChatFolder.id'), nullable=False, index=True)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    added_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    conversation = db.relationship('Conversation')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('folder_id', 'conversation_id', name='uq_chat_folder_item'),
    )


class IMMessage(db.Model):
    """即时通讯消息表 - 统一的消息模型"""
    __tablename__ = 'IMMessage'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=False, index=True)
    sender_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    
    # 消息内容（使用 UnicodeText 以支持 Emoji 等 Unicode 字符）
    message_type = db.Column(db.String(20), default='text', index=True)  # 'text', 'image', 'file', 'voice', 'video', 'system', 'emoji'
    content = db.Column(db.UnicodeText)  # 文本内容 - 支持完整 Unicode（包括 Emoji）
    
    # 媒体文件
    media_url = db.Column(db.String(500))  # 媒体文件URL
    file_name = db.Column(db.String(255))  # 原始文件名
    file_size = db.Column(db.BigInteger)  # 文件大小（字节）
    mime_type = db.Column(db.String(100))  # MIME类型
    
    # 引用和回复
    reply_to_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'))  # 回复的消息ID（已有字段，用于兼容）
    forward_from_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'))  # 转发来源消息ID
    
    # Telegram 式群组功能
    root_message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=True, index=True)  # 频道讨论：指向频道消息ID
    parent_message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=True, index=True)  # 普通群引用回复：指向父消息ID
    comment_count = db.Column(db.Integer, default=0)  # 评论数量（冗余字段，提升性能）
    
    # 扩展元数据（JSON格式）
    extra_data = db.Column(db.JSON)  # 如：提及的用户列表、链接预览、位置信息等
    
    # 状态标记
    is_edited = db.Column(db.Boolean, default=False)  # 是否已编辑
    is_deleted = db.Column(db.Boolean, default=False)  # 是否已删除
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)
    edited_at = db.Column(db.DateTime(timezone=True))  # 编辑时间
    deleted_at = db.Column(db.DateTime(timezone=True))  # 删除时间
    
    # 关系
    sender = db.relationship('Users', foreign_keys=[sender_id], backref='im_messages')
    reply_to = db.relationship('IMMessage', remote_side=[id], foreign_keys=[reply_to_id], backref='replies')
    forward_from = db.relationship('IMMessage', remote_side=[id], foreign_keys=[forward_from_id], backref='forwards')
    root_message = db.relationship('IMMessage', remote_side=[id], foreign_keys=[root_message_id], backref='comments')
    parent_message = db.relationship('IMMessage', remote_side=[id], foreign_keys=[parent_message_id], backref='thread_replies')
    status_records = db.relationship('MessageStatus', backref='message', lazy='dynamic', cascade='all, delete-orphan')


class MessageStatus(db.Model):
    """消息状态跟踪表"""
    __tablename__ = 'MessageStatus'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    
    # 状态
    status = db.Column(db.String(20), default='sent', index=True)  # 'sent', 'delivered', 'read'
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    user = db.relationship('Users', backref='message_statuses')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='uq_message_status'),
        db.Index('idx_message_status', 'message_id', 'user_id', 'status'),
    )


class UserOnlineStatus(db.Model):
    """用户在线状态表"""
    __tablename__ = 'UserOnlineStatus'
    
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), primary_key=True)
    is_online = db.Column(db.Boolean, default=False, index=True)
    last_seen = db.Column(db.DateTime(timezone=True), default=func.now())
    device_info = db.Column(db.String(200))  # 设备信息
    socket_id = db.Column(db.String(100))  # Socket连接ID
    
    # 关系
    user = db.relationship('Users', backref='online_status', uselist=False)


class MessageReaction(db.Model):
    """消息反应表 - 表情反馈"""
    __tablename__ = 'MessageReaction'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    reaction = db.Column(db.Unicode(20), nullable=False)  # 使用Unicode支持emoji: '👍', '❤️', '😂', '😮', '😢', '🙏'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    message = db.relationship('IMMessage', backref='reactions')
    user = db.relationship('Users', backref='message_reactions')
    
    # 唯一约束：每个用户对每条消息只能有一个反应
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='uq_message_reaction'),
        db.Index('idx_message_reaction', 'message_id', 'reaction'),
    )


class PinnedMessage(db.Model):
    """置顶消息表"""
    __tablename__ = 'PinnedMessage'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=False, index=True)
    message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=False, index=True)
    pinned_by = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    pinned_at = db.Column(db.DateTime(timezone=True), default=func.now())
    order_index = db.Column(db.Integer, default=0)  # 多条置顶消息的顺序
    
    # 关系
    conversation = db.relationship('Conversation', backref='pinned_messages')
    message = db.relationship('IMMessage', backref='pinned_records')
    pinner = db.relationship('Users', foreign_keys=[pinned_by])
    
    # 唯一约束：每条消息在每个对话中只能被置顶一次
    __table_args__ = (
        db.UniqueConstraint('conversation_id', 'message_id', name='uq_pinned_message'),
        db.Index('idx_conversation_pinned', 'conversation_id', 'order_index'),
    )


class MentionNotification(db.Model):
    """@ 提及通知表"""
    __tablename__ = 'MentionNotification'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=False, index=True)
    mentioned_user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    message = db.relationship('IMMessage', backref='mentions')
    mentioned_user = db.relationship('Users', backref='mention_notifications')
    
    # 索引
    __table_args__ = (
        db.Index('idx_user_unread_mentions', 'mentioned_user_id', 'is_read'),
    )


class ConversationFolder(db.Model):
    """对话分组文件夹表 - 类似 Telegram 的 Folders"""
    __tablename__ = 'ConversationFolder'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)  # '正在上课', '未读作业', '班级群'
    icon = db.Column(db.String(50))  # emoji 图标
    color = db.Column(db.String(20))  # 颜色标识
    order_index = db.Column(db.Integer, default=0)  # 排序
    is_system = db.Column(db.Boolean, default=False)  # 是否为系统预设分组
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    user = db.relationship('Users', backref='conversation_folders')
    
    __table_args__ = (
        db.Index('idx_user_folder', 'user_id', 'order_index'),
    )


class ConversationFolderItem(db.Model):
    """对话分组成员表"""
    __tablename__ = 'ConversationFolderItem'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    folder_id = db.Column(db.BigInteger, db.ForeignKey('ConversationFolder.id'), nullable=False, index=True)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('Conversation.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    folder = db.relationship('ConversationFolder', backref='items')
    conversation = db.relationship('Conversation', backref='folder_items')
    
    __table_args__ = (
        db.UniqueConstraint('folder_id', 'conversation_id', name='uq_folder_conversation'),
    )


# ==================== 联系人 / 好友系统 ====================
class FriendRequest(db.Model):
    """好友申请表"""
    __tablename__ = 'FriendRequest'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    requester_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    target_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'accepted', 'declined', 'cancelled'
    message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    responded_at = db.Column(db.DateTime(timezone=True))

    requester = db.relationship('Users', foreign_keys=[requester_id])
    target = db.relationship('Users', foreign_keys=[target_id])

    __table_args__ = (
        db.UniqueConstraint('requester_id', 'target_id', name='uq_friend_request'),
    )


class Friendship(db.Model):
    """朋友关系表（单向记录，双向插入以表示互为好友）"""
    __tablename__ = 'Friendship'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    friend_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    user = db.relationship('Users', foreign_keys=[user_id])
    friend = db.relationship('Users', foreign_keys=[friend_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='uq_friend_pair'),
    )


class ContactSetting(db.Model):
    """联系人设置：备注名、是否屏蔽等"""
    __tablename__ = 'ContactSetting'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    contact_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    alias = db.Column(db.String(100))
    is_blocked = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    user = db.relationship('Users', foreign_keys=[user_id])
    contact = db.relationship('Users', foreign_keys=[contact_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'contact_id', name='uq_contact_setting'),
    )


def create_friendship_and_private_conversation(user_a_id, user_b_id):
    """在两个用户之间创建 Friendship 记录（双向）并确保存在一个 private Conversation。
    返回 Conversation 对象（已存在则复用）。"""
    # 创建 Friendship（双向）
    existing_ab = Friendship.query.filter_by(user_id=user_a_id, friend_id=user_b_id).first()
    # 如果需要同时创建两条 Friendship，先分配连续的 id，避免同一事务内冲突
    existing_ba = Friendship.query.filter_by(user_id=user_b_id, friend_id=user_a_id).first()
    if not existing_ab and not existing_ba:
        base = generate_next_id(Friendship)
        db.session.add(Friendship(id=base, user_id=user_a_id, friend_id=user_b_id))
        db.session.add(Friendship(id=base + 1, user_id=user_b_id, friend_id=user_a_id))
    else:
        if not existing_ab:
            db.session.add(Friendship(id=generate_next_id(Friendship), user_id=user_a_id, friend_id=user_b_id))
        if not existing_ba:
            db.session.add(Friendship(id=generate_next_id(Friendship), user_id=user_b_id, friend_id=user_a_id))

    # 查找是否已有仅包含两人的 private 会话
    convs = Conversation.query.filter_by(conversation_type='private').all()
    for conv in convs:
        member_ids = [m.user_id for m in conv.members]
        if set(member_ids) == set([int(user_a_id), int(user_b_id)]):
            db.session.commit()
            return conv

    # 创建新的私聊会话，分配连续 ConversationMember id 避免事务内重复
    conv = Conversation(id=generate_next_id(Conversation), conversation_type='private', created_by=user_a_id)
    db.session.add(conv)
    db.session.flush()

    base_m = generate_next_id(ConversationMember)
    m1 = ConversationMember(id=base_m, conversation_id=conv.id, user_id=user_a_id, role='member')
    m2 = ConversationMember(id=base_m + 1, conversation_id=conv.id, user_id=user_b_id, role='member')
    db.session.add_all([m1, m2])

    db.session.commit()
    return conv


class RaiseHandRecord(db.Model):
    """举手记录表"""
    __tablename__ = 'RaiseHandRecord'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False, index=True)
    raised_at = db.Column(db.DateTime(timezone=True), default=func.now())
    handled_at = db.Column(db.DateTime(timezone=True))  # 老师处理的时间
    handled_by = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'))  # 哪位老师处理的
    status = db.Column(db.String(20), default='pending')  # 'pending', 'handled', 'cancelled'
    question = db.Column(db.Text)  # 学生的问题（可选）
    
    # 关系
    live_class = db.relationship('LiveClass', backref='raise_hand_records')
    user = db.relationship('Users', foreign_keys=[user_id], backref='raise_hands')
    handler = db.relationship('Users', foreign_keys=[handled_by], backref='handled_raise_hands')
    
    __table_args__ = (
        db.Index('idx_live_pending_hands', 'live_class_id', 'status'),
    )


class QuickCommand(db.Model):
    """快捷指令表 - 支持 /call, /quiz 等命令"""
    __tablename__ = 'QuickCommand'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'), nullable=False, index=True)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), nullable=False)
    command_type = db.Column(db.String(20), nullable=False)  # 'attendance', 'quiz', 'poll'
    title = db.Column(db.String(200))  # 命令标题
    config = db.Column(db.Text)  # JSON格式的配置
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    completed_at = db.Column(db.DateTime(timezone=True))
    
    # 关系
    live_class = db.relationship('LiveClass', backref='quick_commands')
    teacher = db.relationship('Users', backref='issued_commands')


class MessageAttachment(db.Model):
    """消息附件表 - 支持按类型筛选"""
    __tablename__ = 'MessageAttachment'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    message_id = db.Column(db.BigInteger, db.ForeignKey('IMMessage.id'), nullable=False, index=True)
    attachment_type = db.Column(db.String(20), nullable=False, index=True)  # 'image', 'document', 'video', 'audio', 'link'
    file_name = db.Column(db.String(200))
    file_url = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)  # 文件大小（字节）
    mime_type = db.Column(db.String(100))
    thumbnail_url = db.Column(db.String(500))  # 缩略图
    extra_data = db.Column(db.Text)  # JSON格式的额外信息
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # 关系
    message = db.relationship('IMMessage', backref='attachments')
    
    __table_args__ = (
        db.Index('idx_message_attachment_type', 'message_id', 'attachment_type'),
    )