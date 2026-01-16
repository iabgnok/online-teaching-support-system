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
