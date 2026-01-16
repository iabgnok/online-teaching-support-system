from flask import jsonify, request, current_app
from flask_login import current_user
from functools import wraps
from models import db, VStudentMyAssignments, Submission, Assignment, generate_next_id
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import api_v1


def api_login_required(f):
    """检查用户是否登录，如果未登录则返回 401"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_v1.route('/student/assignment/<int:assignment_id>', methods=['GET'])
@api_login_required
def get_student_assignment_detail(assignment_id):
    """获取学生作业详情（包含提交状态）"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = current_user.student_profile
    
    # query view for efficiency and blended data
    record = VStudentMyAssignments.query.filter_by(
        student_id=student.student_id,
        assignment_id=assignment_id
    ).first()
    
    # Construct assignment object
    if record:
        assignment_data = {
            'id': record.assignment_id,
            'title': record.assignment_title,
            'content': record.description,
            'type': record.assignment_type,
            'total_score': float(record.total_score) if record.total_score else 0,
            'due_date': record.deadline.isoformat() if record.deadline else None,
            'course_name': record.course_name,
            'class_name': record.class_name,
            'status': record.status_display,
            'material_url': None
        }
        submission_id = record.submission_id
    else:
         # Fallback
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        assignment_data = {
            'id': assignment.assignment_id,
            'title': assignment.title,
            'content': assignment.description,
            'type': assignment.type,
            'total_score': float(assignment.total_score),
            'due_date': assignment.deadline.isoformat() if assignment.deadline else None,
            'course_name': assignment.teaching_class.course.course_name,
            'class_name': assignment.teaching_class.class_name,
            'status': 'unknown', # View missing implies something odd
            'material_url': None
        }
        # Check submission manually
        params = {'assignment_id': assignment_id, 'student_id': student.student_id}
        sub = Submission.query.filter_by(**params).first()
        submission_id = sub.submission_id if sub else None

    # Construct submission object
    submission_data = None
    if submission_id:
        sub = Submission.query.get(submission_id)
        if sub:
            submission_data = {
                'id': sub.submission_id,
                'content': sub.content,
                'file_name': sub.file_name,
                'file_url': f"/submission/{sub.submission_id}/download" if sub.file_name else None,
                'status': sub.status,
                'submitted_at': sub.submit_time.isoformat() if sub.submit_time else None,
                'grade': float(sub.score) if sub.score is not None else None,
                'feedback': sub.feedback
            }
            
    return jsonify({
        'assignment': assignment_data,
        'submission': submission_data
    })

@api_v1.route('/student/submit_assignment', methods=['POST'])
@api_login_required
def submit_assignment():
    """学生提交作业"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    student = current_user.student_profile
    assignment_id = request.form.get('assignment_id')
    content = request.form.get('content')
    file = request.files.get('file')

    if not assignment_id:
        return jsonify({'error': 'Assignment ID is required'}), 400

    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404

    # Check deadline
    if assignment.deadline and datetime.now() > assignment.deadline.replace(tzinfo=None): 
        # Ideally handle timezone accurately
        pass 

    sub = Submission.query.filter_by(assignment_id=assignment_id, student_id=student.student_id).first()
    
    file_name = None
    file_path_str = None
    
    if file:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        # safe filename
        new_filename = f"{student.student_no}_{assignment_id}_{timestamp}{ext}" # Use student_no for cleaner files
        
        save_dir = current_app.config.get('ASSIGNMENTS_FOLDER', 'uploads/assignments')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        file_path = os.path.join(save_dir, new_filename)
        file.save(file_path)
        
        file_name = filename
        file_path_str = file_path

    if sub:
        if content is not None:
             sub.content = content
        if file:
             sub.file_name = file_name
             sub.file_path = file_path_str
        sub.submit_time = datetime.now()
        sub.status = 'submitted'
    else:
        new_id = generate_next_id(Submission, 'submission_id')
        sub = Submission(
            submission_id=new_id,
            assignment_id=assignment_id,
            student_id=student.student_id,
            content=content,
            file_name=file_name,
            file_path=file_path_str,
            submit_time=datetime.now(),
            status='submitted'
        )
        db.session.add(sub)
    
    db.session.commit()
    
    return jsonify({'message': 'Assignment submitted successfully'})
