"""
Telegram 式频道和讨论组 API

提供频道创建、绑定讨论组、评论管理等功能
"""

from flask import jsonify, request, g
from models import (
    db, Conversation, ConversationMember, IMMessage, Users,
    generate_next_id
)
from . import api_v1
from .auth import api_login_required
from sqlalchemy import or_, and_, func, desc
from datetime import datetime


# ==================== 频道管理 API ====================

@api_v1.route('/chat/channels', methods=['POST'])
@api_login_required
def create_channel():
    """创建频道（并可选自动创建讨论组）"""
    data = request.json
    user_id = g.user.user_id
    
    title = data.get('title')
    description = data.get('description', '')
    auto_create_discussion = data.get('auto_create_discussion', True)
    class_id = data.get('class_id')  # 可选：关联班级
    
    if not title:
        return jsonify({'error': '频道标题不能为空'}), 400
    
    try:
        # 1. 创建频道
        channel_id = generate_next_id(Conversation, 'id')
        channel = Conversation(
            id=channel_id,
            title=title,
            description=description,
            conversation_type='group',
            group_subtype='channel',
            created_by=user_id,
            class_id=class_id
        )
        db.session.add(channel)
        db.session.flush()
        
        # 2. 添加创建者为频道管理员
        member_id = generate_next_id(ConversationMember, 'id')
        channel_member = ConversationMember(
            id=member_id,
            conversation_id=channel_id,
            user_id=user_id,
            role='owner'
        )
        db.session.add(channel_member)
        
        discussion_id = None
        
        # 3. 如果需要，自动创建讨论组
        if auto_create_discussion:
            discussion_id = generate_next_id(Conversation, 'id')
            discussion = Conversation(
                id=discussion_id,
                title=f"{title} 讨论区",
                description=f"{title} 的评论和讨论",
                conversation_type='group',
                group_subtype='discussion',
                created_by=user_id,
                linked_channel_id=channel_id,
                class_id=class_id
            )
            db.session.add(discussion)
            db.session.flush()
            
            # 绑定频道和讨论组
            channel.linked_discussion_id = discussion_id
            
            # 添加创建者为讨论组管理员
            disc_member_id = generate_next_id(ConversationMember, 'id')
            disc_member = ConversationMember(
                id=disc_member_id,
                conversation_id=discussion_id,
                user_id=user_id,
                role='owner'
            )
            db.session.add(disc_member)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'channel': {
                'id': channel_id,
                'title': title,
                'description': description,
                'group_subtype': 'channel',
                'linked_discussion_id': discussion_id
            },
            'discussion_id': discussion_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建频道失败: {str(e)}'}), 500


@api_v1.route('/chat/channels/<int:channel_id>/bind-discussion', methods=['POST'])
@api_login_required
def bind_discussion_group(channel_id):
    """为频道绑定讨论组"""
    data = request.json
    user_id = g.user.user_id
    
    # 检查频道是否存在且用户是否有权限
    channel = Conversation.query.get(channel_id)
    if not channel or channel.group_subtype != 'channel':
        return jsonify({'error': '频道不存在'}), 404
    
    member = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        user_id=user_id
    ).first()
    
    if not member or member.role != 'owner':
        return jsonify({'error': '只有频道所有者可以绑定讨论组'}), 403
    
    try:
        discussion_id = data.get('discussion_id')
        create_new = data.get('create_new', False)
        
        if create_new:
            # 创建新讨论组
            discussion_id = generate_next_id(Conversation, 'id')
            discussion_title = data.get('discussion_title', f"{channel.title} 讨论区")
            
            discussion = Conversation(
                id=discussion_id,
                title=discussion_title,
                description=f"{channel.title} 的评论和讨论",
                conversation_type='group',
                group_subtype='discussion',
                created_by=user_id,
                linked_channel_id=channel_id
            )
            db.session.add(discussion)
            
            # 添加创建者为讨论组管理员
            disc_member_id = generate_next_id(ConversationMember, 'id')
            disc_member = ConversationMember(
                id=disc_member_id,
                conversation_id=discussion_id,
                user_id=user_id,
                role='owner'
            )
            db.session.add(disc_member)
            
        else:
            # 使用现有讨论组
            if not discussion_id:
                return jsonify({'error': '请提供讨论组ID或设置create_new=True'}), 400
            
            discussion = Conversation.query.get(discussion_id)
            if not discussion:
                return jsonify({'error': '讨论组不存在'}), 404
            
            # 检查该讨论组是否已绑定其他频道
            if discussion.linked_channel_id and discussion.linked_channel_id != channel_id:
                return jsonify({'error': '该讨论组已绑定其他频道'}), 400
            
            discussion.linked_channel_id = channel_id
            discussion.group_subtype = 'discussion'
        
        # 绑定频道和讨论组
        channel.linked_discussion_id = discussion_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'channel_id': channel_id,
            'discussion_id': discussion_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'绑定讨论组失败: {str(e)}'}), 500


@api_v1.route('/chat/channels/<int:channel_id>', methods=['GET'])
@api_login_required
def get_channel_info(channel_id):
    """获取频道详细信息"""
    user_id = g.user.user_id
    
    channel = Conversation.query.get(channel_id)
    if not channel or channel.group_subtype != 'channel':
        return jsonify({'error': '频道不存在'}), 404
    
    # 检查用户是否有访问权限
    member = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not member:
        return jsonify({'error': '无权访问该频道'}), 403
    
    # 获取成员数量
    member_count = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        left_at=None
    ).count()
    
    # 获取消息数量
    message_count = IMMessage.query.filter_by(
        conversation_id=channel_id,
        root_message_id=None,  # 只计算主帖
        is_deleted=False
    ).count()
    
    return jsonify({
        'id': channel.id,
        'title': channel.title,
        'description': channel.description,
        'avatar': channel.avatar,
        'group_subtype': channel.group_subtype,
        'linked_discussion_id': channel.linked_discussion_id,
        'created_by': channel.created_by,
        'created_at': channel.created_at.isoformat() if channel.created_at else None,
        'member_count': member_count,
        'message_count': message_count,
        'user_role': member.role,
        'is_pinned': member.is_pinned,
        'is_muted': member.is_muted
    })


# ==================== 频道消息管理 API ====================

@api_v1.route('/chat/channels/<int:channel_id>/posts', methods=['GET'])
@api_login_required
def get_channel_posts(channel_id):
    """获取频道帖子列表（带评论统计）"""
    user_id = g.user.user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    # 检查访问权限
    member = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not member:
        return jsonify({'error': '无权访问该频道'}), 403
    
    # 查询频道帖子（使用子查询统计评论数）
    from sqlalchemy import select, func as sql_func
    
    # 子查询：统计每条消息的评论数
    comment_count_subq = (
        select(
            IMMessage.root_message_id,
            sql_func.count(IMMessage.id).label('count')
        )
        .where(IMMessage.root_message_id.isnot(None))
        .where(IMMessage.is_deleted == False)
        .group_by(IMMessage.root_message_id)
        .subquery()
    )
    
    # 主查询
    posts_query = (
        db.session.query(
            IMMessage,
            sql_func.coalesce(comment_count_subq.c.count, 0).label('comment_count')
        )
        .outerjoin(comment_count_subq, IMMessage.id == comment_count_subq.c.root_message_id)
        .filter(IMMessage.conversation_id == channel_id)
        .filter(IMMessage.root_message_id == None)  # 只查询主帖
        .filter(IMMessage.is_deleted == False)
        .order_by(desc(IMMessage.created_at))
    )
    
    # 分页
    total = posts_query.count()
    posts = posts_query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 组装返回数据
    result = []
    for post, comment_count in posts:
        sender = Users.query.get(post.sender_id)
        result.append({
            'id': post.id,
            'content': post.content,
            'message_type': post.message_type,
            'media_url': post.media_url,
            'sender': {
                'user_id': sender.user_id,
                'username': sender.username,
                'real_name': sender.real_name
            },
            'created_at': post.created_at.isoformat() if post.created_at else None,
            'is_edited': post.is_edited,
            'is_pinned': post.is_pinned,
            'comment_count': comment_count,
            'has_comments': comment_count > 0
        })
    
    return jsonify({
        'posts': result,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    })


# ==================== 评论系统 API ====================

@api_v1.route('/chat/messages/<int:message_id>/comments', methods=['GET'])
@api_login_required
def get_message_comments(message_id):
    """获取某条频道消息的所有评论"""
    user_id = g.user.user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    # 查找原始消息
    original_msg = IMMessage.query.get(message_id)
    if not original_msg:
        return jsonify({'error': '消息不存在'}), 404
    
    # 获取频道信息
    channel = Conversation.query.get(original_msg.conversation_id)
    if not channel or channel.group_subtype != 'channel':
        return jsonify({'error': '该消息不是频道消息'}), 400
    
    # 检查频道绑定的讨论组
    if not channel.linked_discussion_id:
        return jsonify({'comments': [], 'total': 0, 'original_message': None})
    
    # 检查用户是否有权限查看讨论组
    member = ConversationMember.query.filter_by(
        conversation_id=channel.linked_discussion_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    # 查询评论
    comments_query = (
        IMMessage.query
        .filter_by(
            conversation_id=channel.linked_discussion_id,
            root_message_id=message_id,
            is_deleted=False
        )
        .order_by(IMMessage.created_at)
    )
    
    total = comments_query.count()
    comments = comments_query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 组装返回数据
    comments_data = []
    for comment in comments:
        sender = Users.query.get(comment.sender_id)
        
        # 如果有父消息（回复评论），获取父消息信息
        parent_info = None
        if comment.parent_message_id:
            parent = IMMessage.query.get(comment.parent_message_id)
            if parent:
                parent_sender = Users.query.get(parent.sender_id)
                parent_info = {
                    'id': parent.id,
                    'content': parent.content[:100],  # 只返回前100字符
                    'sender_name': parent_sender.real_name if parent_sender else '未知用户'
                }
        
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'message_type': comment.message_type,
            'media_url': comment.media_url,
            'sender': {
                'user_id': sender.user_id,
                'username': sender.username,
                'real_name': sender.real_name
            },
            'parent_message': parent_info,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'is_edited': comment.is_edited
        })
    
    # 返回原始消息信息
    original_sender = Users.query.get(original_msg.sender_id)
    original_data = {
        'id': original_msg.id,
        'content': original_msg.content,
        'message_type': original_msg.message_type,
        'sender': {
            'user_id': original_sender.user_id,
            'real_name': original_sender.real_name
        },
        'created_at': original_msg.created_at.isoformat() if original_msg.created_at else None
    } if original_sender else None
    
    return jsonify({
        'comments': comments_data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'original_message': original_data,
        'can_comment': member is not None
    })


@api_v1.route('/chat/messages/<int:message_id>/comments', methods=['POST'])
@api_login_required
def post_comment(message_id):
    """发表评论"""
    data = request.json
    user_id = g.user.user_id
    
    content = data.get('content', '').strip()
    parent_message_id = data.get('parent_message_id')  # 可选：回复某条评论
    
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    # 查找原始消息
    original_msg = IMMessage.query.get(message_id)
    if not original_msg:
        return jsonify({'error': '消息不存在'}), 404
    
    # 获取频道信息
    channel = Conversation.query.get(original_msg.conversation_id)
    if not channel or channel.group_subtype != 'channel':
        return jsonify({'error': '该消息不是频道消息'}), 400
    
    if not channel.linked_discussion_id:
        return jsonify({'error': '该频道未绑定讨论组'}), 400
    
    # 检查用户是否有权限在讨论组发言
    member = ConversationMember.query.filter_by(
        conversation_id=channel.linked_discussion_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not member:
        return jsonify({'error': '您不是讨论组成员，无法发表评论'}), 403
    
    try:
        # 创建评论消息
        comment_id = generate_next_id(IMMessage, 'id')
        comment = IMMessage(
            id=comment_id,
            conversation_id=channel.linked_discussion_id,
            sender_id=user_id,
            content=content,
            message_type='text',
            root_message_id=message_id,  # 指向频道消息
            parent_message_id=parent_message_id  # 可选：回复某条评论
        )
        db.session.add(comment)
        
        # 更新原始消息的评论计数
        original_msg.comment_count = IMMessage.query.filter_by(
            root_message_id=message_id,
            is_deleted=False
        ).count() + 1
        
        # 更新对话的最后消息时间
        discussion = Conversation.query.get(channel.linked_discussion_id)
        discussion.last_message_at = datetime.now()
        
        db.session.commit()
        
        # 返回创建的评论
        sender = Users.query.get(user_id)
        return jsonify({
            'success': True,
            'comment': {
                'id': comment_id,
                'content': content,
                'sender': {
                    'user_id': sender.user_id,
                    'username': sender.username,
                    'real_name': sender.real_name
                },
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'parent_message_id': parent_message_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'发表评论失败: {str(e)}'}), 500


# ==================== 权限检查辅助函数 ====================

def can_post_in_channel(user_id, channel_id):
    """检查用户是否有权在频道发帖"""
    conversation = Conversation.query.get(channel_id)
    if not conversation:
        return False
    
    # 如果不是频道，所有成员都可以发帖
    if conversation.group_subtype != 'channel':
        return True
    
    # 频道只允许 owner 和 admin 发帖
    member = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    return member and member.role in ['owner', 'admin']
