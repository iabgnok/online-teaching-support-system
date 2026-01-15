from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Attendance, AttendanceRecord, StudentClass, TeacherClass, db, generate_next_id, Student, Users
from datetime import datetime, date

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/class/<int:class_id>', methods=['GET'])
@login_required
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
@login_required
def create_attendance(class_id):
    """Create a new attendance session and init records for all students"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Check if for today already exists? (Optional)
    
    # Create Attendance
    att_id = generate_next_id(Attendance)
    new_att = Attendance(
        id=att_id,
        class_id=class_id,
        date=datetime.now().date(),
        is_self_checkin=False
    )
    db.session.add(new_att)
    
    # Init records for all students with default 'present' or 'absent'? Let's say 'present' default, teacher marks absent
    students = StudentClass.query.filter_by(class_id=class_id, status=1).all()
    
    record_objects = []
    for s in students:
        rec = AttendanceRecord(
            id=generate_next_id(AttendanceRecord), # This might be slow one by one, but consistent
            attendance_id=att_id,
            student_id=s.student_id,
            status='present' # Default
        )
        record_objects.append(rec)
        
    db.session.add_all(record_objects)
    db.session.commit()
    
    return jsonify({'message': 'Attendance created', 'id': att_id, 'date': new_att.date.isoformat()}), 201

@attendance_bp.route('/<int:attendance_id>', methods=['GET'])
@login_required
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
@login_required
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
@login_required
def get_student_my_attendance(class_id):
    """Get current student's attendance records for a class"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    student = Student.query.filter_by(user_id=current_user.id).first()
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
    
    # Map back to date
    att_map = {a.id: a.date for a in attendances}
    
    data = []
    for r in records:
        data.append({
            'date': att_map[r.attendance_id].isoformat(),
            'status': r.status,
            'remarks': r.remarks
        })

    # Sort by date desc
    data.sort(key=lambda x: x['date'], reverse=True)
    
    return jsonify(data)

