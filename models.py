from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_login import UserMixin   # type: ignore
from sqlalchemy.sql import func  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash   # type: ignore

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
    """成绩表：存储最终归档的成绩"""
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
