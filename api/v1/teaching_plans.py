from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from models import db, TeachingPlan, TeachingClass, TeacherClass, PersonalTask, Student, StudentClass
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_, func

from . import api_v1

def make_aware(dt):
    """将 naive datetime 转换为 aware datetime"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# ==================== 教学计划API ====================

@api_v1.route('/teaching-plans', methods=['GET'])
@login_required
def get_teaching_plans():
    """获取教学计划列表（教师端）"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can access teaching plans'}), 403
    
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    # 获取教师教授的班级
    class_ids = [tc.class_id for tc in TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()]
    
    if not class_ids:
        return jsonify([])
    
    # 获取过滤参数
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    class_id = request.args.get('class_id')
    
    query = TeachingPlan.query.filter(TeachingPlan.class_id.in_(class_ids))
    
    if class_id:
        try:
            query = query.filter_by(class_id=int(class_id))
        except (ValueError, TypeError):
            pass
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(TeachingPlan.planned_date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(TeachingPlan.planned_date <= end)
        except ValueError:
            pass
    
    plans = query.order_by(TeachingPlan.planned_date).all()
    
    result = []
    for plan in plans:
        result.append({
            'id': plan.plan_id,
            'title': plan.title,
            'class_id': plan.class_id,
            'class_name': plan.teaching_class.class_name,
            'description': plan.description,
            'planned_date': plan.planned_date.isoformat(),
            'duration_minutes': plan.duration_minutes,
            'sync_to_students': plan.sync_to_students,
            'color': get_event_color(plan.planned_date),
            'created_at': plan.created_at.isoformat(),
            'updated_at': plan.updated_at.isoformat()
        })
    
    return jsonify(result)


@api_v1.route('/teaching-plans', methods=['POST'])
@login_required
def create_teaching_plan():
    """创建教学计划"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can create teaching plans'}), 403
    
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['title', 'planned_date', 'class_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # 验证班级权限
    class_id = data['class_id']
    teaching = TeacherClass.query.filter_by(
        teacher_id=teacher.teacher_id,
        class_id=class_id
    ).first()
    
    if not teaching:
        return jsonify({'error': 'You do not have permission to this class'}), 403
    
    try:
        plan_id = db.session.query(db.func.max(TeachingPlan.plan_id)).scalar() or 0
        plan_id += 1
        
        planned_date = datetime.fromisoformat(data['planned_date'].replace('Z', '+00:00'))
        
        plan = TeachingPlan(
            plan_id=plan_id,
            teacher_id=teacher.teacher_id,
            class_id=class_id,
            title=data['title'],
            description=data.get('description', ''),
            planned_date=planned_date,
            duration_minutes=data.get('duration_minutes', 60),
            sync_to_students=data.get('sync_to_students', False)
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'id': plan.plan_id,
            'title': plan.title,
            'class_id': plan.class_id,
            'description': plan.description,
            'planned_date': plan.planned_date.isoformat(),
            'duration_minutes': plan.duration_minutes,
            'sync_to_students': plan.sync_to_students,
            'color': get_event_color(plan.planned_date),
            'created_at': plan.created_at.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_v1.route('/teaching-plans/<int:plan_id>', methods=['PUT'])
@login_required
def update_teaching_plan(plan_id):
    """更新教学计划"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can update teaching plans'}), 403
    
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    plan = TeachingPlan.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Teaching plan not found'}), 404
    
    if plan.teacher_id != teacher.teacher_id:
        return jsonify({'error': 'You do not have permission to update this plan'}), 403
    
    data = request.get_json()
    
    try:
        if 'title' in data:
            plan.title = data['title']
        if 'description' in data:
            plan.description = data['description']
        if 'planned_date' in data:
            plan.planned_date = datetime.fromisoformat(data['planned_date'].replace('Z', '+00:00'))
        if 'duration_minutes' in data:
            plan.duration_minutes = data['duration_minutes']
        if 'sync_to_students' in data:
            plan.sync_to_students = data['sync_to_students']
        
        db.session.commit()
        
        return jsonify({
            'id': plan.plan_id,
            'title': plan.title,
            'class_id': plan.class_id,
            'description': plan.description,
            'planned_date': plan.planned_date.isoformat(),
            'duration_minutes': plan.duration_minutes,
            'sync_to_students': plan.sync_to_students,
            'color': get_event_color(plan.planned_date),
            'updated_at': plan.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_v1.route('/teaching-plans/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_teaching_plan(plan_id):
    """删除教学计划"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can delete teaching plans'}), 403
    
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    plan = TeachingPlan.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Teaching plan not found'}), 404
    
    if plan.teacher_id != teacher.teacher_id:
        return jsonify({'error': 'You do not have permission to delete this plan'}), 403
    
    try:
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'message': 'Teaching plan deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_v1.route('/teaching-plans/sync-to-students/<int:plan_id>', methods=['POST'])
@login_required
def sync_plan_to_students(plan_id):
    """一键同步教学计划到学生端"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can sync plans'}), 403
    
    teacher = current_user.teacher_profile
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    plan = TeachingPlan.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Teaching plan not found'}), 404
    
    if plan.teacher_id != teacher.teacher_id:
        return jsonify({'error': 'You do not have permission to sync this plan'}), 403
    
    try:
        plan.sync_to_students = True
        db.session.commit()
        return jsonify({'message': 'Teaching plan synced to students successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 个人任务API ====================

@api_v1.route('/personal-tasks', methods=['GET'])
@login_required
def get_personal_tasks():
    """获取学生的个人任务列表"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can access personal tasks'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # 获取过滤参数
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    completed = request.args.get('completed')  # 'true', 'false', or None for all
    
    query = PersonalTask.query.filter_by(student_id=student.student_id)
    
    if completed is not None:
        is_completed = completed.lower() == 'true'
        query = query.filter_by(is_completed=is_completed)
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(PersonalTask.planned_date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(PersonalTask.planned_date <= end)
        except ValueError:
            pass
    
    tasks = query.order_by(PersonalTask.planned_date).all()
    
    result = []
    for task in tasks:
        result.append({
            'id': task.task_id,
            'title': task.title,
            'description': task.description,
            'planned_date': task.planned_date.isoformat(),
            'duration_minutes': task.duration_minutes,
            'is_completed': task.is_completed,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'priority': task.priority,
            'color': get_personal_task_color(task),
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        })
    
    return jsonify(result)


@api_v1.route('/personal-tasks', methods=['POST'])
@login_required
def create_personal_task():
    """创建个人任务"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can create personal tasks'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['title', 'planned_date']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        task_id = db.session.query(db.func.max(PersonalTask.task_id)).scalar() or 0
        task_id += 1
        
        planned_date = datetime.fromisoformat(data['planned_date'].replace('Z', '+00:00'))
        
        task = PersonalTask(
            task_id=task_id,
            student_id=student.student_id,
            title=data['title'],
            description=data.get('description', ''),
            planned_date=planned_date,
            duration_minutes=data.get('duration_minutes', 60),
            priority=data.get('priority', 'normal')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'id': task.task_id,
            'title': task.title,
            'description': task.description,
            'planned_date': task.planned_date.isoformat(),
            'duration_minutes': task.duration_minutes,
            'is_completed': task.is_completed,
            'priority': task.priority,
            'color': get_personal_task_color(task),
            'created_at': task.created_at.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_v1.route('/personal-tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_personal_task(task_id):
    """更新个人任务"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can update personal tasks'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    task = PersonalTask.query.get(task_id)
    if not task:
        return jsonify({'error': 'Personal task not found'}), 404
    
    if task.student_id != student.student_id:
        return jsonify({'error': 'You do not have permission to update this task'}), 403
    
    data = request.get_json()
    
    try:
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'planned_date' in data:
            task.planned_date = datetime.fromisoformat(data['planned_date'].replace('Z', '+00:00'))
        if 'duration_minutes' in data:
            task.duration_minutes = data['duration_minutes']
        if 'priority' in data:
            task.priority = data['priority']
        if 'is_completed' in data:
            task.is_completed = data['is_completed']
            if data['is_completed'] and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif not data['is_completed']:
                task.completed_at = None
        
        db.session.commit()
        
        return jsonify({
            'id': task.task_id,
            'title': task.title,
            'description': task.description,
            'planned_date': task.planned_date.isoformat(),
            'duration_minutes': task.duration_minutes,
            'is_completed': task.is_completed,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'priority': task.priority,
            'color': get_personal_task_color(task),
            'updated_at': task.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_v1.route('/personal-tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_personal_task(task_id):
    """删除个人任务"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can delete personal tasks'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    task = PersonalTask.query.get(task_id)
    if not task:
        return jsonify({'error': 'Personal task not found'}), 404
    
    if task.student_id != student.student_id:
        return jsonify({'error': 'You do not have permission to delete this task'}), 403
    
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Personal task deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 辅助函数 ====================

def get_event_color(planned_date):
    """根据剩余时间计算教学计划的颜色（颜色渐变逻辑）"""
    try:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        plan_date = make_aware(planned_date)
        delta = plan_date - now
        
        if delta.days >= 14:  # 剩余时间 > 2周
            return '#5cb85c'  # 绿色
        elif 7 <= delta.days < 14:  # 剩余时间 1周 - 2周
            return '#f0ad4e'  # 黄色
        elif 1 <= delta.days < 7:  # 剩余时间 < 1周
            return '#d58a2d'  # 橙色
        elif delta.days == 0:  # 剩余时间 = 1天（但这里用0天表示今天内）
            return '#d9534f'  # 红色
        else:  # 已过期
            return '#6c757d'  # 灰色
    except:
        return '#909399'  # 默认灰色


def get_personal_task_color(task):
    """根据任务状态和优先级获取颜色"""
    if task.is_completed:
        return '#5cb85c'  # 绿色：已完成
    
    # 如果未完成，根据优先级和剩余时间着色
    try:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        task_date = make_aware(task.planned_date)
        delta = task_date - now
        
        if task.priority == 'high':
            if delta.days < 1:
                return '#d9534f'  # 红色：紧急
            else:
                return '#d58a2d'  # 橙色：高优先级
        elif task.priority == 'normal':
            if delta.days >= 14:
                return '#5cb85c'  # 绿色
            elif 7 <= delta.days < 14:
                return '#f0ad4e'  # 黄色
            else:
                return '#d58a2d'  # 橙色
        else:  # low
            return '#5cb85c'  # 绿色
    except:
        return '#909399'  # 默认灰色
