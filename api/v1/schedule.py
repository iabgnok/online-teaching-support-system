from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from models import db, Assignment, TeachingClass, StudentClass, TeacherClass
from datetime import timedelta

from . import api_v1

@api_v1.route('/schedule/events', methods=['GET'])
@login_required
def get_events():
    """获取日历事件（作业、考试）"""
    # FullCalendar 传递 start 和 end 参数 (ISO8601 字符串)
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = []
    
    # 1. 获取用户关联的班级ID列表
    class_ids = []
    if current_user.role == 'student':
        student = current_user.student_profile
        if student:
            enrollments = StudentClass.query.filter_by(student_id=student.student_id, status=1).all()
            class_ids = [e.class_id for e in enrollments]
    elif current_user.role == 'teacher':
        teacher = current_user.teacher_profile
        if teacher:
            teachings = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
            class_ids = [t.class_id for t in teachings]
    elif current_user.role == 'admin':
        # 管理员暂无日历视图需求，或者可以查看全校大事件
        return jsonify([])

    if not class_ids:
        return jsonify(events)

    # 2. 查询这些班级的作业和考试
    query = Assignment.query.filter(Assignment.class_id.in_(class_ids))
    
    # 如果传来起止时间，可以加过滤优化查询
    # if start_date:
    #     query = query.filter(Assignment.deadline >= start_date)
    # if end_date:
    #     query = query.filter(Assignment.deadline <= end_date)

    assignments = query.all()

    for assign in assignments:
        # 事件的基本属性
        class_name = assign.teaching_class.class_name if assign.teaching_class else "Unknown Class"
        
        # 1. 作业/考试 截止时间
        if assign.deadline:
            events.append({
                'id': f'deadline_{assign.assignment_id}',
                'title': f'[截止] {assign.title} ({class_name})',
                'start': assign.deadline.isoformat(),
                'allDay': False, # 截止时间通常是具体时刻
                'color': '#d9534f', # Bootstrap Danger Red
                'extendedProps': {
                    'type': 'deadline',
                    'assignment_id': assign.assignment_id,
                    'description': assign.description
                }
            })
        
        # 2. 考试 开始时间
        if assign.type == 'exam' and assign.start_time:
            start_time = assign.start_time
            end_time = start_time
            if assign.duration:
                 end_time = start_time + timedelta(minutes=assign.duration)

            events.append({
                'id': f'exam_{assign.assignment_id}',
                'title': f'[考试] {assign.title} ({class_name})',
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'color': '#f0ad4e', # Bootstrap Warning Orange
                'extendedProps': {
                    'type': 'exam',
                    'assignment_id': assign.assignment_id
                }
            })

    return jsonify(events)
