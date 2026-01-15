from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from models import (
    db, TeachingClass, StudentClass, TeacherClass, 
    Material, Assignment, Submission, Grade, generate_next_id
)
from datetime import datetime
import os
from werkzeug.utils import secure_filename

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('/student/stats', methods=['GET'])
@login_required
def get_student_stats():
    """获取学生首页统计数据"""
    if current_user.role != 'student':
        return jsonify({})
    
    student = current_user.student_profile
    stats = {
        'total_courses': 0,
        'total_pending': 0,
        'average_grade': 0.0,
        'graded_count': 0
    }
    
    # 1. Total Courses
    enrollments = StudentClass.query.filter_by(student_id=student.student_id, status=1).all()
    stats['total_courses'] = len(enrollments)
    class_ids = [e.class_id for e in enrollments]
    
    if not class_ids:
        return jsonify(stats)
        
    # 2. Average Grade
    grades = Grade.query.filter(Grade.student_id == student.student_id, Grade.class_id.in_(class_ids)).all()
    total_score = 0
    graded_count = 0
    for g in grades:
        if g.final_grade is not None:
            total_score += float(g.final_grade)
            graded_count += 1
    
    stats['graded_count'] = graded_count
    if graded_count > 0:
        stats['average_grade'] = round(total_score / graded_count, 1)
        
    # 3. Pending Assignments (Simplified for performance)
    # Check assignments where deadine > now and no submission
    now = datetime.now()
    pending_count = 0
    
    assignments = Assignment.query.filter(Assignment.class_id.in_(class_ids), Assignment.status == 1).all()
    for a in assignments:
        # Check submission
        sub = Submission.query.filter_by(assignment_id=a.assignment_id, student_id=student.student_id).first()
        if not sub or sub.status not in ['submitted', 'graded']:
            # Also check if deadline not passed (optional, but "pending" usually means todo)
            # If deadline passed, it's overdue, still "pending" action?
            # Let's count tasks that are NOT submitted.
            pending_count += 1
            
    stats['total_pending'] = pending_count
    
    return jsonify(stats)


@classes_bp.route('/teacher/stats', methods=['GET'])
@login_required
def get_teacher_stats():
    """获取教师首页统计数据"""
    if current_user.role != 'teacher':
        return jsonify({})
    
    teacher = current_user.teacher_profile
    if not teacher:
         return jsonify({'active_courses': 0, 'total_students': 0, 'pending_grading': 0})

    # 1. Active Courses
    # Use relationship teaching_assignments from Teacher model
    # t_classes = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
    # Or use teacher.teaching_assignments which is a query object (lazy='dynamic')
    t_classes = teacher.teaching_assignments.all()
    active_courses = len(t_classes)
    
    # 2. Total Students (Distinct) - Count students in all my classes
    class_ids = [tc.teaching_class.class_id for tc in t_classes]
    total_students = 0
    if class_ids:
        total_students = StudentClass.query.filter(
            StudentClass.class_id.in_(class_ids), 
            StudentClass.status == 1
        ).distinct(StudentClass.student_id).count()
    
    # 3. Pending Grading
    pending_grading = 0
    if class_ids:
        pending_grading = Submission.query.join(Assignment).filter(
            Assignment.class_id.in_(class_ids),
            Submission.status == 'submitted'
        ).count()
        
    return jsonify({
        'active_courses': active_courses,
        'total_students': total_students,
        'pending_grading': pending_grading
    })


@classes_bp.route('/my', methods=['GET'])
@login_required
def get_my_classes():
    """获取我的班级列表"""
    classes_data = []
    
    if current_user.role == 'student':
        student = current_user.student_profile
        if student:
            enrollments = StudentClass.query.filter_by(student_id=student.student_id, status=1).all()
            for enroll in enrollments:
                tc = enroll.teaching_class
                course = tc.course
                teacher_main = TeacherClass.query.filter_by(class_id=tc.class_id, role='main').first()
                teacher_name = teacher_main.teacher.name if teacher_main else "未分配"
                
                # Fetch Grade
                grade_rec = Grade.query.filter_by(student_id=student.student_id, class_id=tc.class_id).first()
                final_grade = float(grade_rec.final_grade) if grade_rec and grade_rec.final_grade is not None else None
                
                # Count Pending for this class
                assignments = Assignment.query.filter_by(class_id=tc.class_id, status=1).all()
                pending_count = 0
                for a in assignments:
                     sub = Submission.query.filter_by(assignment_id=a.assignment_id, student_id=student.student_id).first()
                     if not sub or sub.status not in ['submitted', 'graded']:
                         pending_count += 1

                classes_data.append({
                    'class_id': tc.class_id,
                    'class_name': tc.class_name,
                    'course_name': course.course_name,
                    'course_code': course.course_code,
                    'teacher_name': teacher_name,
                    'semester': tc.semester,
                    'classroom': tc.classroom,
                    'time': tc.class_time,
                    'credit': float(course.credit) if course.credit else 0,
                    'final_grade': final_grade,
                    'pending_count': pending_count
                })

    elif current_user.role == 'teacher':
        teacher = current_user.teacher_profile
        if teacher:
            teachings = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
            for t in teachings:
                tc = t.teaching_class
                course = tc.course
                
                # Calculate pending grading (Assignment in this class -> Submissions where status='submitted')
                pending_grading = Submission.query.join(Assignment).filter(
                    Assignment.class_id == tc.class_id,
                    Submission.status == 'submitted'
                ).count()

                classes_data.append({
                    'class_id': tc.class_id,
                    'class_name': tc.class_name,
                    'course_name': course.course_name,
                    'course_code': course.course_code,
                    'role': t.role,
                    'student_count': tc.enrollments.count(),
                    'semester': tc.semester, 
                    'classroom': tc.classroom,
                    'time': tc.class_time,
                    'pending_grading': pending_grading
                })
                
    elif current_user.role == 'admin':
        # 管理员可以看到所有班级，或者返回空列表提示使用后台管理
        # 这里仅返回前20个作为示例，或实现搜索
        pass
        
    return jsonify(classes_data)

@classes_bp.route('/<int:class_id>/materials', methods=['GET'])
@login_required
def get_class_materials(class_id):
    """获取班级资料"""
    # 鉴权：检查用户是否在班级中（略，简化处理）
    materials = Material.query.filter_by(class_id=class_id).order_by(Material.publish_time.desc()).all()
    
    data = [{
        'id': m.material_id,
        'title': m.title,
        'description': m.description,
        'file_name': m.file_name,
        'file_size': m.file_size, # 可以格式化
        'publish_time': m.publish_time.isoformat(),
        'url': f'/material/{m.material_id}/download' 
    } for m in materials]
    
    return jsonify(data)

@classes_bp.route('/<int:class_id>/materials', methods=['POST'])
@login_required
def upload_material(class_id):
    """上传班级资料"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Check permissions
    teacher = current_user.teacher_profile
    has_access = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not has_access:
        return jsonify({'error': 'You do not teach this class'}), 403
        
    # File handling
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        original_filename = secure_filename(file.filename)
        # Using timestamp to avoid collision
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        
        file_path = os.path.join(current_app.config['MATERIALS_FOLDER'], filename)
        file.save(file_path)
        
        # Determine file type (simplified)
        ext = os.path.splitext(filename)[1].lower()
        file_type = ext.replace('.', '')
        
        # Create DB record
        new_material = Material(
            material_id=generate_next_id(Material, 'material_id'), # explicit ID field
            class_id=class_id,
            teacher_id=teacher.teacher_id,
            title=request.form.get('title', original_filename),
            description=request.form.get('description', ''),
            file_name=filename,
            file_path=filename, # Relative path or filename
            file_size=os.path.getsize(file_path),
            file_type=file_type
        )
        
        db.session.add(new_material)
        db.session.commit()
        
        return jsonify({'message': 'File uploaded successfully', 'id': new_material.material_id}), 201

@classes_bp.route('/<int:class_id>/students', methods=['GET'])
@login_required
def get_class_students(class_id):
    """获取班级学生名单"""
    # 鉴权：检查用户是否在班级中
    if current_user.role == 'teacher':
        # Check if teacher teaches this class
        has_access = TeacherClass.query.filter_by(teacher_id=current_user.teacher_profile.teacher_id, class_id=class_id).first()
        if not has_access and current_user.role != 'admin': # Admin usually has access
             return jsonify({'error': '无权访问该班级'}), 403
             
    enrollments = StudentClass.query.filter_by(class_id=class_id, status=1).all()
    data = []
    
    for enr in enrollments:
        student = enr.student
        user = student.user
        
        data.append({
            'student_id': student.student_id,
            'student_no': student.student_no,
            'name': user.real_name,
            'major': student.major,
            'dept_name': student.department.dept_name if student.department else '未知',
            'attendance_rate': 0  # To be implemented in Phase 2B
        })
        
    return jsonify(data)

@classes_bp.route('/<int:class_id>/assignments', methods=['GET'])
@login_required
def get_class_assignments(class_id):
    """获取班级作业"""
    assignments = Assignment.query.filter_by(class_id=class_id).order_by(Assignment.deadline.desc()).all()
    
    data = []
    now = datetime.now()
    
    for a in assignments:
        item = {
            'id': a.assignment_id,
            'title': a.title,
            'type': a.type, # homework, exam
            'deadline': a.deadline.isoformat(),
            'status': 'open' if a.status == 1 else 'closed',
            'score': float(a.total_score),
            'duration': a.duration,
            'is_overdue': False
        }
        
        # 如果是学生，查看提交状态
        if current_user.role == 'student':
            sub = Submission.query.filter_by(assignment_id=a.assignment_id, student_id=current_user.student_profile.student_id).first()
            if sub:
                item['submission_status'] = sub.status
                item['submission_time'] = sub.submit_time.isoformat()
                item['my_score'] = float(sub.score) if sub.score is not None else None
            else:
                item['submission_status'] = 'unsubmitted'
                # Check overdue
                if a.deadline < now:
                    item['is_overdue'] = True
        
        # 如果是教师，查看提交统计
        elif current_user.role == 'teacher':
             total_students = StudentClass.query.filter_by(class_id=class_id, status=1).count()
             # Submitted: status='submitted' | Graded: status='graded'
             submitted_count = Submission.query.filter_by(assignment_id=a.assignment_id, status='submitted').count()
             graded_count = Submission.query.filter_by(assignment_id=a.assignment_id, status='graded').count()
             
             item['stats'] = {
                 'total': total_students,
                 'submitted': submitted_count,
                 'graded': graded_count,
                 # unsubmitted is approximation
                 'pending': submitted_count # teacher needs to grade these
             }

        data.append(item)
        
    return jsonify(data)
