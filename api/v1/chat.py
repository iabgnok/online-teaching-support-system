"""
即时通讯API端点
提供对话管理和消息收发功能
"""

from flask import jsonify, request, g
from werkzeug.utils import secure_filename
from models import (
    db, Conversation, ConversationMember, IMMessage, MessageStatus, 
    UserOnlineStatus, Users, TeachingClass, generate_next_id,
    MessageReaction, PinnedMessage, MentionNotification
)
from . import api_v1
from .auth import api_login_required
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, timedelta
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# ==================== 辅助函数 ====================

def extract_link_preview(url):
    """提取网页链接预览信息"""
    try:
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 发送请求，设置超时
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取 Open Graph 标签
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        
        # 如果没有 OG 标签，使用普通标签
        title = og_title['content'] if og_title else (soup.find('title').text if soup.find('title') else url)
        description = og_description['content'] if og_description else ''
        image = og_image['content'] if og_image else ''
        
        # 获取域名
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        return {
            'url': url,
            'title': title[:200],  # 限制长度
            'description': description[:500] if description else '',
            'image': image,
            'domain': domain
        }
    except Exception as e:
        # 如果获取失败，返回基本信息
        parsed_url = urlparse(url)
        return {
            'url': url,
            'title': parsed_url.netloc,
            'description': '',
            'image': '',
            'domain': parsed_url.netloc
        }


# ==================== 对话管理 API ====================

@api_v1.route('/chat/conversations', methods=['GET'])
@api_login_required
def get_conversations():
    """获取用户的所有对话列表"""
    user_id = g.user.user_id
    
    # 查询用户参与的所有对话
    memberships = ConversationMember.query.filter_by(
        user_id=user_id,
        left_at=None  # 只显示未退出的对话
    ).all()
    
    conversations = []
    for membership in memberships:
        conv = membership.conversation
        
        # 获取最后一条消息
        last_message = IMMessage.query.filter_by(
            conversation_id=conv.id,
            is_deleted=False
        ).order_by(desc(IMMessage.created_at)).first()
        
        # 构建对话信息
        conv_data = {
            'id': conv.id,
            'type': conv.conversation_type,
            'title': conv.title,
            'avatar': conv.avatar,
            'is_pinned': membership.is_pinned,
            'is_muted': membership.is_muted,
            'unread_count': membership.unread_count,
            'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
            'last_message': None,
            'class_id': conv.class_id,  # 添加班级ID
            'member_count': ConversationMember.query.filter_by(
                conversation_id=conv.id,
                left_at=None
            ).count()  # 添加成员数量
        }
        
        # 如果是私聊，获取对方信息
        if conv.conversation_type == 'private':
            # 找到对方
            other_member = ConversationMember.query.filter(
                ConversationMember.conversation_id == conv.id,
                ConversationMember.user_id != user_id
            ).first()
            
            if other_member:
                other_user = other_member.user
                conv_data['title'] = other_user.real_name
                conv_data['other_user'] = {
                    'user_id': other_user.user_id,
                    'username': other_user.username,
                    'real_name': other_user.real_name,
                    'role': other_user.role
                }
                
                # 获取在线状态
                online_status = UserOnlineStatus.query.get(other_user.user_id)
                if online_status:
                    conv_data['other_user']['is_online'] = online_status.is_online
                    conv_data['other_user']['last_seen'] = online_status.last_seen.isoformat()
        
        # 添加最后一条消息信息
        if last_message:
            conv_data['last_message'] = {
                'content': last_message.content,
                'sender_name': last_message.sender.real_name,
                'created_at': last_message.created_at.isoformat(),
                'message_type': last_message.message_type
            }
        
        # 添加草稿
        if membership.draft_content:
            conv_data['draft'] = membership.draft_content
        
        conversations.append(conv_data)
    
    # 按置顶和更新时间排序
    conversations.sort(key=lambda x: (not x['is_pinned'], x['updated_at'] or ''), reverse=True)
    
    return jsonify(conversations)


@api_v1.route('/chat/conversations', methods=['POST'])
@api_login_required
def create_conversation():
    """创建新对话（私聊、群聊、班级群组或课程群组）"""
    data = request.get_json()
    conversation_type = data.get('type', 'private')  # private, group, class_group, course_group
    title = data.get('title')
    member_ids = data.get('member_ids', [])  # 成员ID列表
    class_id = data.get('class_id')  # 课程班级ID（班级群组和课程群组需要）
    
    user_id = g.user.user_id
    
    # 验证对话类型
    valid_types = ['private', 'group', 'class_group', 'course_group', 'live_class']
    if conversation_type not in valid_types:
        return jsonify({'error': '无效的对话类型'}), 400
    
    # 私聊必须指定一个对方
    if conversation_type == 'private':
        if not member_ids or len(member_ids) != 1:
            return jsonify({'error': '私聊需要指定一个对话对象'}), 400
        
        other_user_id = member_ids[0]
        
        # 检查是否已存在该私聊
        existing = db.session.query(Conversation).join(ConversationMember).filter(
            Conversation.conversation_type == 'private',
            ConversationMember.user_id.in_([user_id, other_user_id])
        ).group_by(Conversation.id).having(
            func.count(ConversationMember.id) == 2
        ).first()
        
        if existing:
            return jsonify({'id': existing.id, 'message': '对话已存在'}), 200
    
    # 班级群组和课程群组需要class_id
    if conversation_type in ['class_group', 'course_group']:
        if not class_id:
            return jsonify({'error': '班级群组和课程群组需要指定班级ID'}), 400
        
        # 验证用户是否有权限创建该班级的群组
        teaching_class = TeachingClass.query.get(class_id)
        if not teaching_class:
            return jsonify({'error': '班级不存在'}), 404
        
        # 检查是否已存在该类型的群组
        existing_group = Conversation.query.filter_by(
            conversation_type=conversation_type,
            class_id=class_id,
            is_active=True
        ).first()
        
        if existing_group:
            return jsonify({'id': existing_group.id, 'message': '该班级的群组已存在'}), 200
        
        # 自动设置标题
        if not title:
            if conversation_type == 'class_group':
                title = f"{teaching_class.class_name} - 班级群"
            else:
                title = f"{teaching_class.class_name} - 课程群"
    
    # 普通群聊需要标题
    if conversation_type == 'group' and not title:
        return jsonify({'error': '群聊需要指定名称'}), 400
    
    # 创建对话
    conversation = Conversation(
        id=generate_next_id(Conversation),
        conversation_type=conversation_type,
        title=title,
        created_by=user_id,
        class_id=class_id
    )
    db.session.add(conversation)
    
    # 添加创建者为成员
    creator_member = ConversationMember(
        id=generate_next_id(ConversationMember),
        conversation_id=conversation.id,
        user_id=user_id,
        role='owner'
    )
    db.session.add(creator_member)
    
    # 添加其他成员
    if conversation_type in ['class_group', 'course_group']:
        # 班级群组：添加所有学生和教师
        # 课程群组：只添加教师
        if conversation_type == 'class_group':
            # 查找所有班级学生
            from models import StudentClass
            students = StudentClass.query.filter_by(class_id=class_id).all()
            for student in students:
                if student.student_id != user_id:
                    member = ConversationMember(
                        id=generate_next_id(ConversationMember),
                        conversation_id=conversation.id,
                        user_id=student.student_id,
                        role='member'
                    )
                    db.session.add(member)
        
        # 添加教师（两种群组都需要）
        from models import TeacherClass
        teachers = TeacherClass.query.filter_by(class_id=class_id).all()
        for teacher in teachers:
            if teacher.teacher_id != user_id:
                member = ConversationMember(
                    id=generate_next_id(ConversationMember),
                    conversation_id=conversation.id,
                    user_id=teacher.teacher_id,
                    role='admin'
                )
                db.session.add(member)
    else:
        # 普通群聊和私聊：根据指定的member_ids添加
        for member_id in member_ids:
            if member_id != user_id:
                member = ConversationMember(
                    id=generate_next_id(ConversationMember),
                    conversation_id=conversation.id,
                    user_id=member_id,
                    role='member'
                )
                db.session.add(member)
    
    db.session.commit()
    
    return jsonify({
        'id': conversation.id,
        'type': conversation.conversation_type,
        'title': conversation.title,
        'message': '对话创建成功'
    }), 201


@api_v1.route('/chat/conversations/<int:conversation_id>', methods=['GET'])
@api_login_required
def get_conversation_detail(conversation_id):
    """获取对话详情"""
    user_id = g.user.user_id
    
    # 验证用户是否是该对话成员
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # 获取所有成员
    members = []
    for member in conversation.members.filter_by(left_at=None):
        user = member.user
        member_data = {
            'user_id': user.user_id,
            'username': user.username,
            'real_name': user.real_name,
            'role': member.role,
            'joined_at': member.joined_at.isoformat()
        }
        
        # 获取在线状态
        online_status = UserOnlineStatus.query.get(user.user_id)
        if online_status:
            member_data['is_online'] = online_status.is_online
            member_data['last_seen'] = online_status.last_seen.isoformat()
        
        members.append(member_data)
    
    return jsonify({
        'id': conversation.id,
        'type': conversation.conversation_type,
        'title': conversation.title,
        'avatar': conversation.avatar,
        'description': conversation.description,
        'created_by': conversation.created_by,
        'created_at': conversation.created_at.isoformat(),
        'members': members,
        'member_count': len(members)
    })


@api_v1.route('/chat/conversations/<int:conversation_id>', methods=['PUT'])
@api_login_required
def update_conversation(conversation_id):
    """更新对话信息（标题、头像等）"""
    user_id = g.user.user_id
    data = request.get_json()
    
    # 验证权限（需要是owner或admin）
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not membership or membership.role not in ['owner', 'admin']:
        return jsonify({'error': '无权修改对话信息'}), 403
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # 更新字段
    if 'title' in data:
        conversation.title = data['title']
    if 'avatar' in data:
        conversation.avatar = data['avatar']
    if 'description' in data:
        conversation.description = data['description']
    
    conversation.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({'message': '对话信息已更新'})


@api_v1.route('/chat/conversations/<int:conversation_id>/members', methods=['POST'])
@api_login_required
def add_conversation_member(conversation_id):
    """添加对话成员（仅限群组）"""
    user_id = g.user.user_id
    data = request.get_json()
    new_member_id = data.get('user_id')
    
    if not new_member_id:
        return jsonify({'error': '缺少用户ID'}), 400
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not membership or membership.role not in ['owner', 'admin']:
        return jsonify({'error': '无权添加成员'}), 403
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.conversation_type == 'private':
        return jsonify({'error': '私聊不支持添加成员'}), 400
    
    # 检查是否已是成员
    existing = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=new_member_id,
        left_at=None
    ).first()
    
    if existing:
        return jsonify({'error': '用户已是成员'}), 400
    
    # 添加新成员
    new_member = ConversationMember(
        id=generate_next_id(ConversationMember),
        conversation_id=conversation_id,
        user_id=new_member_id,
        role='member'
    )
    db.session.add(new_member)
    
    # 创建系统消息
    system_msg = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=conversation_id,
        sender_id=user_id,
        message_type='system',
        content=f'{g.user.real_name} 邀请 {new_member.user.real_name} 加入了群组'
    )
    db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '成员已添加'})


@api_v1.route('/chat/conversations/<int:conversation_id>/members/<int:member_id>', methods=['DELETE'])
@api_login_required
def remove_conversation_member(conversation_id, member_id):
    """移除对话成员"""
    user_id = g.user.user_id
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not membership or membership.role not in ['owner', 'admin']:
        return jsonify({'error': '无权移除成员'}), 403
    
    # 找到要移除的成员
    target_member = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=member_id
    ).first()
    
    if not target_member:
        return jsonify({'error': '成员不存在'}), 404
    
    # 标记为已离开
    target_member.left_at = datetime.now()
    
    # 创建系统消息
    system_msg = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=conversation_id,
        sender_id=user_id,
        message_type='system',
        content=f'{target_member.user.real_name} 被移出了群组'
    )
    db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '成员已移除'})


# ==================== 消息管理 API ====================

@api_v1.route('/chat/conversations/<int:conversation_id>/messages', methods=['GET'])
@api_login_required
def get_chat_messages(conversation_id):
    """获取对话消息列表（分页）"""
    user_id = g.user.user_id
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    before_id = request.args.get('before_id', type=int)  # 加载该消息之前的消息
    
    # 构建查询
    query = IMMessage.query.filter_by(
        conversation_id=conversation_id,
        is_deleted=False
    )
    
    if before_id:
        query = query.filter(IMMessage.id < before_id)
    
    # 按时间倒序
    messages = query.order_by(desc(IMMessage.created_at)).limit(per_page).all()
    
    # 反转顺序，让最新的在最后
    messages.reverse()
    
    result = []
    for msg in messages:
        # 检查是否对当前用户隐藏
        if msg.extra_data and 'hidden_for_users' in msg.extra_data:
            if user_id in msg.extra_data['hidden_for_users']:
                continue  # 跳过对该用户隐藏的消息
        
        msg_data = {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.real_name,
            'sender_avatar': None,  # TODO: 添加头像字段
            'content': msg.content,
            'message_type': msg.message_type,
            'media_url': msg.media_url,
            'file_name': msg.file_name,
            'file_size': msg.file_size,
            'reply_to_id': msg.reply_to_id,
            'forward_from_id': msg.forward_from_id,
            'is_edited': msg.is_edited,
            'created_at': msg.created_at.isoformat(),
            'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
            'extra_data': msg.extra_data
        }
        
        # 如果是回复消息，获取被回复的消息
        if msg.reply_to_id:
            reply_to = IMMessage.query.get(msg.reply_to_id)
            if reply_to:
                msg_data['reply_to'] = {
                    'id': reply_to.id,
                    'sender_name': reply_to.sender.real_name,
                    'content': reply_to.content[:50] + '...' if len(reply_to.content) > 50 else reply_to.content
                }
        
        # 获取消息的反应统计
        reactions = MessageReaction.query.filter_by(message_id=msg.id).all()
        if reactions:
            reaction_summary = {}
            for r in reactions:
                if r.reaction not in reaction_summary:
                    reaction_summary[r.reaction] = {
                        'reaction': r.reaction,
                        'count': 0,
                        'users': [],
                        'i_reacted': False
                    }
                reaction_summary[r.reaction]['count'] += 1
                reaction_summary[r.reaction]['users'].append(r.user_id)
                if r.user_id == user_id:
                    reaction_summary[r.reaction]['i_reacted'] = True
            
            msg_data['reactions'] = list(reaction_summary.values())
        else:
            msg_data['reactions'] = []
        
        # 标记是否被置顶
        is_pinned = PinnedMessage.query.filter_by(
            conversation_id=conversation_id,
            message_id=msg.id
        ).first()
        msg_data['is_pinned'] = bool(is_pinned)
        
        result.append(msg_data)
    
    return jsonify({
        'messages': result,
        'has_more': len(messages) == per_page
    })


@api_v1.route('/chat/conversations/<int:conversation_id>/messages', methods=['POST'])
@api_login_required
def send_chat_message(conversation_id):
    """发送消息"""
    user_id = g.user.user_id
    data = request.get_json()
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权发送消息'}), 403
    
    content = data.get('content', '')
    message_type = data.get('message_type', 'text')
    reply_to_id = data.get('reply_to_id')
    
    if not content and message_type == 'text':
        return jsonify({'error': '消息内容不能为空'}), 400
    
    # 提取 @ 提及的用户
    mentioned_users = []
    if message_type == 'text' and content:
        # 匹配 @username 或 @用户名 格式
        mention_pattern = r'@(\S+)'
        matches = re.findall(mention_pattern, content)
        
        if matches:
            # 查找被提及的用户
            for username in matches:
                # 尝试按用户名或真实姓名查找
                mentioned_user = Users.query.filter(
                    or_(
                        Users.username == username,
                        Users.real_name == username
                    )
                ).first()
                
                if mentioned_user:
                    # 检查被提及用户是否是对话成员
                    is_member = ConversationMember.query.filter_by(
                        conversation_id=conversation_id,
                        user_id=mentioned_user.user_id,
                        left_at=None
                    ).first()
                    
                    if is_member and mentioned_user.user_id != user_id:
                        mentioned_users.append(mentioned_user.user_id)
    
    # 创建消息
    extra_data = data.get('extra_data') or {}
    if mentioned_users:
        extra_data['mentioned_users'] = mentioned_users
    
    message = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=conversation_id,
        sender_id=user_id,
        content=content,
        message_type=message_type,
        reply_to_id=reply_to_id,
        media_url=data.get('media_url'),
        file_name=data.get('file_name'),
        file_size=data.get('file_size'),
        extra_data=extra_data if extra_data else None
    )
    db.session.add(message)
    db.session.flush()  # 获取 message.id
    
    # 创建 @ 提及通知
    for mentioned_user_id in mentioned_users:
        mention_notification = MentionNotification(
            id=generate_next_id(MentionNotification),
            message_id=message.id,
            mentioned_user_id=mentioned_user_id,
            is_read=False
        )
        db.session.add(mention_notification)
    
    # 更新对话最后消息时间
    conversation = Conversation.query.get(conversation_id)
    conversation.last_message_at = datetime.now()
    conversation.updated_at = datetime.now()
    
    # 更新其他成员的未读计数
    other_members = ConversationMember.query.filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id != user_id,
        ConversationMember.left_at.is_(None)
    ).all()
    
    for member in other_members:
        member.unread_count += 1
        
        # 创建消息状态记录
        status = MessageStatus(
            id=generate_next_id(MessageStatus),
            message_id=message.id,
            user_id=member.user_id,
            status='sent'
        )
        db.session.add(status)
    
    # 清空发送者的草稿
    membership.draft_content = None
    membership.draft_updated_at = None
    
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'created_at': message.created_at.isoformat(),
        'message': '消息已发送'
    }), 201


@api_v1.route('/chat/messages/<int:message_id>', methods=['PUT'])
@api_login_required
def edit_chat_message(message_id):
    """编辑消息"""
    user_id = g.user.user_id
    data = request.get_json()
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 只能编辑自己的消息
    if message.sender_id != user_id:
        return jsonify({'error': '无权编辑该消息'}), 403
    
    # 只能编辑文本消息
    if message.message_type != 'text':
        return jsonify({'error': '只能编辑文本消息'}), 400
    
    new_content = data.get('content', '').strip()
    if not new_content:
        return jsonify({'error': '消息内容不能为空'}), 400
    
    message.content = new_content
    message.is_edited = True
    message.edited_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': '消息已编辑'})


@api_v1.route('/chat/messages/<int:message_id>', methods=['DELETE'])
@api_login_required
def delete_chat_message(message_id):
    """删除消息"""
    user_id = g.user.user_id
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 只能删除自己的消息
    if message.sender_id != user_id:
        return jsonify({'error': '无权删除该消息'}), 403
    
    message.is_deleted = True
    message.deleted_at = datetime.now()
    message.content = '[消息已删除]'
    
    db.session.commit()
    
    return jsonify({'message': '消息已删除'})


@api_v1.route('/chat/messages/<int:message_id>/read', methods=['POST'])
@api_login_required
def mark_chat_message_read(message_id):
    """标记消息为已读"""
    user_id = g.user.user_id
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=message.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 更新或创建消息状态
    status = MessageStatus.query.filter_by(
        message_id=message_id,
        user_id=user_id
    ).first()
    
    if not status:
        status = MessageStatus(
            id=generate_next_id(MessageStatus),
            message_id=message_id,
            user_id=user_id,
            status='read'
        )
        db.session.add(status)
    else:
        status.status = 'read'
        status.timestamp = datetime.now()
    
    # 更新成员的最后已读消息ID和时间
    membership.last_read_message_id = message_id
    membership.last_read_at = datetime.now()
    
    # 减少未读计数
    if membership.unread_count > 0:
        membership.unread_count -= 1
    
    db.session.commit()
    
    return jsonify({'message': '已标记为已读'})


@api_v1.route('/chat/conversations/<int:conversation_id>/read_all', methods=['POST'])
@api_login_required
def mark_conversation_read(conversation_id):
    """标记对话所有消息为已读"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 获取最后一条消息
    last_message = IMMessage.query.filter_by(
        conversation_id=conversation_id,
        is_deleted=False
    ).order_by(desc(IMMessage.created_at)).first()
    
    if last_message:
        membership.last_read_message_id = last_message.id
        membership.last_read_at = datetime.now()
        membership.unread_count = 0
        
        db.session.commit()
    
    return jsonify({'message': '所有消息已标记为已读'})


# ==================== 搜索 API ====================

@api_v1.route('/chat/search', methods=['GET'])
@api_login_required
def search_chat_messages():
    """全局搜索消息"""
    user_id = g.user.user_id
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({'error': '搜索关键词不能为空'}), 400
    
    # 获取用户参与的所有对话ID
    conversation_ids = [
        m.conversation_id for m in ConversationMember.query.filter_by(
            user_id=user_id,
            left_at=None
        ).all()
    ]
    
    # 搜索消息
    messages = IMMessage.query.filter(
        IMMessage.conversation_id.in_(conversation_ids),
        IMMessage.is_deleted == False,
        IMMessage.content.contains(keyword)
    ).order_by(desc(IMMessage.created_at)).limit(50).all()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'conversation_id': msg.conversation_id,
            'conversation_title': msg.conversation.title,
            'sender_name': msg.sender.real_name,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify(result)


# ==================== 个性化设置 API ====================

@api_v1.route('/chat/conversations/<int:conversation_id>/pin', methods=['POST'])
@api_login_required
def pin_chat_conversation(conversation_id):
    """置顶对话"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first_or_404()
    
    membership.is_pinned = True
    db.session.commit()
    
    return jsonify({'message': '已置顶'})


@api_v1.route('/chat/conversations/<int:conversation_id>/unpin', methods=['POST'])
@api_login_required
def unpin_chat_conversation(conversation_id):
    """取消置顶"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first_or_404()
    
    membership.is_pinned = False
    db.session.commit()
    
    return jsonify({'message': '已取消置顶'})


@api_v1.route('/chat/conversations/<int:conversation_id>/mute', methods=['POST'])
@api_login_required
def mute_chat_conversation(conversation_id):
    """静音对话"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first_or_404()
    
    membership.is_muted = True
    db.session.commit()
    
    return jsonify({'message': '已静音'})


@api_v1.route('/chat/conversations/<int:conversation_id>/unmute', methods=['POST'])
@api_login_required
def unmute_chat_conversation(conversation_id):
    """取消静音"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first_or_404()
    
    membership.is_muted = False
    db.session.commit()
    
    return jsonify({'message': '已取消静音'})


@api_v1.route('/chat/conversations/<int:conversation_id>/draft', methods=['POST'])
@api_login_required
def save_chat_draft(conversation_id):
    """保存草稿"""
    user_id = g.user.user_id
    data = request.get_json()
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first_or_404()
    
    membership.draft_content = data.get('content', '')
    membership.draft_updated_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': '草稿已保存'})


@api_v1.route('/chat/conversations/<int:conversation_id>/leave', methods=['POST'])
@api_login_required
def leave_conversation(conversation_id):
    """离开/删除对话"""
    user_id = g.user.user_id
    
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first_or_404()
    
    # 标记为已离开
    membership.left_at = datetime.now()
    
    # 如果是群组，创建系统消息
    conversation = Conversation.query.get(conversation_id)
    if conversation.conversation_type != 'private':
        system_msg = IMMessage(
            id=generate_next_id(IMMessage),
            conversation_id=conversation_id,
            sender_id=user_id,
            content=f'{g.user.real_name} 离开了对话',
            message_type='system'
        )
        db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '已离开对话'})

# ==================== 文件上传 API ====================

@api_v1.route('/chat/upload', methods=['POST'])
@api_login_required
def upload_chat_file():
    """上传聊天文件（图片/文件）"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    # 获取文件扩展名
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    # 确定上传目录
    upload_dir = os.path.join('uploads', 'chat')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    
    # 返回文件URL
    file_url = f"/uploads/chat/{unique_filename}"
    
    return jsonify({
        'url': file_url,
        'filename': filename,
        'size': os.path.getsize(filepath)
    }), 200


# ==================== 消息反应 API ====================

@api_v1.route('/chat/messages/<int:message_id>/reactions', methods=['POST'])
@api_login_required
def add_message_reaction(message_id):
    """添加消息反应（表情回应）"""
    user_id = g.user.user_id
    data = request.get_json()
    reaction = data.get('reaction', '👍')
    
    # 验证表情是否在支持列表中
    allowed_reactions = ['👍', '❤️', '😂', '😮', '😢', '🙏', '🔥', '👏']
    if reaction not in allowed_reactions:
        return jsonify({'error': '不支持的表情'}), 400
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 验证权限（是否是对话成员）
    membership = ConversationMember.query.filter_by(
        conversation_id=message.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 检查是否已经有反应
    existing_reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=user_id
    ).first()
    
    if existing_reaction:
        # 如果是相同的反应，则取消
        if existing_reaction.reaction == reaction:
            db.session.delete(existing_reaction)
            db.session.commit()
            return jsonify({'message': '已取消反应', 'action': 'removed'})
        else:
            # 更新为新的反应
            existing_reaction.reaction = reaction
            existing_reaction.created_at = datetime.now()
            db.session.commit()
            return jsonify({'message': '已更新反应', 'action': 'updated'})
    
    # 创建新反应
    new_reaction = MessageReaction(
        id=generate_next_id(MessageReaction),
        message_id=message_id,
        user_id=user_id,
        reaction=reaction
    )
    db.session.add(new_reaction)
    db.session.commit()
    
    return jsonify({'message': '已添加反应', 'action': 'added'}), 201


@api_v1.route('/chat/messages/<int:message_id>/reactions', methods=['GET'])
@api_login_required
def get_message_reactions(message_id):
    """获取消息的所有反应"""
    message = IMMessage.query.get_or_404(message_id)
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=message.conversation_id,
        user_id=g.user.user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 统计每种反应的数量和用户
    reactions = MessageReaction.query.filter_by(message_id=message_id).all()
    
    # 按反应类型分组
    reaction_summary = {}
    for r in reactions:
        if r.reaction not in reaction_summary:
            reaction_summary[r.reaction] = {
                'reaction': r.reaction,
                'count': 0,
                'users': []
            }
        reaction_summary[r.reaction]['count'] += 1
        reaction_summary[r.reaction]['users'].append({
            'user_id': r.user_id,
            'real_name': r.user.real_name
        })
    
    return jsonify(list(reaction_summary.values()))


@api_v1.route('/chat/messages/<int:message_id>/reactions/<int:user_id>', methods=['DELETE'])
@api_login_required
def remove_message_reaction(message_id, user_id):
    """移除消息反应（只能移除自己的）"""
    current_user_id = g.user.user_id
    
    # 只能删除自己的反应
    if current_user_id != user_id:
        return jsonify({'error': '无权删除他人的反应'}), 403
    
    reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=user_id
    ).first_or_404()
    
    db.session.delete(reaction)
    db.session.commit()
    
    return jsonify({'message': '已移除反应'})


# ==================== 消息置顶 API ====================

@api_v1.route('/chat/conversations/<int:conversation_id>/pinned_messages', methods=['GET'])
@api_login_required
def get_pinned_messages(conversation_id):
    """获取对话的置顶消息列表"""
    user_id = g.user.user_id
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 查询置顶消息
    pinned = PinnedMessage.query.filter_by(
        conversation_id=conversation_id
    ).order_by(PinnedMessage.order_index.desc()).all()
    
    result = []
    for p in pinned:
        msg = p.message
        result.append({
            'pin_id': p.id,
            'message_id': msg.id,
            'content': msg.content,
            'sender_name': msg.sender.real_name,
            'message_type': msg.message_type,
            'pinned_by': p.pinner.real_name,
            'pinned_at': p.pinned_at.isoformat(),
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify(result)


@api_v1.route('/chat/messages/<int:message_id>/pin', methods=['POST'])
@api_login_required
def pin_message(message_id):
    """置顶消息（需要管理员权限）"""
    user_id = g.user.user_id
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 验证权限（需要是owner或admin）
    membership = ConversationMember.query.filter_by(
        conversation_id=message.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership or membership.role not in ['owner', 'admin']:
        return jsonify({'error': '无权置顶消息，需要管理员权限'}), 403
    
    # 检查是否已置顶
    existing = PinnedMessage.query.filter_by(
        conversation_id=message.conversation_id,
        message_id=message_id
    ).first()
    
    if existing:
        return jsonify({'message': '消息已置顶'}), 200
    
    # 获取当前最大的 order_index
    max_order = db.session.query(func.max(PinnedMessage.order_index)).filter_by(
        conversation_id=message.conversation_id
    ).scalar() or 0
    
    # 创建置顶记录
    pinned = PinnedMessage(
        id=generate_next_id(PinnedMessage),
        conversation_id=message.conversation_id,
        message_id=message_id,
        pinned_by=user_id,
        order_index=max_order + 1
    )
    db.session.add(pinned)
    
    # 创建系统消息
    system_msg = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=message.conversation_id,
        sender_id=user_id,
        message_type='system',
        content=f'{g.user.real_name} 置顶了一条消息'
    )
    db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '已置顶消息'}), 201


@api_v1.route('/chat/pinned_messages/<int:pin_id>', methods=['DELETE'])
@api_login_required
def unpin_message(pin_id):
    """取消置顶消息"""
    user_id = g.user.user_id
    
    pinned = PinnedMessage.query.get_or_404(pin_id)
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=pinned.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership or membership.role not in ['owner', 'admin']:
        return jsonify({'error': '无权取消置顶，需要管理员权限'}), 403
    
    db.session.delete(pinned)
    
    # 创建系统消息
    system_msg = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=pinned.conversation_id,
        sender_id=user_id,
        message_type='system',
        content=f'{g.user.real_name} 取消了消息置顶'
    )
    db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '已取消置顶'})


# ==================== 消息转发 API ====================

@api_v1.route('/chat/messages/<int:message_id>/forward', methods=['POST'])
@api_login_required
def forward_message(message_id):
    """转发消息到其他对话"""
    user_id = g.user.user_id
    data = request.get_json()
    target_conversation_ids = data.get('conversation_ids', [])
    
    if not target_conversation_ids:
        return jsonify({'error': '请选择至少一个目标对话'}), 400
    
    # 获取原消息
    original_message = IMMessage.query.get_or_404(message_id)
    
    # 验证原消息访问权限
    source_membership = ConversationMember.query.filter_by(
        conversation_id=original_message.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not source_membership:
        return jsonify({'error': '无权访问原消息'}), 403
    
    forwarded_count = 0
    
    for target_id in target_conversation_ids:
        # 验证目标对话权限
        target_membership = ConversationMember.query.filter_by(
            conversation_id=target_id,
            user_id=user_id,
            left_at=None
        ).first()
        
        if not target_membership:
            continue  # 跳过无权限的对话
        
        # 创建转发消息
        forwarded_msg = IMMessage(
            id=generate_next_id(IMMessage),
            conversation_id=target_id,
            sender_id=user_id,
            message_type=original_message.message_type,
            content=original_message.content,
            media_url=original_message.media_url,
            file_name=original_message.file_name,
            file_size=original_message.file_size,
            mime_type=original_message.mime_type,
            forward_from_id=message_id,
            extra_data={
                'forwarded_from': {
                    'sender_name': original_message.sender.real_name,
                    'conversation_title': original_message.conversation.title,
                    'original_time': original_message.created_at.isoformat()
                }
            }
        )
        db.session.add(forwarded_msg)
        
        # 更新目标对话最后消息时间
        target_conv = Conversation.query.get(target_id)
        target_conv.last_message_at = datetime.now()
        target_conv.updated_at = datetime.now()
        
        # 更新其他成员的未读计数
        other_members = ConversationMember.query.filter(
            ConversationMember.conversation_id == target_id,
            ConversationMember.user_id != user_id,
            ConversationMember.left_at.is_(None)
        ).all()
        
        for member in other_members:
            member.unread_count += 1
        
        forwarded_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'已转发到 {forwarded_count} 个对话',
        'count': forwarded_count
    }), 201


# ==================== @ 提及功能 API ====================

@api_v1.route('/chat/conversations/<int:conversation_id>/members/search', methods=['GET'])
@api_login_required
def search_conversation_members(conversation_id):
    """搜索对话成员（用于 @ 提及）"""
    user_id = g.user.user_id
    keyword = request.args.get('q', '').strip()
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 查询成员
    query = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        left_at=None
    ).join(Users)
    
    if keyword:
        query = query.filter(
            or_(
                Users.real_name.contains(keyword),
                Users.username.contains(keyword)
            )
        )
    
    members = query.limit(10).all()
    
    result = []
    for m in members:
        result.append({
            'user_id': m.user_id,
            'username': m.user.username,
            'real_name': m.user.real_name,
            'role': m.role
        })
    
    return jsonify(result)


@api_v1.route('/chat/mentions', methods=['GET'])
@api_login_required
def get_my_mentions():
    """获取我的所有 @ 提及"""
    user_id = g.user.user_id
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = MentionNotification.query.filter_by(mentioned_user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    query = query.order_by(desc(MentionNotification.created_at))
    
    mentions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = []
    for m in mentions.items:
        msg = m.message
        result.append({
            'mention_id': m.id,
            'message_id': msg.id,
            'conversation_id': msg.conversation_id,
            'conversation_title': msg.conversation.title,
            'sender_name': msg.sender.real_name,
            'content': msg.content,
            'is_read': m.is_read,
            'created_at': m.created_at.isoformat()
        })
    
    return jsonify({
        'mentions': result,
        'total': mentions.total,
        'page': page,
        'per_page': per_page,
        'has_next': mentions.has_next
    })


@api_v1.route('/chat/mentions/<int:mention_id>/read', methods=['POST'])
@api_login_required
def mark_mention_read(mention_id):
    """标记提及为已读"""
    user_id = g.user.user_id
    
    mention = MentionNotification.query.get_or_404(mention_id)
    
    if mention.mentioned_user_id != user_id:
        return jsonify({'error': '无权操作'}), 403
    
    mention.is_read = True
    db.session.commit()
    
    return jsonify({'message': '已标记为已读'})


# ==================== 撤回消息改进 API ====================

@api_v1.route('/chat/messages/<int:message_id>/unsend', methods=['POST'])
@api_login_required
def unsend_message(message_id):
    """撤回消息（对所有人删除，有时间限制）"""
    user_id = g.user.user_id
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 只能撤回自己的消息
    if message.sender_id != user_id:
        return jsonify({'error': '无权撤回他人消息'}), 403
    
    # 检查时间限制（5分钟内）
    time_limit = timedelta(minutes=5)
    if datetime.now() - message.created_at > time_limit:
        return jsonify({'error': '超过撤回时间限制（5分钟）'}), 400
    
    # 标记为已删除
    message.is_deleted = True
    message.deleted_at = datetime.now()
    original_content = message.content
    message.content = '[此消息已撤回]'
    
    # 创建系统消息通知
    system_msg = IMMessage(
        id=generate_next_id(IMMessage),
        conversation_id=message.conversation_id,
        sender_id=user_id,
        message_type='system',
        content=f'{g.user.real_name} 撤回了一条消息',
        extra_data={'unsent_message_id': message_id}
    )
    db.session.add(system_msg)
    
    db.session.commit()
    
    return jsonify({'message': '已撤回消息'})


@api_v1.route('/chat/messages/<int:message_id>/delete_for_me', methods=['POST'])
@api_login_required
def delete_message_for_me(message_id):
    """仅对我删除消息"""
    user_id = g.user.user_id
    data = request.get_json() or {}
    
    message = IMMessage.query.get_or_404(message_id)
    
    # 验证权限
    membership = ConversationMember.query.filter_by(
        conversation_id=message.conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    
    if not membership:
        return jsonify({'error': '无权访问该对话'}), 403
    
    # 在 extra_data 中记录对该用户隐藏
    if not message.extra_data:
        message.extra_data = {}
    
    if 'hidden_for_users' not in message.extra_data:
        message.extra_data['hidden_for_users'] = []
    
    if user_id not in message.extra_data['hidden_for_users']:
        message.extra_data['hidden_for_users'].append(user_id)
    
    db.session.commit()
    
    return jsonify({'message': '已删除（仅对您可见）'})


# ==================== 链接预览 API ====================

@api_v1.route('/chat/link_preview', methods=['POST'])
@api_login_required
def get_link_preview():
    """获取网页链接预览"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL不能为空'}), 400
    
    # 验证URL格式
    url_pattern = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # 或IP
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return jsonify({'error': '无效的URL格式'}), 400
    
    # 获取预览信息
    preview = extract_link_preview(url)
    
    return jsonify(preview)