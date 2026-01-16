# -*- coding: utf-8 -*-
"""论坛管理和审核API"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from models import (
    ForumPost, ForumComment, ForumModeration, ForumPostStatus,
    TeachingClass, TeacherClass, db, generate_next_id
)
from permission_manager import (
    forum_admin_required, content_reviewer_required, api_login_required
)
from datetime import datetime
import os

forum_mgmt_bp = Blueprint('forum_management', __name__, url_prefix='/api/v1/forum-management')


# ==================== 论坛内容管理 ====================

@forum_mgmt_bp.route('/admin/posts', methods=['GET'])
@forum_admin_required
def get_all_forum_posts():
    """获取所有论坛帖子（管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        class_id = request.args.get('class_id', type=int)
        author_id = request.args.get('author_id', type=int)
        status_filter = request.args.get('status', '')  # 'hidden', 'locked', 'flagged', 'normal'
        
        query = ForumPost.query
        
        if class_id:
            query = query.filter_by(class_id=class_id)
        if author_id:
            query = query.filter_by(author_id=author_id)
        
        # 应用状态过滤
        if status_filter == 'hidden':
            query = query.join(ForumPostStatus).filter(ForumPostStatus.is_hidden == True)
        elif status_filter == 'locked':
            query = query.join(ForumPostStatus).filter(ForumPostStatus.is_locked == True)
        elif status_filter == 'flagged':
            query = query.join(ForumPostStatus).filter(ForumPostStatus.is_flagged == True)
        elif status_filter == 'normal':
            query = query.outerjoin(ForumPostStatus).filter(
                (ForumPostStatus.is_hidden == False) | (ForumPostStatus.id == None)
            )
        
        paginated = query.order_by(ForumPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        posts = []
        for p in paginated.items:
            status = p.status_tracking[0] if p.status_tracking else None
            posts.append({
                'id': p.id,
                'title': p.title,
                'content': p.content[:100] + '...' if len(p.content) > 100 else p.content,
                'author_name': p.author.real_name,
                'author_id': p.author_id,
                'class_id': p.class_id,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'view_count': p.view_count,
                'reply_count': p.comments.count(),
                'is_pinned': p.is_pinned,
                'is_hidden': status.is_hidden if status else False,
                'is_locked': status.is_locked if status else False,
                'is_flagged': status.is_flagged if status else False,
                'warning_level': status.warning_level if status else 0
            })
        
        return jsonify({
            'posts': posts,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get all forum posts: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/pin', methods=['POST'])
@forum_admin_required
def pin_post(post_id):
    """置顶帖子"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', '管理员置顶')
        
        post.is_pinned = True
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='pin',
            reason=reason,
            status='completed'
        )
        
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post pinned', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to pin post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/unpin', methods=['POST'])
@forum_admin_required
def unpin_post(post_id):
    """取消置顶"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', '管理员取消置顶')
        
        post.is_pinned = False
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='unpin',
            reason=reason,
            status='completed'
        )
        
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post unpinned', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to unpin post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/hide', methods=['POST'])
@forum_admin_required
def hide_post(post_id):
    """隐藏帖子（不显示给普通用户，仅管理员和作者可见）"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', '内容违规')
        
        # 获取或创建状态记录
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if not status:
            status = ForumPostStatus(
                id=generate_next_id(ForumPostStatus, 'id'),
                post_id=post_id
            )
        
        status.is_hidden = True
        status.hide_reason = reason
        status.hidden_by = current_user.admin_profile.admin_id
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='hide',
            reason=reason,
            status='completed'
        )
        
        db.session.add(status)
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post hidden', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to hide post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/unhide', methods=['POST'])
@forum_admin_required
def unhide_post(post_id):
    """显示隐藏的帖子"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if status:
            status.is_hidden = False
            status.hide_reason = None
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='unhide',
            reason='管理员恢复显示',
            status='completed'
        )
        
        if status:
            db.session.add(status)
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post unhidden', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to unhide post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/lock', methods=['POST'])
@forum_admin_required
def lock_post(post_id):
    """锁定帖子（禁止回复）"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', '讨论已结束')
        
        # 获取或创建状态记录
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if not status:
            status = ForumPostStatus(
                id=generate_next_id(ForumPostStatus, 'id'),
                post_id=post_id
            )
        
        status.is_locked = True
        status.lock_reason = reason
        status.locked_by = current_user.admin_profile.admin_id
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='lock',
            reason=reason,
            status='completed'
        )
        
        db.session.add(status)
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post locked', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to lock post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/unlock', methods=['POST'])
@forum_admin_required
def unlock_post(post_id):
    """解锁帖子"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if status:
            status.is_locked = False
            status.lock_reason = None
        
        # 记录审核日志
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='unlock',
            reason='管理员解锁',
            status='completed'
        )
        
        if status:
            db.session.add(status)
        db.session.add(moderation)
        db.session.commit()
        
        return jsonify({'message': 'Post unlocked', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to unlock post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/delete', methods=['DELETE'])
@forum_admin_required
def admin_delete_post(post_id):
    """管理员删除帖子（保存备份）"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', '内容违规')
        
        # 保存内容备份
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='post',
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='delete',
            reason=reason,
            content_snapshot=f"标题: {post.title}\n内容: {post.content}",
            status='completed'
        )
        
        # 删除附件
        if post.file_path:
            full_path = os.path.join(current_app.root_path, post.file_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except:
                pass
        
        db.session.add(moderation)
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted by admin', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to delete post: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 评论管理 ====================

@forum_mgmt_bp.route('/admin/comments/<int:comment_id>/delete', methods=['DELETE'])
@forum_admin_required
def admin_delete_comment(comment_id):
    """管理员删除评论"""
    try:
        comment = ForumComment.query.get_or_404(comment_id)
        post_id = comment.post_id
        
        data = request.get_json() or {}
        reason = data.get('reason', '内容违规')
        
        # 保存内容备份
        moderation = ForumModeration(
            id=generate_next_id(ForumModeration, 'id'),
            content_type='comment',
            comment_id=comment_id,
            post_id=post_id,
            admin_id=current_user.admin_profile.admin_id,
            action='delete',
            reason=reason,
            content_snapshot=f"评论: {comment.content}",
            status='completed'
        )
        
        db.session.add(moderation)
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': 'Comment deleted by admin', 'comment_id': comment_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to delete comment: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 内容审核 ====================

@forum_mgmt_bp.route('/review/flagged-posts', methods=['GET'])
@content_reviewer_required
def get_flagged_posts():
    """获取标记为需要审核的帖子列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ForumPost.query.join(ForumPostStatus).filter(
            ForumPostStatus.is_flagged == True
        )
        
        paginated = query.order_by(ForumPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        posts = []
        for p in paginated.items:
            status = p.status_tracking[0] if p.status_tracking else None
            posts.append({
                'id': p.id,
                'title': p.title,
                'content': p.content[:200] + '...' if len(p.content) > 200 else p.content,
                'author_name': p.author.real_name,
                'author_id': p.author_id,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'warning_level': status.warning_level if status else 0,
                'warning_message': status.warning_message if status else None
            })
        
        return jsonify({
            'posts': posts,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get flagged posts: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/flag', methods=['POST'])
@forum_admin_required
def flag_post_for_review(post_id):
    """标记帖子需要审核"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        data = request.get_json() or {}
        warning_level = data.get('warning_level', 1)  # 1=轻度, 2=中度, 3=严重
        warning_message = data.get('warning_message', '该内容需要审核')
        
        # 获取或创建状态记录
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if not status:
            status = ForumPostStatus(
                id=generate_next_id(ForumPostStatus, 'id'),
                post_id=post_id
            )
        
        status.is_flagged = True
        status.warning_level = warning_level
        status.warning_message = warning_message
        
        db.session.add(status)
        db.session.commit()
        
        return jsonify({'message': 'Post flagged for review', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to flag post: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/posts/<int:post_id>/unflag', methods=['POST'])
@forum_admin_required
def unflag_post(post_id):
    """取消审核标记"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        status = ForumPostStatus.query.filter_by(post_id=post_id).first()
        if status:
            status.is_flagged = False
            status.warning_level = 0
            status.warning_message = None
            db.session.add(status)
        
        db.session.commit()
        
        return jsonify({'message': 'Post unflagged', 'post_id': post_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to unflag post: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 审核日志 ====================

@forum_mgmt_bp.route('/admin/moderation-logs', methods=['GET'])
@forum_admin_required
def get_moderation_logs():
    """获取审核日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        admin_id = request.args.get('admin_id', type=int)
        action = request.args.get('action', '')
        
        query = ForumModeration.query
        
        if admin_id:
            query = query.filter_by(admin_id=admin_id)
        if action:
            query = query.filter_by(action=action)
        
        paginated = query.order_by(ForumModeration.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = []
        for log in paginated.items:
            logs.append({
                'id': log.id,
                'content_type': log.content_type,
                'post_id': log.post_id,
                'comment_id': log.comment_id,
                'admin_name': log.moderator.user.real_name if log.moderator else 'System',
                'action': log.action,
                'reason': log.reason,
                'status': log.status,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            })
        
        return jsonify({
            'logs': logs,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get moderation logs: {e}")
        return jsonify({'error': str(e)}), 500


@forum_mgmt_bp.route('/admin/moderation-logs/<int:log_id>/reverse', methods=['POST'])
@forum_admin_required
def reverse_moderation_action(log_id):
    """撤销审核操作"""
    try:
        log = ForumModeration.query.get_or_404(log_id)
        
        if log.status == 'reversed':
            return jsonify({'error': 'This action has already been reversed'}), 400
        
        # 根据操作类型撤销
        if log.action == 'hide' and log.post_id:
            post = ForumPost.query.get(log.post_id)
            if post:
                status = ForumPostStatus.query.filter_by(post_id=log.post_id).first()
                if status:
                    status.is_hidden = False
                    db.session.add(status)
        
        elif log.action == 'lock' and log.post_id:
            post = ForumPost.query.get(log.post_id)
            if post:
                status = ForumPostStatus.query.filter_by(post_id=log.post_id).first()
                if status:
                    status.is_locked = False
                    db.session.add(status)
        
        log.status = 'reversed'
        log.reversed_at = datetime.now()
        log.reversed_by = current_user.admin_profile.admin_id
        
        db.session.commit()
        
        return jsonify({'message': 'Moderation action reversed', 'log_id': log_id}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to reverse moderation action: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== 统计和报告 ====================

@forum_mgmt_bp.route('/admin/statistics', methods=['GET'])
@forum_admin_required
def get_forum_statistics():
    """获取论坛统计信息"""
    try:
        total_posts = ForumPost.query.count()
        total_comments = ForumComment.query.count()
        total_hidden_posts = ForumPostStatus.query.filter_by(is_hidden=True).count()
        total_locked_posts = ForumPostStatus.query.filter_by(is_locked=True).count()
        total_flagged_posts = ForumPostStatus.query.filter_by(is_flagged=True).count()
        
        # 最活跃的讨论区（按帖子数）
        active_classes = db.session.query(
            ForumPost.class_id,
            db.func.count(ForumPost.id).label('post_count'),
            db.func.count(ForumComment.id).label('comment_count')
        ).outerjoin(ForumComment, ForumPost.id == ForumComment.post_id).group_by(
            ForumPost.class_id
        ).order_by(db.func.count(ForumPost.id).desc()).limit(10).all()
        
        # 最活跃的用户
        active_users = db.session.query(
            ForumPost.author_id,
            db.func.count(ForumPost.id).label('post_count')
        ).group_by(ForumPost.author_id).order_by(
            db.func.count(ForumPost.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'total_posts': total_posts,
            'total_comments': total_comments,
            'total_hidden_posts': total_hidden_posts,
            'total_locked_posts': total_locked_posts,
            'total_flagged_posts': total_flagged_posts,
            'active_classes': len(active_classes),
            'active_users': len(active_users)
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get forum statistics: {e}")
        return jsonify({'error': str(e)}), 500
