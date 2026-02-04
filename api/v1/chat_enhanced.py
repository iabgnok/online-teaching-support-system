"""
聊天增强功能API - 实现Telegram和钉钉风格的新功能
包括：消息已读状态、分组、表情回复、举手、快捷指令等
"""

from flask import Blueprint, request, jsonify, g
from models import (
    db, MessageStatus, MessageReaction, PinnedMessage, ConversationFolder,
    ConversationFolderItem, RaiseHandRecord, QuickCommand, MessageAttachment,
    IMMessage, Conversation, ConversationMember, LiveClass, Users
)
from api.v1.auth import api_login_required
from datetime import datetime
import json

api_enhanced = Blueprint('chat_enhanced', __name__)


# ==================== 消息已读状态 ====================

@api_enhanced.route('/messages/<int:message_id>/status', methods=['GET'])
@api_login_required
def get_message_status(message_id):
    """获取消息的已读/未读状态列表（显示n人已读/未读）"""
    message = IMMessage.query.get_or_404(message_id)
    conversation = message.conversation
    
    # 检查权限：只有对话成员可以查看
    member = ConversationMember.query.filter_by(
        conversation_id=conversation.id,
        user_id=g.user.user_id
    ).first()
    
    if not member and g.user.role not in ['admin', 'teacher']:
        return jsonify({'code': 403, 'message': '无权查看此消息状态'}), 403
    
    # 获取所有成员的状态
    all_members = ConversationMember.query.filter_by(conversation_id=conversation.id).all()
    
    read_users = []
    unread_users = []
    
    for member in all_members:
        if member.user_id == message.sender_id:
            continue  # 跳过发送者
            
        status = MessageStatus.query.filter_by(
            message_id=message_id,
            user_id=member.user_id
        ).first()
        
        user_info = {
            'user_id': member.user_id,
            'real_name': member.user.real_name,
            'role': member.user.role
        }
        
        if status and status.status == 'read':
            user_info['read_at'] = status.timestamp.isoformat()
            read_users.append(user_info)
        else:
            unread_users.append(user_info)
    
    return jsonify({
        'code': 200,
        'data': {
            'message_id': message_id,
            'read_count': len(read_users),
            'unread_count': len(unread_users),
            'read_users': read_users,
            'unread_users': unread_users
        }
    })


@api_enhanced.route('/messages/<int:message_id>/mark_read', methods=['POST'])
@api_login_required
def mark_message_read(message_id):
    """标记消息为已读"""
    message = IMMessage.query.get_or_404(message_id)
    user_id = g.user.user_id
    
    # 查找或创建状态记录
    status = MessageStatus.query.filter_by(
        message_id=message_id,
        user_id=user_id
    ).first()
    
    if not status:
        from models import generate_next_id
        status = MessageStatus(
            id=generate_next_id(MessageStatus),
            message_id=message_id,
            user_id=user_id,
            status='read',
            timestamp=datetime.utcnow()
        )
        db.session.add(status)
    else:
        status.status = 'read'
        status.timestamp = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '已标记为已读'})


# ==================== 表情回复 ====================

@api_enhanced.route('/messages/<int:message_id>/reactions', methods=['GET'])
@api_login_required
def get_message_reactions(message_id):
    """获取消息的所有表情回复"""
    reactions = MessageReaction.query.filter_by(message_id=message_id).all()
    
    # 按表情分组统计
    reaction_summary = {}
    for r in reactions:
        if r.reaction not in reaction_summary:
            reaction_summary[r.reaction] = {
                'emoji': r.reaction,
                'count': 0,
                'users': []
            }
        reaction_summary[r.reaction]['count'] += 1
        reaction_summary[r.reaction]['users'].append({
            'user_id': r.user_id,
            'real_name': r.user.real_name
        })
    
    return jsonify({
        'code': 200,
        'data': {
            'message_id': message_id,
            'reactions': list(reaction_summary.values())
        }
    })


@api_enhanced.route('/messages/<int:message_id>/reactions', methods=['POST'])
@api_login_required
def add_message_reaction(message_id):
    """添加表情回复"""
    try:
        data = request.get_json()
        print(f"[DEBUG] Reaction request data: {data}")
        
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        reaction = data.get('reaction', '').strip()
        print(f"[DEBUG] Extracted reaction: {reaction}, type: {type(reaction)}")
        
        if not reaction:
            return jsonify({'code': 400, 'message': '表情不能为空'}), 400
        
        # 支持的表情列表（扩展列表，支持更多表情）
        allowed_reactions = ['👍', '❤️', '😂', '😮', '😢', '🙏', '👏', '🔥']
        
        # 如果表情不在列表中，仍然接受（放宽限制）
        if reaction not in allowed_reactions:
            print(f"[WARNING] Reaction {reaction} not in allowed list, but accepting it")
        
        user_id = g.user.user_id
        
        # 检查是否已经有反应
        existing = MessageReaction.query.filter_by(
            message_id=message_id,
            user_id=user_id
        ).first()
        
        if existing:
            # 如果是同一个表情，删除（取消）
            if existing.reaction == reaction:
                db.session.delete(existing)
                db.session.commit()
                return jsonify({'code': 200, 'message': '已取消表情', 'action': 'removed'})
            else:
                # 更换表情
                existing.reaction = reaction
                existing.created_at = datetime.utcnow()
        else:
            # 创建新反应
            from models import generate_next_id
            new_reaction = MessageReaction(
                id=generate_next_id(MessageReaction),
                message_id=message_id,
                user_id=user_id,
                reaction=reaction
            )
            db.session.add(new_reaction)
        
        db.session.commit()
        
        return jsonify({'code': 200, 'message': '表情添加成功', 'action': 'added'})
    
    except Exception as e:
        print(f"[ERROR] Exception in add_message_reaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


# ==================== 置顶消息 ====================

@api_enhanced.route('/conversations/<int:conversation_id>/pinned', methods=['GET'])
@api_login_required
def get_pinned_messages(conversation_id):
    """获取对话的置顶消息列表"""
    pinned = PinnedMessage.query.filter_by(
        conversation_id=conversation_id
    ).order_by(PinnedMessage.order_index).all()
    
    result = []
    for p in pinned:
        message_data = None
        if p.message:
            message_data = {
                'id': p.message.id,
                'content': p.message.content,
                'sender_id': p.message.sender_id,
                'sender_name': p.message.sender.real_name if p.message.sender else 'Unknown',
                'created_at': p.message.created_at.isoformat() if p.message.created_at else None
            }
        
        result.append({
            'pin_id': p.id,
            'message_id': p.message_id,
            'message': message_data,
            'pinned_by': p.pinner.real_name if p.pinner else 'Unknown',
            'pinned_at': p.pinned_at.isoformat(),
            'order': p.order_index
        })
    
    return jsonify({'code': 200, 'data': result})


@api_enhanced.route('/conversations/<int:conversation_id>/pin/<int:message_id>', methods=['POST'])
@api_login_required
def pin_message(conversation_id, message_id):
    """置顶消息"""
    # 检查权限：只有老师或管理员可以置顶
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以置顶消息'}), 403
    
    # 检查消息是否存在
    message = IMMessage.query.filter_by(
        id=message_id,
        conversation_id=conversation_id
    ).first_or_404()
    
    # 检查是否已置顶
    existing = PinnedMessage.query.filter_by(
        conversation_id=conversation_id,
        message_id=message_id
    ).first()
    
    if existing:
        return jsonify({'code': 400, 'message': '消息已经置顶'}), 400
    
    # 获取当前最大排序
    max_order = db.session.query(db.func.max(PinnedMessage.order_index)).filter_by(
        conversation_id=conversation_id
    ).scalar() or 0
    
    from models import generate_next_id
    pinned = PinnedMessage(
        id=generate_next_id(PinnedMessage),
        conversation_id=conversation_id,
        message_id=message_id,
        pinned_by=g.user.user_id,
        order_index=max_order + 1
    )
    
    db.session.add(pinned)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '消息已置顶'})


@api_enhanced.route('/conversations/<int:conversation_id>/unpin/<int:message_id>', methods=['POST'])
@api_login_required
def unpin_message(conversation_id, message_id):
    """取消置顶"""
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以取消置顶'}), 403
    
    pinned = PinnedMessage.query.filter_by(
        conversation_id=conversation_id,
        message_id=message_id
    ).first_or_404()
    
    db.session.delete(pinned)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '已取消置顶'})


# ==================== 对话分组 ====================

@api_enhanced.route('/folders', methods=['GET'])
@api_login_required
def get_conversation_folders():
    """获取用户的对话分组列表"""
    folders = ConversationFolder.query.filter_by(
        user_id=g.user.user_id
    ).order_by(ConversationFolder.order_index).all()
    
    result = []
    for folder in folders:
        result.append({
            'id': folder.id,
            'name': folder.name,
            'icon': folder.icon,
            'color': folder.color,
            'is_system': folder.is_system,
            'conversation_count': len(folder.items)
        })
    
    return jsonify({'code': 200, 'data': result})


@api_enhanced.route('/folders', methods=['POST'])
@api_login_required
def create_folder():
    """创建对话分组"""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'code': 400, 'message': '分组名称不能为空'}), 400
    
    from models import generate_next_id
    folder = ConversationFolder(
        id=generate_next_id(ConversationFolder),
        user_id=g.user.user_id,
        name=name,
        icon=data.get('icon', '📁'),
        color=data.get('color', '#409EFF'),
        order_index=data.get('order', 0)
    )
    
    db.session.add(folder)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '分组创建成功', 'data': {'id': folder.id}})


@api_enhanced.route('/folders/<int:folder_id>/conversations', methods=['POST'])
@api_login_required
def add_conversation_to_folder(folder_id):
    """将对话添加到分组"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'code': 400, 'message': '对话ID不能为空'}), 400
    
    # 检查分组是否属于当前用户
    folder = ConversationFolder.query.filter_by(
        id=folder_id,
        user_id=g.user.user_id
    ).first_or_404()
    
    # 检查是否已经在分组中
    existing = ConversationFolderItem.query.filter_by(
        folder_id=folder_id,
        conversation_id=conversation_id
    ).first()
    
    if existing:
        return jsonify({'code': 400, 'message': '对话已在此分组中'}), 400
    
    from models import generate_next_id
    item = ConversationFolderItem(
        id=generate_next_id(ConversationFolderItem),
        folder_id=folder_id,
        conversation_id=conversation_id
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '已添加到分组'})


# ==================== 举手功能 ====================

@api_enhanced.route('/live/<int:live_class_id>/raise_hand', methods=['POST'])
@api_login_required
def raise_hand(live_class_id):
    """学生举手"""
    live_class = LiveClass.query.get_or_404(live_class_id)
    
    if live_class.status != 'active':
        return jsonify({'code': 400, 'message': '课堂未进行中'}), 400
    
    # 检查是否已经举手
    existing = RaiseHandRecord.query.filter_by(
        live_class_id=live_class_id,
        user_id=g.user.user_id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'code': 400, 'message': '您已经举手了，请等待老师回应'}), 400
    
    data = request.get_json() or {}
    from models import generate_next_id
    record = RaiseHandRecord(
        id=generate_next_id(RaiseHandRecord),
        live_class_id=live_class_id,
        user_id=g.user.user_id,
        question=data.get('question', '').strip()
    )
    
    db.session.add(record)
    db.session.commit()
    
    # TODO: 通过 SocketIO 通知老师
    
    return jsonify({'code': 200, 'message': '举手成功', 'data': {'id': record.id}})


@api_enhanced.route('/live/<int:live_class_id>/raise_hands', methods=['GET'])
@api_login_required
def get_raise_hands(live_class_id):
    """获取举手列表（老师查看）"""
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以查看'}), 403
    
    hands = RaiseHandRecord.query.filter_by(
        live_class_id=live_class_id,
        status='pending'
    ).order_by(RaiseHandRecord.raised_at).all()
    
    result = []
    for hand in hands:
        result.append({
            'id': hand.id,
            'user_id': hand.user_id,
            'student_name': hand.user.real_name,
            'question': hand.question,
            'raised_at': hand.raised_at.isoformat(),
            'waiting_time': (datetime.utcnow() - hand.raised_at).seconds
        })
    
    return jsonify({'code': 200, 'data': result})


@api_enhanced.route('/live/<int:live_class_id>/raise_hands/<int:hand_id>/handle', methods=['POST'])
@api_login_required
def handle_raise_hand(live_class_id, hand_id):
    """老师处理举手"""
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以处理'}), 403
    
    hand = RaiseHandRecord.query.filter_by(
        id=hand_id,
        live_class_id=live_class_id
    ).first_or_404()
    
    hand.status = 'handled'
    hand.handled_at = datetime.utcnow()
    hand.handled_by = g.user.user_id
    
    db.session.commit()
    
    # TODO: 通过 SocketIO 通知学生
    
    return jsonify({'code': 200, 'message': '已处理'})


# ==================== 快捷指令 ====================

@api_enhanced.route('/live/<int:live_class_id>/commands/attendance', methods=['POST'])
@api_login_required
def create_attendance_command(live_class_id):
    """创建签到指令 /call"""
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以发起签到'}), 403
    
    live_class = LiveClass.query.get_or_404(live_class_id)
    
    if live_class.status != 'active':
        return jsonify({'code': 400, 'message': '课堂未进行中'}), 400
    
    data = request.get_json() or {}
    config = {
        'duration': data.get('duration', 300),  # 默认5分钟
        'title': data.get('title', '课堂签到')
    }
    
    from models import generate_next_id
    command = QuickCommand(
        id=generate_next_id(QuickCommand),
        live_class_id=live_class_id,
        teacher_id=g.user.user_id,
        command_type='attendance',
        title=config['title'],
        config=json.dumps(config)
    )
    
    db.session.add(command)
    db.session.commit()
    
    # TODO: 通过 SocketIO 广播签到消息
    
    return jsonify({
        'code': 200,
        'message': '签到已发起',
        'data': {
            'command_id': command.id,
            'duration': config['duration']
        }
    })


@api_enhanced.route('/live/<int:live_class_id>/commands/quiz', methods=['POST'])
@api_login_required
def create_quiz_command(live_class_id):
    """创建随堂测试指令 /quiz"""
    if g.user.role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '只有教师可以发起测试'}), 403
    
    live_class = LiveClass.query.get_or_404(live_class_id)
    
    if live_class.status != 'active':
        return jsonify({'code': 400, 'message': '课堂未进行中'}), 400
    
    data = request.get_json() or {}
    config = {
        'question': data.get('question', ''),
        'options': data.get('options', []),
        'correct_answer': data.get('correct_answer'),
        'duration': data.get('duration', 60)
    }
    
    if not config['question']:
        return jsonify({'code': 400, 'message': '问题不能为空'}), 400
    
    from models import generate_next_id
    command = QuickCommand(
        id=generate_next_id(QuickCommand),
        live_class_id=live_class_id,
        teacher_id=g.user.user_id,
        command_type='quiz',
        title='随堂测试',
        config=json.dumps(config)
    )
    
    db.session.add(command)
    db.session.commit()
    
    # TODO: 通过 SocketIO 广播测试消息
    
    return jsonify({
        'code': 200,
        'message': '测试已发起',
        'data': {'command_id': command.id}
    })


# ==================== 消息附件筛选 ====================

@api_enhanced.route('/conversations/<int:conversation_id>/attachments', methods=['GET'])
@api_login_required
def get_conversation_attachments(conversation_id):
    """获取对话中的附件列表（支持按类型筛选）"""
    try:
        attachment_type = request.args.get('type')  # 'image', 'document', 'link'
        
        # 获取对话中的所有消息ID
        messages = IMMessage.query.filter_by(conversation_id=conversation_id).all()
        message_ids = [m.id for m in messages]
        
        if not message_ids:
            return jsonify({'code': 200, 'data': []})
        
        query = MessageAttachment.query.filter(
            MessageAttachment.message_id.in_(message_ids)
        )
        
        if attachment_type:
            query = query.filter_by(attachment_type=attachment_type)
        
        attachments = query.order_by(MessageAttachment.created_at.desc()).limit(100).all()
        
        result = []
        for att in attachments:
            sender_name = 'Unknown'
            if att.message and att.message.sender:
                sender_name = att.message.sender.real_name
                
            result.append({
                'id': att.id,
                'message_id': att.message_id,
                'type': att.attachment_type,
                'file_name': att.file_name,
                'file_url': att.file_url,
                'file_size': att.file_size,
                'thumbnail_url': att.thumbnail_url,
                'created_at': att.created_at.isoformat() if att.created_at else None,
                'sender': sender_name
            })
        
        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
