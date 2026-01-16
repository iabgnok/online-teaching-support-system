from flask import Blueprint, jsonify, request
from flask_login import current_user
from functools import wraps
from models import Attendance, AttendanceRecord, StudentClass, TeacherClass, db, generate_next_id, Student, Users
from datetime import datetime, date

attendance_bp = Blueprint('attendance', __name__)


def api_login_required(f):
    """检查用户是否登录，如果未登录则返回 401"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@attendance_bp.route('/class/<int:class_id>', methods=['GET'])
@api_login_required
def get_class_attendance_list(class_id):
    """Get all attendance sessions for a class (Teacher or Student of that class)"""
    # Simply listing dates
    # Check permissions (omitted for brevity)
    
    attendances = Attendance.query.filter_by(class_id=class_id).order_by(Attendance.date.desc()).all()
    
    data = []
    for att in attendances:
        present_count = att.records.filter_by(status='present').count()
        absent_count = att.records.filter_by(status='absent').count()
        late_count = att.records.filter_by(status='late').count()
        leave_count = att.records.filter_by(status='leave').count()
        total_count = att.records.count()
        
        data.append({
            'attendance_id': att.id,
            'date': att.date.isoformat(),
            'created_at': att.created_at.isoformat(),
            'stats': {
                'total': total_count,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'leave': leave_count
            }
        })
        
    return jsonify(data)

@attendance_bp.route('/class/<int:class_id>', methods=['POST'])
@api_login_required
def create_attendance(class_id):
    """Create a new attendance session and init records for all students"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 验证教师权限
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    has_access = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=class_id).first()
    if not has_access:
        return jsonify({'error': 'You do not teach this class'}), 403
    
    data = request.get_json() or {}
    
    # 获取参数
    attendance_date = data.get('date')
    is_self_checkin = data.get('is_self_checkin', False)
    # 如果开启自助签到，默认状态应该是absent（未签到），否则是present
    default_status = data.get('default_status', 'absent' if is_self_checkin else 'present')
    
    # 解析日期
    if attendance_date:
        try:
            if isinstance(attendance_date, str):
                attendance_date = datetime.fromisoformat(attendance_date.replace('Z', '+00:00')).date()
            else:
                attendance_date = datetime.now().date()
        except:
            attendance_date = datetime.now().date()
    else:
        attendance_date = datetime.now().date()
        
    try:
        # Create Attendance
        att_id = generate_next_id(Attendance)
        new_att = Attendance(
            id=att_id,
            class_id=class_id,
            date=attendance_date,
            is_self_checkin=is_self_checkin
        )
        db.session.add(new_att)
        
        # Init records for all students with default status
        students = StudentClass.query.filter_by(class_id=class_id, status=1).all()
        
        if not students:
            db.session.rollback()
            return jsonify({'error': 'No students enrolled in this class'}), 400
        
        current_max_id = db.session.query(db.func.max(AttendanceRecord.id)).scalar() or 0

        record_objects = []
        for i, s in enumerate(students):
            rec = AttendanceRecord(
                id=current_max_id + i + 1,
                attendance_id=att_id,
                student_id=s.student_id,
                status=default_status
            )
            record_objects.append(rec)
            
        db.session.add_all(record_objects)
        db.session.commit()
        
        return jsonify({'message': 'Attendance created', 'id': att_id, 'date': new_att.date.isoformat()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@attendance_bp.route('/<int:attendance_id>', methods=['GET'])
@api_login_required
def get_attendance_detail(attendance_id):
    """Get student list and status for an attendance session"""
    att = Attendance.query.get_or_404(attendance_id)
    # Permission check
    
    records = AttendanceRecord.query.filter_by(attendance_id=attendance_id).all()
    data = []
    for r in records:
        student = r.student
        user = student.user
        data.append({
            'record_id': r.id,
            'student_id': student.student_id,
            'student_no': student.student_no,
            'name': user.real_name,
            'status': r.status,
            'remarks': r.remarks
        })
        
    # Sort by student no
    data.sort(key=lambda x: x['student_no'])
    
    return jsonify({
        'attendance_id': att.id,
        'date': att.date.isoformat(),
        'class_id': att.class_id,
        'records': data
    })

@attendance_bp.route('/<int:attendance_id>/records', methods=['PUT'])
@api_login_required
def update_attendance_records(attendance_id):
    """Batch update records"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json() 
    # Expecting: { records: [ { record_id: 1, status: 'absent' }, ... ] } or just update one logic
    
    updates = data.get('records', [])
    for item in updates:
        rec = AttendanceRecord.query.get(item['record_id'])
        if rec and rec.attendance_id == attendance_id:
            rec.status = item.get('status', rec.status)
            rec.remarks = item.get('remarks', rec.remarks)
            
    db.session.commit()
    return jsonify({'message': 'Updated'})

@attendance_bp.route('/class/<int:class_id>/me', methods=['GET'])
@api_login_required
def get_student_my_attendance(class_id):
    """Get current student's attendance records for a class"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    student = Student.query.filter_by(user_id=current_user.user_id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
        
    # Get all attendance sessions for this class
    attendances = Attendance.query.filter_by(class_id=class_id).order_by(Attendance.date.desc()).all()
    if not attendances:
        return jsonify([])
        
    attendance_ids = [a.id for a in attendances]
    
    # Get records
    records = AttendanceRecord.query.filter(
        AttendanceRecord.attendance_id.in_(attendance_ids),
        AttendanceRecord.student_id == student.student_id
    ).all()
    
    # Map back to attendance object
    att_map = {a.id: a for a in attendances}
    now_date = datetime.now().date()
    
    data = []
    for r in records:
        att = att_map.get(r.attendance_id)
        if not att: continue
        
        # Determine if check-in is allowed
        can_checkin = False
        if att.is_self_checkin and r.status == 'absent':
            # Check date (simplified: must be today)
            if att.date == now_date:
                can_checkin = True
        
        data.append({
            'attendance_id': att.id,
            'date': att.date.isoformat(),
            'status': r.status,
            'remarks': r.remarks,
            'can_checkin': can_checkin
        })

    # Sort by date desc
    data.sort(key=lambda x: x['date'], reverse=True)
    
    return jsonify(data)


@attendance_bp.route('/<int:attendance_id>/checkin', methods=['POST'])
@api_login_required
def student_checkin(attendance_id):
    """Student self check-in"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
        
    att = Attendance.query.get_or_404(attendance_id)
    
    if not att.is_self_checkin:
        return jsonify({'error': 'Self check-in is not enabled for this session'}), 400
        
    # Check time window (simplified: match date)
    if att.date != datetime.now().date():
         return jsonify({'error': 'Attendance is not for today'}), 400
         
    # Find record
    record = AttendanceRecord.query.filter_by(attendance_id=attendance_id, student_id=student.student_id).first()
    if not record:
         return jsonify({'error': 'You are not on the list'}), 404
         
    if record.status == 'present':
         return jsonify({'message': 'Already checked in'})
         
    record.status = 'present'
    db.session.commit()
    
    return jsonify({'message': 'Check-in successful'})


@attendance_bp.route('/<int:attendance_id>', methods=['DELETE'])
@api_login_required
def delete_attendance(attendance_id):
    """Delete an attendance session and all its records"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    att = Attendance.query.get_or_404(attendance_id)
    
    # 验证教师权限
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    has_access = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=att.class_id).first()
    if not has_access:
        return jsonify({'error': 'You do not teach this class'}), 403
    
    try:
        # 删除所有相关的考勤记录
        AttendanceRecord.query.filter_by(attendance_id=attendance_id).delete()
        # 删除考勤会话
        db.session.delete(att)
        db.session.commit()
        
        return jsonify({'message': 'Attendance deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

