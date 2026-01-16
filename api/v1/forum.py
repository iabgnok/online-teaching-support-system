# -*- coding: utf-8 -*-
from flask import jsonify, request, current_app
from flask_login import current_user
from functools import wraps
from models import ForumPost, ForumComment, TeachingClass, TeacherClass, StudentClass, db, generate_next_id
from . import api_v1
from datetime import datetime
import os
from werkzeug.utils import secure_filename


def api_login_required(f):
    """API????????401 JSON?????"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip', '7z', 'rar'}

@api_v1.route('/my-classes', methods=['GET'])
@api_login_required
def get_my_classes():
    classes = []
    try:
        if current_user.role == 'student':
            student_profile = current_user.student_profile
            if not student_profile:
                return jsonify([])
            # enrollments via StudentClass
            enrollments = StudentClass.query.filter_by(student_id=student_profile.student_id, status=1).all()
            for e in enrollments:
                if e.teaching_class:
                    classes.append({
                        'id': e.class_id,
                        'name': f"{e.teaching_class.class_name}"
                    })
        elif current_user.role == 'teacher':
            teacher_profile = current_user.teacher_profile
            if not teacher_profile:
                return jsonify([])
            assignments = TeacherClass.query.filter_by(teacher_id=teacher_profile.teacher_id).all()
            for a in assignments:
                if a.teaching_class:
                    classes.append({
                        'id': a.class_id,
                        'name': f"{a.teaching_class.class_name}"
                    })
        elif current_user.role == 'admin':
             all_classes = TeachingClass.query.all()
             for c in all_classes:
                 classes.append({
                     'id': c.class_id,
                     'name': f"{c.class_name} ({c.class_id})"
                 })
    except Exception as e:
        print(f"Error getting my classes: {e}")
        return jsonify([])
             
    return jsonify(classes)

@api_v1.route('/classes/<int:class_id>/forum/posts', methods=['GET'])
@api_login_required
def get_forum_posts(class_id):
    """?????????????"""
    # ???????????????
    
    posts = ForumPost.query.filter_by(class_id=class_id).order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc()).all()
    
    results = []
    for p in posts:
        results.append({
            'id': p.id,
            'title': p.title,
            'content': p.content[:200] + '...' if len(p.content) > 200 else p.content,
            'author_name': p.author.real_name,
            'author_id': p.author_id,
            'author_role': p.author.role,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None,
            'reply_count': p.comments.count(),
            'view_count': p.view_count,
            'is_pinned': p.is_pinned,
            'is_solved': p.is_solved,
            'has_attachment': bool(p.file_path)
        })
    return jsonify(results)

@api_v1.route('/classes/<int:class_id>/forum/posts', methods=['POST'])
@api_login_required
def create_forum_post(class_id):
    """???????????"""
    title = request.form.get('title')
    content = request.form.get('content')
    file = request.files.get('file')
    
    # ??JSON????????
    if not title and not content and request.is_json:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
        
    post = ForumPost(
        id=generate_next_id(ForumPost, 'id'),
        class_id=class_id,
        title=title,
        content=content,
        author_id=current_user.user_id
    )

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Unique filename: post_id_timestamp_filename
        unique_filename = f"{post.id}_{int(datetime.now().timestamp())}_{filename}"
        
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'forum')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        post.file_name = filename
        # Store relative path or just filename. Storing full web path is better if served static, 
        # but here let's store filename and serve via route
        post.file_path = f"uploads/forum/{unique_filename}"
    
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created', 'id': post.id}), 201

@api_v1.route('/forum/posts/<int:post_id>', methods=['GET'])
@api_login_required
def get_post_detail(post_id):
    """?????????"""
    post = ForumPost.query.get_or_404(post_id)
    
    # Update view count
    post.view_count += 1
    db.session.commit()
    
    # Fetch top-level comments
    top_comments = post.comments.filter_by(parent_id=None).order_by(ForumComment.created_at.asc()).all()
    
    def format_comment(c):
        return {
            'id': c.id,
            'content': c.content,
            'author_name': c.author.real_name,
            'author_id': c.author.user_id,
            'author_role': c.author.role,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'is_accepted': c.is_accepted_answer,
            'replies': [format_comment(r) for r in c.replies]
        }

    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author_name': post.author.real_name,
        'author_id': post.author_id,
        'author_role': post.author.role,
        'created_at': post.created_at.isoformat() if post.created_at else None,
        'is_pinned': post.is_pinned,
        'is_solved': post.is_solved,
        'file_name': post.file_name,
        'file_url': f'/api/v1/download/{post.id}' if post.file_path else None, # Helper route needed
        'comments': [format_comment(c) for c in top_comments]
    })


@api_v1.route('/download/<int:post_id>')
@api_login_required
def download_post_file(post_id):
    from flask import send_from_directory
    post = ForumPost.query.get_or_404(post_id)
    if not post.file_path:
        return jsonify({'error': 'No file attached'}), 404
    
    directory = os.path.join(current_app.root_path, 'uploads', 'forum')
    filename = os.path.basename(post.file_path)
    return send_from_directory(directory, filename, as_attachment=True, download_name=post.file_name)


@api_v1.route('/forum/posts/<int:post_id>', methods=['DELETE'])
@api_login_required
def delete_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Permission Check
    can_delete = False
    
    # 1. Admin
    if current_user.role == 'admin':
        can_delete = True
    # 2. Author
    elif post.author_id == current_user.user_id:
        can_delete = True
    # 3. Teacher of this class
    elif current_user.role == 'teacher':
        # Check if teacher teaches this class
        is_teacher = TeacherClass.query.filter_by(
            teacher_id=current_user.teacher_profile.teacher_id, 
            class_id=post.class_id
        ).first()
        if is_teacher:
            # Teacher can delete student posts
            can_delete = True
            
    if not can_delete:
        return jsonify({'error': 'Permission denied'}), 403

    # Delete file if exists
    if post.file_path:
        full_path = os.path.join(current_app.root_path, post.file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except:
                pass # logging error

    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted'})

@api_v1.route('/forum/posts/<int:post_id>', methods=['PUT'])
@api_login_required
def update_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Only author can edit (or maybe admin, but requirement says author edit own)
    if post.author_id != current_user.user_id and current_user.role != 'admin':
         return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    # Simple edit: title/content only for now. Re-uploading file logic can be complex
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
        
    db.session.commit()
    return jsonify({'message': 'Post updated'})


@api_v1.route('/forum/posts/<int:post_id>/comments', methods=['POST'])
@api_login_required
def add_comment(post_id):
    """????/??"""
    data = request.get_json()
    content = data.get('content')
    parent_id = data.get('parent_id') # Optional for nested replies
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
        
    comment = ForumComment(
        id=generate_next_id(ForumComment, 'id'),
        post_id=post_id,
        content=content,
        author_id=current_user.user_id,
        parent_id=parent_id
    )
    
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added', 'id': comment.id}), 201

@api_v1.route('/forum/comments/<int:comment_id>', methods=['DELETE'])
@api_login_required
def delete_comment(comment_id):
    comment = ForumComment.query.get_or_404(comment_id)
    post = comment.post
    
    # Permission Check (Similar logic to post)
    can_delete = False
    
    if current_user.role == 'admin':
        can_delete = True
    elif comment.author_id == current_user.user_id:
        can_delete = True
    elif current_user.role == 'teacher':
        is_teacher = TeacherClass.query.filter_by(
            teacher_id=current_user.teacher_profile.teacher_id, 
            class_id=post.class_id
        ).first()
        if is_teacher:
            can_delete = True
            
    if not can_delete:
        return jsonify({'error': 'Permission denied'}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted'})

@api_v1.route('/forum/comments/<int:comment_id>', methods=['PUT'])
@api_login_required
def update_comment(comment_id):
    comment = ForumComment.query.get_or_404(comment_id)
    
    if comment.author_id != current_user.user_id and current_user.role != 'admin':
         return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    if 'content' in data:
        comment.content = data['content']
        
    db.session.commit()
    return jsonify({'message': 'Comment updated'})
