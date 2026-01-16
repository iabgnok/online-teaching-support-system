from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Assignment, Submission, TeacherClass, StudentClass, Student, generate_next_id
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__, url_prefix='/assignments')

@assignments_bp.route('/', methods=['POST'])
@login_required
def create_assignment():
    """发布新作业"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    
    # Validation
    class_id = data.get('class_id')
    title = data.get('title')
    deadline_str = data.get('deadline')
    
    if not all([class_id, title, deadline_str]):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Check permissions
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
        
    has_access = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not has_access:
        return jsonify({'error': 'You do not teach this class'}), 403
        
    try:
        # Handle ISO format from JS (e.g. 2023-12-01T12:00:00.000Z or 2023-12-01 12:00:00)
        # Replacing Z with +00:00 for fromisoformat comp. if needed, but simplified:
        if 'T' in deadline_str:
             deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        else:
             deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error parsing date: {str(e)}'}), 400

    try:
        new_assignment = Assignment(
            assignment_id=generate_next_id(Assignment, 'assignment_id'),
            class_id=class_id,
            teacher_id=teacher.teacher_id,
            title=title,
            description=data.get('description', ''),
            type=data.get('type', 'homework'),
            total_score=data.get('total_score', 100),
            deadline=deadline,
            status=1 # Open
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return jsonify({'message': 'Assignment created successfully', 'id': new_assignment.assignment_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@assignments_bp.route('/<int:assignment_id>', methods=['GET'])
@login_required
def get_assignment_detail(assignment_id):
    """获取作业详情"""
    assignment = Assignment.query.get_or_404(assignment_id)
    # Check permission (Teacher of class or Student of class)
    # Simplified for now
    
    return jsonify({
        'id': assignment.assignment_id,
        'title': assignment.title,
        'description': assignment.description,
        'deadline': assignment.deadline.isoformat(),
        'total_score': float(assignment.total_score),
        'class_id': assignment.class_id,
        'class_name': assignment.teaching_class.class_name,
        'course_name': assignment.teaching_class.course.course_name
    })

@assignments_bp.route('/<int:assignment_id>/submissions', methods=['GET'])
@login_required
def get_submissions(assignment_id):
    """获取某作业的所有提交（教师端）"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    assignment = Assignment.query.get_or_404(assignment_id)
    # Check teacher permission...
    
    # Get all students in class
    enrollments = StudentClass.query.filter_by(class_id=assignment.class_id, status=1).all()
    
    submissions_map = {s.student_id: s for s in Submission.query.filter_by(assignment_id=assignment_id).all()}
    
    data = []
    for enr in enrollments:
        student = enr.student
        sub = submissions_map.get(student.student_id)
        
        item = {
            'student_id': student.student_id,
            'student_no': student.student_no,
            'name': student.user.real_name,
            'status': 'unsubmitted'
        }
        
        if sub:
            item.update({
                'submission_id': sub.submission_id,
                'status': sub.status,
                'submit_time': sub.submit_time.isoformat() if sub.submit_time else None,
                'score': float(sub.score) if sub.score is not None else None,
                'file_name': sub.file_name,
                # Use existing Flask route for download
                'file_url': f"/submission/{sub.submission_id}/download" if sub.file_name else None,
                'feedback': sub.feedback
            })
            
        data.append(item)
        
    # Sort: Submitted first, then by student_no
    data.sort(key=lambda x: (x['status'] == 'unsubmitted', x['student_no']))
    
    return jsonify(data)

@assignments_bp.route('/<int:assignment_id>/submissions/<int:student_id>', methods=['POST'])
@login_required
def grade_submission(assignment_id, student_id):
    """批改作业 (创建或更新 Submission)"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    score = data.get('score')
    feedback = data.get('feedback')
    
    if score is None:
        return jsonify({'error': 'Score is required'}), 400
        
    sub = Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id).first()
    
    if not sub:
        # If grading a student who hasn't submitted, create a record (e.g. 0 score)
        # Note: Usually we grade existing submissions, but teacher might want to give 0 for missing work
        import time
        sub = Submission(
            submission_id=int(time.time() * 1000), # Simple ID generation
            assignment_id=assignment_id,
            student_id=student_id,
            submit_time=None, 
            status='graded'
        )
        db.session.add(sub)
    
    sub.score = score
    sub.feedback = feedback
    sub.status = 'graded'
    sub.graded_by = current_user.teacher_profile.teacher_id
    sub.graded_time = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': 'Graded successfully'})


@assignments_bp.route('/<int:assignment_id>/grades', methods=['GET'])
@login_required
def get_assignment_grades(assignment_id):
    """获取某作业的所有学生成绩（教师端）"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # 获取班级所有学生
    enrollments = StudentClass.query.filter_by(class_id=assignment.class_id, status=1).all()
    
    result = []
    for enrollment in enrollments:
        student = enrollment.student
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student.student_id
        ).first()
        
        result.append({
            'student_id': student.student_id,
            'student_no': student.student_no,
            'student_name': student.user.real_name,
            'score': float(submission.score) if submission and submission.score is not None else None,
            'submitted_at': submission.submit_time.isoformat() if submission and submission.submit_time else None,
            'graded_at': submission.graded_time.isoformat() if submission and submission.graded_time else None,
            'feedback': submission.feedback if submission else None,
            'status': submission.status if submission else 'unsubmitted'
        })
    
    return jsonify(result)
