
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
# 假设 db 已经初始化为 SQLAlchemy 实例
db = SQLAlchemy()
# -----------------------------------------------------------
# 0. 基础数据模块
# -----------------------------------------------------------

class Department(db.Model):
    """
    部门表 (dbo.Department)
    统一管理所有部门信息，避免数据冗余
    """
    __tablename__ = 'Department'

    dept_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系定义：Department -> Student/Teacher/Admin (一对多)
    students = db.relationship('Student', backref='department', lazy='dynamic')
    teachers = db.relationship('Teacher', backref='department', lazy='dynamic')
    admins = db.relationship('Admin', backref='department', lazy='dynamic')

# -----------------------------------------------------------
# 1. 用户管理模块
# -----------------------------------------------------------

class Users(db.Model, UserMixin):
    """
    用户表 (dbo.Users)
    统一存放所有用户（管理员、教师、学生）的基本信息
    """
    __tablename__ = 'Users'

    # 字段定义 
    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # 对应 SQL 中的 password 字段，用于存储哈希值
    password_hash = db.Column('password', db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    # role 字段有 CHECK 约束: 'admin', 'teacher', 'student' 
    role = db.Column(db.String(20), nullable=False)
    # status 字段有 CHECK 约束: 0, 1 
    status = db.Column(db.SmallInteger, default=1)
    
    # 自动填充时间戳 
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # --- 密码加密和验证方法 (来自您的示例) ---
    @property
    def password(self):
        """防止直接读取 password_hash"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """设置密码时，自动进行哈希加密"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码时，检查哈希值是否匹配"""
        return check_password_hash(self.password_hash, password)

    def check_password(self, password):
        """与 verify_password 等价，供视图调用"""
        return self.verify_password(password)

    def set_password(self, raw_password):
        """同时兼容明文或已哈希密码的设置"""
        if raw_password is None:
            return
        if self.is_hashed_password(raw_password):
            self.password_hash = raw_password
        else:
            self.password_hash = generate_password_hash(raw_password)

    @staticmethod
    def is_hashed_password(value):
        """简单判断给定字符串是否看起来已经是哈希"""
        if not value or not isinstance(value, str):
            return False
        return value.startswith(('pbkdf2:', 'scrypt:', 'argon2:'))

    def get_id(self):
        # 兼容 UserMixin，返回 user_id 的字符串形式
        return str(self.user_id)

    # --- 关系定义：User -> Admin/Student/Teacher (一对一) ---
    # backref 允许在子表（如 Student）中通过 user 属性访问 User 对象
    admin_profile = db.relationship('Admin', backref='user', uselist=False)
    student_profile = db.relationship('Student', backref='user', uselist=False)
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)


class Admin(db.Model):
    """管理员表 (dbo.Admin)"""
    __tablename__ = 'Admin'

    # 字段定义 [cite: 3]
    admin_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    admin_no = db.Column(db.String(20), unique=True, nullable=False)
    # name 字段已删除，统一使用 Users.real_name
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
    # 权限级别：1-最高权限(可管理权限), 2-中级权限(可管理用户), 3-一般权限(仅查询), 默认为3
    permission_level = db.Column(db.SmallInteger, default=3)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系定义：Admin -> User (通过 user_id 关联) [cite: 3]
    # user 关系已通过 User 模型的 backref 定义
    
    def has_permission(self, level):
        """检查是否有指定级别的权限（数字越小权限越高）"""
        return self.permission_level <= level
    
    @property
    def name(self):
        """获取管理员姓名（从 Users 表）"""
        return self.user.real_name if self.user else None




class Student(db.Model):
    """学生表 (dbo.Student)"""
    __tablename__ = 'Student'

    # 字段定义 [cite: 4]
    student_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    # 对应 SQL 中的 CHAR(10) NOT NULL UNIQUE [cite: 4]
    student_no = db.Column(db.String(10), unique=True, nullable=False) 
    # name 字段已删除，统一使用 Users.real_name
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
    major = db.Column(db.String(100))
    # grade 和 class_name 已删除，这些是变动属性，应在 StudentClass 中管理
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系定义：Student -> User (通过 user_id 关联) [cite: 4]
    # user 关系已通过 User 模型的 backref 定义
    
    # 关系定义：Student -> StudentClass (一对多)
    enrollments = db.relationship('StudentClass', backref='student', lazy='dynamic')
    # 关系定义：Student -> Submission (一对多)
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')
    # 关系定义：Student -> Grade (一对多)
    grades = db.relationship('Grade', backref='student', lazy='dynamic')
    
    @property
    def name(self):
        """获取学生姓名（从 Users 表）"""
        return self.user.real_name if self.user else None


class Teacher(db.Model):
    """教师表 (dbo.Teacher)"""
    __tablename__ = 'Teacher'

    # 字段定义 [cite: 6]
    teacher_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    teacher_no = db.Column(db.String(20), unique=True, nullable=False)
    # name 字段已删除，统一使用 Users.real_name
    title = db.Column(db.String(50))
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系定义：Teacher -> User (通过 user_id 关联) [cite: 6]
    # user 关系已通过 User 模型的 backref 定义

    # 关系定义：Teacher -> TeacherClass (一对多)
    teaching_assignments = db.relationship('TeacherClass', backref='teacher', lazy='dynamic')
    # 关系定义：Teacher -> Material (一对多)
    materials = db.relationship('Material', backref='teacher', lazy='dynamic')
    # 关系定义：Teacher -> Assignment (一对多)
    assignments = db.relationship('Assignment', backref='teacher', lazy='dynamic')
    # 关系定义：Teacher -> Grade (一对多，作为计算者)
    calculated_grades = db.relationship('Grade', backref='calculator', lazy='dynamic', foreign_keys='Grade.calculated_by')
    # 关系定义：Teacher -> Submission (一对多，作为评分者)
    graded_submissions = db.relationship('Submission', backref='grader', lazy='dynamic', foreign_keys='Submission.graded_by')

    # models.py (在 class Teacher 中添加)
    # 关系定义：Teacher -> Grade (计算者)
    # 明确指出这个关系是针对 Grade 表中的 calculated_by 字段
    
    @property
    def name(self):
        """获取教师姓名（从 Users 表）"""
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
    # DECIMAL(3,1) 对应 Numeric(3, 1)
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
    """教学班表 (dbo.TeachingClass)"""
    __tablename__ = 'TeachingClass'

    # 字段定义 [cite: 10]
    class_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    course_id = db.Column(db.BigInteger, db.ForeignKey('Course.course_id'), nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    class_time = db.Column(db.String(200))
    classroom = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    # status 字段有 CHECK 约束: 0, 1 [cite: 10]
    status = db.Column(db.SmallInteger, default=1) 
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # 关系定义：TeachingClass -> StudentClass (一对多)
    enrollments = db.relationship('StudentClass', backref='teaching_class', lazy='dynamic')
    # 关系定义：TeachingClass -> TeacherClass (一对多)
    teachers = db.relationship('TeacherClass', backref='teaching_class', lazy='dynamic')
    # 关系定义：TeachingClass -> Material (一对多)
    materials = db.relationship('Material', backref='teaching_class', lazy='dynamic')
    # 关系定义：TeachingClass -> Assignment (一对多)
    assignments = db.relationship('Assignment', backref='teaching_class', lazy='dynamic')
    # 关系定义：TeachingClass -> Grade (一对多)
    grades = db.relationship('Grade', backref='teaching_class', lazy='dynamic')


class StudentClass(db.Model):
    """学生选课关系表 (dbo.StudentClass)"""
    __tablename__ = 'StudentClass'

    # 字段定义 [cite: 12]
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    enroll_time = db.Column(db.DateTime(timezone=True), default=func.now())
    # status 字段有 CHECK 约束: 0, 1 [cite: 12]
    status = db.Column(db.SmallInteger, default=1)

    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_StudentClass_Student_Class'),
    )


class TeacherClass(db.Model):
    """教师任课关系表 (dbo.TeacherClass)"""
    __tablename__ = 'TeacherClass'

    # 字段定义 [cite: 14]
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    # role 字段有 CHECK 约束: 'main', 'assistant' [cite: 14]
    role = db.Column(db.String(20), default='main')
    assign_time = db.Column(db.DateTime(timezone=True), default=func.now())

    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'class_id', name='UK_TeacherClass_Teacher_Class'),
    )

# -----------------------------------------------------------
# 3. 教学资源模块
# -----------------------------------------------------------

class Material(db.Model):
    """教学资料表 (dbo.Material)"""
    __tablename__ = 'Material'

    # 字段定义 [cite: 17]
    material_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    file_type = db.Column(db.String(50))
    download_count = db.Column(db.Integer, default=0)
    publish_time = db.Column(db.DateTime(timezone=True), default=func.now())


# -----------------------------------------------------------
# 4. 作业考试模块
# -----------------------------------------------------------

class Assignment(db.Model):
    """作业/考试表 (dbo.Assignment)"""
    __tablename__ = 'Assignment'

    # 字段定义 [cite: 19, 20]
    assignment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'), nullable=False)
    # type 字段有 CHECK 约束: 'homework', 'exam' [cite: 19]
    type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # DECIMAL(5,2) 对应 Numeric(5, 2)
    total_score = db.Column(db.Numeric(5, 2), nullable=False, default=100.00)
    deadline = db.Column(db.DateTime(timezone=True), nullable=False)
    
    # 考试特有字段
    start_time = db.Column(db.DateTime(timezone=True))
    duration = db.Column(db.Integer)
    
    publish_time = db.Column(db.DateTime(timezone=True), default=func.now())
    # status 字段有 CHECK 约束: 0, 1 [cite: 19, 20]
    status = db.Column(db.SmallInteger, default=1)

    # 关系定义：Assignment -> Submission (一对多)
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic')


class Submission(db.Model):
    """提交记录表 (dbo.Submission)"""
    __tablename__ = 'Submission'

    # 字段定义 [cite: 21, 22, 23]
    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    assignment_id = db.Column(db.BigInteger, db.ForeignKey('Assignment.assignment_id'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    content = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    submit_time = db.Column(db.DateTime(timezone=True), default=func.now())
    
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    # 评分人是 Teacher [cite: 22]
    graded_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    graded_time = db.Column(db.DateTime(timezone=True))
    # status 字段有 CHECK 约束: 'submitted', 'graded' [cite: 22]
    status = db.Column(db.String(20), default='submitted')

    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='UK_Submission_Assignment_Student'),
    )

# -----------------------------------------------------------
# 5. 成绩管理模块
# -----------------------------------------------------------

class Grade(db.Model):
    """成绩表 (dbo.Grade)"""
    __tablename__ = 'Grade'

    # 字段定义 [cite: 25]
    grade_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    
    homework_avg = db.Column(db.Numeric(5, 2))
    exam_avg = db.Column(db.Numeric(5, 2))
    teacher_evaluation = db.Column(db.Numeric(5, 2))
    final_grade = db.Column(db.Numeric(5, 2))
    
    # 成绩计算人是 Teacher [cite: 25]
    calculated_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    calculated_at = db.Column(db.DateTime(timezone=True))
    remarks = db.Column(db.Text)

    # 联合唯一约束 [cite: 25]
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_Grade_Student_Class'),
    )
