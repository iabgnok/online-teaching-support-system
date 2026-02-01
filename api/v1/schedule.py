from flask import Blueprint, jsonify, request, g
from .auth import api_login_required
from models import db, Assignment, TeachingClass, StudentClass, TeacherClass, Submission, TeachingPlan, PersonalTask
from datetime import timedelta, datetime, timezone

from . import api_v1

def make_aware(dt):
    """将naive datetime转换为aware datetime（UTC）"""
    if dt is None:
        return None
    if isinstance(dt, str):
        # 尝试解析字符串
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def get_event_color(planned_date):
    """根据剩余时间计算事件的颜色（颜色渐变逻辑）"""
    try:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        event_date = make_aware(planned_date)
        delta = event_date - now
        
        if delta.days >= 14:  # 剩余时间 > 2周
            return '#5cb85c'  # 绿色
        elif 7 <= delta.days < 14:  # 剩余时间 1周 - 2周
            return '#f0ad4e'  # 黄色
        elif 1 <= delta.days < 7:  # 剩余时间 < 1周
            return '#d58a2d'  # 橙色
        elif delta.days == 0:  # 剩余时间 = 1天
            return '#d9534f'  # 红色
        else:  # 已过期
            return '#6c757d'  # 灰色
    except:
        return '#909399'  # 默认灰色

@api_v1.route('/schedule/events', methods=['GET'])
@api_login_required
def get_events():
    """获取日历事件（作业、考试、教学计划、个人任务）"""
    # FullCalendar 传递 start 和 end 参数 (ISO8601 字符串)
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = []
    
    # 1. 获取用户关联的班级ID列表
    student_id = None
    class_ids = []
    if g.user.role == 'student':
        student = g.user.student_profile
        if student:
            student_id = student.student_id
            enrollments = StudentClass.query.filter_by(student_id=student.student_id, status=1).all()
            class_ids = [e.class_id for e in enrollments]
    elif g.user.role == 'teacher':
        teacher = g.user.teacher_profile
        if teacher:
            teachings = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
            class_ids = [t.class_id for t in teachings]
    elif g.user.role == 'admin':
        # 管理员暂无日历视图需求，或者可以查看全校大事件
        return jsonify([])

    if not class_ids:
        return jsonify(events)

    # 2. 查询这些班级的作业和考试
    query = Assignment.query.filter(Assignment.class_id.in_(class_ids))
    assignments = query.all()
    
    # 获取提交状态（如果是学生）
    submitted_assignment_ids = set()
    submission_status_map = {}  # assignment_id -> status
    if student_id:
        submissions = Submission.query.filter(
            Submission.student_id == student_id,
            Submission.assignment_id.in_([a.assignment_id for a in assignments])
        ).all()
        submitted_assignment_ids = {s.assignment_id for s in submissions}
        submission_status_map = {s.assignment_id: s.status for s in submissions}

    for assign in assignments:
        # 事件的基本属性
        class_name = assign.teaching_class.class_name if assign.teaching_class else "Unknown Class"
        is_submitted = assign.assignment_id in submitted_assignment_ids
        submission_status = submission_status_map.get(assign.assignment_id, 'unsubmitted')
        
        # 逻辑调整：如果是考试且有考试时间，只显示考试事件；如果是作业，显示截止时间
        
        if assign.type == 'exam' and assign.start_time:
            start_time = assign.start_time
            end_time = start_time
            if assign.duration:
                 end_time = start_time + timedelta(minutes=assign.duration)

            events.append({
                'id': f'exam_{assign.assignment_id}',
                'title': f'{assign.title} ({class_name})',
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'color': '#f0ad4e', # Bootstrap Warning Orange
                'extendedProps': {
                    'type': 'exam',
                    'assignment_id': assign.assignment_id,
                    'submitted': is_submitted,
                    'submission_status': submission_status
                }
            })
        elif assign.deadline:
            # 作业 或 没有开始时间的考试（ fallback）
            events.append({
                'id': f'deadline_{assign.assignment_id}',
                'title': f'{assign.title} ({class_name})',
                'start': assign.deadline.isoformat(),
                'allDay': False, # 截止时间通常是具体时刻
                'color': get_event_color(assign.deadline),
                'extendedProps': {
                    'type': 'deadline',
                    'assignment_id': assign.assignment_id,
                    'class_name': class_name,
                    'description': assign.description,
                    'submitted': is_submitted,
                    'submission_status': submission_status,
                    'duration_minutes': assign.duration if assign.type == 'exam' else 0
                }
            })

    # 3. 如果是学生端，添加已同步的教学计划
    if g.user.role == 'student':
        # 获取已同步到学生端的教学计划
        teaching_plans = TeachingPlan.query.filter(
            TeachingPlan.class_id.in_(class_ids),
            TeachingPlan.sync_to_students == True
        ).all()
        
        for plan in teaching_plans:
            events.append({
                'id': f'teaching_plan_{plan.plan_id}',
                'title': f'📚 {plan.title}',
                'start': plan.planned_date.isoformat(),
                'allDay': False,
                'color': get_event_color(plan.planned_date),
                'extendedProps': {
                    'type': 'teaching_plan',
                    'class_name': plan.teaching_class.class_name,
                    'description': plan.description,
                    'duration_minutes': plan.duration_minutes
                }
            })
        
        # 4. 获取学生的个人任务
        personal_tasks = PersonalTask.query.filter_by(student_id=student_id).all()
        
        for task in personal_tasks:
            # 根据任务状态和优先级计算颜色
            if task.is_completed:
                color = '#5cb85c'
            else:
                color = get_event_color(task.planned_date)
            
            events.append({
                'id': f'personal_task_{task.task_id}',
                'title': f'📝 {task.title}',
                'start': task.planned_date.isoformat(),
                'allDay': False,
                'color': color,
                'extendedProps': {
                    'type': 'personal_task',
                    'description': task.description,
                    'duration_minutes': task.duration_minutes,
                    'priority': task.priority,
                    'is_completed': task.is_completed,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
            })

    return jsonify(events)

