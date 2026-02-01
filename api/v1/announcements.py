from flask import jsonify, request, current_app, g
from models import Announcement, TeacherClass, StudentClass, db, generate_next_id, TeachingClass
from . import api_v1
from datetime import datetime
from .auth import api_login_required

@api_v1.route('/announcements', methods=['GET'])
@api_login_required
def get_announcements():
    """获取公告列表"""
    try:
        scope = request.args.get('scope') # global or class
    
        if scope == 'global':
            announcements = Announcement.query.filter_by(scope_type='global').order_by(Announcement.created_at.desc()).limit(20).all()
        elif scope == 'class':
            # Get announcements for classes the user is enrolled in (student) or teaching (teacher)
            class_ids = []
            
            if g.user.role == 'student' and g.user.student_profile:
                student = g.user.student_profile
                class_ids = [e.class_id for e in student.enrollments]
            elif g.user.role == 'teacher' and g.user.teacher_profile:
                teacher = g.user.teacher_profile
                from models import TeacherClass
                teachings = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
                class_ids = [t.class_id for t in teachings]
                
            if class_ids:
                announcements = Announcement.query.filter(
                    Announcement.scope_type == 'class',
                    Announcement.target_class_id.in_(class_ids)
                ).order_by(Announcement.created_at.desc()).limit(20).all()
            else:
                announcements = []
        else:
            # 默认返回全局 + 班级公告
            class_ids = []
            if g.user.role == 'student' and g.user.student_profile:
                student = g.user.student_profile
                class_ids = [e.class_id for e in student.enrollments]
            elif g.user.role == 'teacher' and g.user.teacher_profile:
                teacher = g.user.teacher_profile
                from models import TeacherClass
                teachings = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id).all()
                class_ids = [t.class_id for t in teachings]
            
            query = Announcement.query.filter(
                (Announcement.scope_type == 'global') |
                ((Announcement.scope_type == 'class') & (Announcement.target_class_id.in_(class_ids)))
            )
            announcements = query.order_by(Announcement.created_at.desc()).limit(20).all()

        results = []
        for a in announcements:
            results.append({
                'id': a.id,
                'title': a.title,
                'content': a.content,
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'author_name': a.author.real_name if a.author else 'Unknown',
                'target_class_name': a.target_class.class_name if a.target_class else None
            })
            
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"Failed to get announcements: {e}")
        return jsonify({'error': str(e)}), 500
@api_v1.route('/announcements/<int:id>', methods=['GET'])
@api_login_required
def get_announcement_detail(id):
    """获取公告详情"""
    try:
        announcement = db.session.get(Announcement, id)
        if not announcement:
            return jsonify({'error': 'Not found'}), 404
        
        # 检查权限
        if g.user.role == 'student':
            # 学生只能查看全局公告或自己班级的公告
            if announcement.scope_type == 'class':
                student = g.user.student_profile
                if not student or not StudentClass.query.filter_by(
                    student_id=student.student_id, 
                    class_id=announcement.target_class_id
                ).first():
                    return jsonify({'error': 'No permission to view this announcement'}), 403
        elif g.user.role == 'teacher':
            # 教师只能查看自己班级的公告或全局公告
            if announcement.scope_type == 'class':
                teacher = g.user.teacher_profile
                if not teacher or not TeacherClass.query.filter_by(
                    teacher_id=teacher.teacher_id, 
                    class_id=announcement.target_class_id
                ).first():
                    return jsonify({'error': 'No permission to view this announcement'}), 403
        
        result = {
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'created_at': announcement.created_at.isoformat() if announcement.created_at else None,
            'author_name': announcement.author.real_name if announcement.author else '系统',
            'scope_type': announcement.scope_type,
            'target_class_name': announcement.target_class.class_name if announcement.target_class else None
        }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Failed to get announcement detail: {e}")
        return jsonify({'error': str(e)}), 500
@api_v1.route('/announcements', methods=['POST'])
@api_login_required
def create_announcement():
    """发布公告"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        title = data.get('title')
        content = data.get('content')
        scope_type = data.get('scope_type', 'global')
        target_class_id = data.get('target_class_id')
        
        if not title or not content:
            return jsonify({'error': 'Missing title or content'}), 400
            
        # Permission check
        if scope_type == 'global':
            if g.user.role != 'admin':
                return jsonify({'error': 'Permission denied'}), 403
            target_class_id = None
        elif scope_type == 'class':
            if current_user.role not in ['teacher', 'admin']:
                return jsonify({'error': 'Permission denied'}), 403
                
            if not target_class_id:
                return jsonify({'error': 'Missing target_class_id'}), 400
                
            if current_user.role == 'teacher':
                 teacher = g.user.teacher_profile
                 is_teaching = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=target_class_id).first()
                 if not is_teaching:
                     pass 
        
        announcement = Announcement(
            id=generate_next_id(Announcement),
            title=title,
            content=content,
            author_id=g.user.user_id,
            scope_type=scope_type,
            target_class_id=target_class_id
        )
        db.session.add(announcement)
        db.session.commit()
        
        return jsonify({'message': 'Announcement created', 'id': announcement.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create announcement: {e}")
        return jsonify({'error': str(e)}), 500

@api_v1.route('/announcements/<int:id>', methods=['DELETE'])
@api_login_required
def delete_announcement(id):
    """删除公告"""
    try:
        announcement = db.session.get(Announcement, id)
        if not announcement:
            return jsonify({'error': 'Not found'}), 404
            
        # Permission check
        if g.user.role == 'admin':
            pass
        elif g.user.user_id == announcement.author_id:
            pass
        else:
            return jsonify({'error': 'Permission denied'}), 403
            
        db.session.delete(announcement)
        db.session.commit()
        
        return jsonify({'message': 'Deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
