from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from models import Announcement, TeacherClass, db, generate_next_id, TeachingClass
from . import api_v1
from datetime import datetime

@api_v1.route('/announcements', methods=['GET'])
# @login_required
def get_announcements():
    """获取公告列表"""
    try:
        # if not current_user.is_authenticated:
        #     return jsonify({'error': 'Authentication required'}), 401
            
        scope = request.args.get('scope', 'global') # global or class
    
        if scope == 'global':
            announcements = Announcement.query.filter_by(scope_type='global').order_by(Announcement.created_at.desc()).limit(20).all()
        elif scope == 'class':
            # Get announcements for classes the user is enrolled in (student) or teaching (teacher)
            class_ids = []
            
            # Safe check for authenticated user roles
            if current_user.is_authenticated:
                if current_user.role == 'student' and current_user.student_profile:
                    student = current_user.student_profile
                    class_ids = [e.class_id for e in student.enrollments]
                elif current_user.role == 'teacher' and current_user.teacher_profile:
                    teacher = current_user.teacher_profile
                    # 兼容不同的关联方式
                    class_ids = [] 
                else:
                    class_ids = []
            else:
                class_ids = []
                
            if class_ids:
                announcements = Announcement.query.filter(
                    Announcement.scope_type == 'class',
                    Announcement.target_class_id.in_(class_ids)
                ).order_by(Announcement.created_at.desc()).limit(20).all()
            else:
                announcements = []
        else:
            return jsonify({'error': 'Invalid scope'}), 400

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

@api_v1.route('/announcements', methods=['POST'])
@login_required
def create_announcement():
    """发布公告"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
            
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
            if current_user.role != 'admin':
                return jsonify({'error': 'Permission denied'}), 403
            target_class_id = None
        elif scope_type == 'class':
            if current_user.role not in ['teacher', 'admin']:
                return jsonify({'error': 'Permission denied'}), 403
                
            if not target_class_id:
                return jsonify({'error': 'Missing target_class_id'}), 400
                
            if current_user.role == 'teacher':
                 teacher = current_user.teacher_profile
                 is_teaching = TeacherClass.query.filter_by(teacher_id=teacher.teacher_id, class_id=target_class_id).first()
                 if not is_teaching:
                     pass 
        
        announcement = Announcement(
            id=generate_next_id(Announcement),
            title=title,
            content=content,
            author_id=current_user.user_id,
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
@login_required
def delete_announcement(id):
    """删除公告"""
    try:
        announcement = db.session.get(Announcement, id)
        if not announcement:
            return jsonify({'error': 'Not found'}), 404
            
        # Permission check
        if current_user.role == 'admin':
            pass
        elif current_user.user_id == announcement.author_id:
            pass
        else:
            return jsonify({'error': 'Permission denied'}), 403
            
        db.session.delete(announcement)
        db.session.commit()
        
        return jsonify({'message': 'Deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
