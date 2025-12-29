from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

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
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    status = db.Column(db.SmallInteger, default=1)  # 0=禁用, 1=激活
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
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)


class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'Admin'

    admin_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    admin_no = db.Column(db.String(20), unique=True, nullable=False)
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
    permission_level = db.Column(db.SmallInteger, default=3)  # 1=最高, 2=中级, 3=一般
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def has_permission(self, level):
        """检查是否有指定级别的权限（数字越小权限越高）"""
        return self.permission_level <= level
    
    @property
    def name(self):
        """获取管理员姓名"""
        return self.user.real_name if self.user else None




class Student(db.Model):
    """学生表"""
    __tablename__ = 'Student'

    student_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    student_no = db.Column(db.String(10), unique=True, nullable=False)
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
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
    user_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'), unique=True, nullable=False)
    teacher_no = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(50))
    dept_id = db.Column(db.BigInteger, db.ForeignKey('Department.dept_id'))
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
    """教学班表"""
    __tablename__ = 'TeachingClass'

    class_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    course_id = db.Column(db.BigInteger, db.ForeignKey('Course.course_id'), nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    class_time = db.Column(db.String(200))
    classroom = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    status = db.Column(db.SmallInteger, default=1)  # 0=禁用, 1=激活
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
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    enroll_time = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.SmallInteger, default=1)  # 0=退课, 1=正常

    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_StudentClass_Student_Class'),
    )


class TeacherClass(db.Model):
    """教师任课关系表"""
    __tablename__ = 'TeacherClass'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
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


# ==================== 作业考试模块 ====================

class Assignment(db.Model):
    """作业/考试表"""
    __tablename__ = 'Assignment'

    assignment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'homework'=作业, 'exam'=考试
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_score = db.Column(db.Numeric(5, 2), nullable=False, default=100.00)
    deadline = db.Column(db.DateTime(timezone=True), nullable=False)
    start_time = db.Column(db.DateTime(timezone=True))  # 考试特有
    duration = db.Column(db.Integer)  # 考试时长(分钟)
    publish_time = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.SmallInteger, default=1)  # 0=关闭, 1=开放

    # 关系：Assignment -> Submission (一对多)
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic')


class Submission(db.Model):
    """作业提交记录表"""
    __tablename__ = 'Submission'

    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    assignment_id = db.Column(db.BigInteger, db.ForeignKey('Assignment.assignment_id'), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    content = db.Column(db.Text)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    submit_time = db.Column(db.DateTime(timezone=True), default=func.now())
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    graded_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    graded_time = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='submitted')  # 'submitted'=已提交, 'graded'=已批改

    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='UK_Submission_Assignment_Student'),
    )

# ==================== 成绩管理模块 ====================

class Grade(db.Model):
    """成绩表"""
    __tablename__ = 'Grade'

    grade_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'), nullable=False)
    class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=False)
    homework_avg = db.Column(db.Numeric(5, 2))
    exam_avg = db.Column(db.Numeric(5, 2))
    teacher_evaluation = db.Column(db.Numeric(5, 2))
    final_grade = db.Column(db.Numeric(5, 2))
    calculated_by = db.Column(db.BigInteger, db.ForeignKey('Teacher.teacher_id'))
    calculated_at = db.Column(db.DateTime(timezone=True))
    remarks = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='UK_Grade_Student_Class'),
    )
