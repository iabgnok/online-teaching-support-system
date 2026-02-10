from flask import jsonify, request, g
from . import api_v1
from .auth import api_login_required
from models import (
    db, Users, FriendRequest, Friendship, Conversation, ConversationMember, UserOnlineStatus,
    generate_next_id, create_friendship_and_private_conversation
)
from extensions import socketio
from datetime import datetime


@api_v1.route('/contacts', methods=['GET'])
@api_login_required
def get_contacts():
    user = g.user
    # 获取所有私聊对话
    private_conversations = Conversation.query.filter_by(conversation_type='private').all()
    
    contact_ids = set()
    for conv in private_conversations:
        member_ids = [m.user_id for m in conv.members]
        if int(user.user_id) in member_ids:
            # 添加另一个成员作为联系人
            for mid in member_ids:
                if mid != int(user.user_id):
                    contact_ids.add(mid)
    
    result = []
    for contact_id in contact_ids:
        u = Users.query.get(contact_id)
        if not u:
            continue
            
        online = None
        last_seen = None
        try:
            status = UserOnlineStatus.query.get(u.user_id)
            if status:
                online = bool(status.is_online)
                last_seen = status.last_seen.isoformat() if status.last_seen else None
        except Exception:
            online = None
            last_seen = None

        # 获取两个用户之间最近的一条私聊消息（作为预览）
        last_message_text = None
        last_message_at = None
        try:
            # 查找私聊 conversation 包含两位成员
            convs = Conversation.query.filter_by(conversation_type='private').all()
            for conv in convs:
                member_ids = [m.user_id for m in conv.members]
                if set(member_ids) == set([int(g.user.user_id), int(u.user_id)]):
                    msg = IMMessage.query.filter_by(conversation_id=conv.id).order_by(IMMessage.created_at.desc()).first()
                    if msg:
                        last_message_text = (msg.content or '')[:120]
                        last_message_at = msg.created_at.isoformat() if msg.created_at else None
                    break
        except Exception:
            pass

        # 读取联系人设置（别名/屏蔽）
        alias = None
        is_blocked = False
        try:
            cs = ContactSetting.query.filter_by(user_id=g.user.user_id, contact_id=u.user_id).first()
            if cs:
                alias = cs.alias
                is_blocked = bool(cs.is_blocked)
        except Exception:
            pass

        result.append({
            'id': u.user_id,
            'username': u.username,
            'real_name': u.real_name,
            'display_name': alias or u.real_name,
            'role': u.role,
            'avatar_url': u.avatar_url,
            'is_online': online,
            'last_seen': last_seen,
            'last_message': last_message_text,
            'last_message_at': last_message_at,
            'alias': alias,
            'is_blocked': is_blocked
        })
    return jsonify(result)


@api_v1.route('/contacts/<int:contact_id>/settings', methods=['GET'])
@api_login_required
def get_contact_setting(contact_id):
    user = g.user
    cs = ContactSetting.query.filter_by(user_id=user.user_id, contact_id=contact_id).first()
    if not cs:
        return jsonify({'alias': None, 'is_blocked': False})
    return jsonify({'alias': cs.alias, 'is_blocked': bool(cs.is_blocked)})


@api_v1.route('/contacts/<int:contact_id>/alias', methods=['PUT'])
@api_login_required
def set_alias(contact_id):
    user = g.user
    data = request.get_json() or {}
    alias = (data.get('alias') or '').strip()

    cs = ContactSetting.query.filter_by(user_id=user.user_id, contact_id=contact_id).first()
    if not cs:
        cs = ContactSetting(id=generate_next_id(ContactSetting), user_id=user.user_id, contact_id=contact_id)
        db.session.add(cs)

    cs.alias = alias or None
    db.session.commit()
    return jsonify({'message': 'Alias updated', 'alias': cs.alias})


@api_v1.route('/contacts/<int:contact_id>/block', methods=['POST'])
@api_login_required
def block_contact(contact_id):
    user = g.user
    cs = ContactSetting.query.filter_by(user_id=user.user_id, contact_id=contact_id).first()
    if not cs:
        cs = ContactSetting(id=generate_next_id(ContactSetting), user_id=user.user_id, contact_id=contact_id)
        db.session.add(cs)

    cs.is_blocked = True
    db.session.commit()
    return jsonify({'message': 'Contact blocked'})


@api_v1.route('/contacts/<int:contact_id>/unblock', methods=['POST'])
@api_login_required
def unblock_contact(contact_id):
    user = g.user
    cs = ContactSetting.query.filter_by(user_id=user.user_id, contact_id=contact_id).first()
    if cs:
        cs.is_blocked = False
        db.session.commit()
    return jsonify({'message': 'Contact unblocked'})

@api_v1.route('/contacts/requests', methods=['GET'])
@api_login_required
def get_requests():
    user = g.user
    incoming = FriendRequest.query.filter_by(target_id=user.user_id).order_by(FriendRequest.created_at.desc()).all()
    outgoing = FriendRequest.query.filter_by(requester_id=user.user_id).order_by(FriendRequest.created_at.desc()).all()

    def map_req(r):
        return {
            'id': r.id,
            'requester_id': r.requester_id,
            'target_id': r.target_id,
            'status': r.status,
            'message': r.message,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'responded_at': r.responded_at.isoformat() if r.responded_at else None
        }

    return jsonify({
        'incoming': [map_req(r) for r in incoming if r.status == 'pending'],
        'outgoing': [map_req(r) for r in outgoing if r.status == 'pending']
    })


@api_v1.route('/contacts/requests', methods=['POST'])
@api_login_required
def send_friend_request():
    data = request.get_json() or {}
    target_id = data.get('target_id')
    message = (data.get('message') or '').strip()

    if not target_id:
        return jsonify({'error': 'target_id required'}), 400

    if int(target_id) == int(g.user.user_id):
        return jsonify({'error': "不能添加自己为好友"}), 400

    # Already friends?
    if Friendship.query.filter_by(user_id=g.user.user_id, friend_id=target_id).first():
        return jsonify({'error': 'Already friends'}), 400

    # Existing pending request
    exist = FriendRequest.query.filter_by(requester_id=g.user.user_id, target_id=target_id, status='pending').first()
    if exist:
        return jsonify({'error': 'Request already pending'}), 400

    fr = FriendRequest(id=generate_next_id(FriendRequest), requester_id=g.user.user_id, target_id=target_id, message=message)
    db.session.add(fr)
    db.session.commit()

    # Notify target if online
    online = UserOnlineStatus.query.get(target_id)
    payload = {
        'id': fr.id,
        'from': g.user.user_id,
        'from_name': g.user.real_name,
        'message': fr.message
    }
    try:
        if online and online.socket_id:
            socketio.emit('contacts:request', payload, room=online.socket_id)
    except Exception:
        pass

    return jsonify({'message': 'Request sent', 'request_id': fr.id}), 201


@api_v1.route('/contacts/requests/<int:request_id>/accept', methods=['POST'])
@api_login_required
def accept_request(request_id):
    fr = FriendRequest.query.get(request_id)
    if not fr:
        return jsonify({'error': 'Request not found'}), 404
    if int(fr.target_id) != int(g.user.user_id):
        return jsonify({'error': 'Not authorized to accept'}), 403
    if fr.status != 'pending':
        return jsonify({'error': 'Request not pending'}), 400

    fr.status = 'accepted'
    fr.responded_at = datetime.now()

    # create friendship and private conversation
    conv = None
    try:
        conv = create_friendship_and_private_conversation(fr.requester_id, fr.target_id)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    db.session.add(fr)
    db.session.commit()

    # Notify requester
    online = UserOnlineStatus.query.get(fr.requester_id)
    payload = {
        'request_id': fr.id,
        'accepted_by': fr.target_id,
        'conversation_id': conv.id if conv else None
    }
    try:
        if online and online.socket_id:
            socketio.emit('contacts:request_accepted', payload, room=online.socket_id)
    except Exception:
        pass

    return jsonify({'message': 'Accepted', 'conversation_id': conv.id if conv else None})


@api_v1.route('/contacts/requests/<int:request_id>/decline', methods=['POST'])
@api_login_required
def decline_request(request_id):
    fr = FriendRequest.query.get(request_id)
    if not fr:
        return jsonify({'error': 'Request not found'}), 404
    if int(fr.target_id) != int(g.user.user_id):
        return jsonify({'error': 'Not authorized to decline'}), 403
    if fr.status != 'pending':
        return jsonify({'error': 'Request not pending'}), 400

    fr.status = 'declined'
    fr.responded_at = datetime.now()
    db.session.add(fr)
    db.session.commit()

    # Optionally notify requester
    online = UserOnlineStatus.query.get(fr.requester_id)
    payload = {'request_id': fr.id, 'declined_by': fr.target_id}
    try:
        if online and online.socket_id:
            socketio.emit('contacts:request_declined', payload, room=online.socket_id)
    except Exception:
        pass

    return jsonify({'message': 'Declined'})


@api_v1.route('/contacts/<int:contact_id>', methods=['DELETE'])
@api_login_required
def remove_contact(contact_id):
    user = g.user
    # delete both directions
    Friendship.query.filter_by(user_id=user.user_id, friend_id=contact_id).delete()
    Friendship.query.filter_by(user_id=contact_id, friend_id=user.user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Removed'})


@api_v1.route('/contacts/private-conversation', methods=['POST'])
@api_login_required
def get_or_create_private_conversation():
    """创建或获取两人之间的私聊会话（不自动建立好友关系）"""
    data = request.get_json() or {}
    target_id = data.get('target_id')

    if not target_id:
        return jsonify({'error': 'target_id required'}), 400

    if int(target_id) == int(g.user.user_id):
        return jsonify({'error': 'cannot create private conversation with self'}), 400

    try:
        # 查找已有的私聊会话
        for conv in Conversation.query.filter_by(conversation_type='private').all():
            member_ids = [m.user_id for m in conv.members]
            if set(member_ids) == set([int(g.user.user_id), int(target_id)]):
                return jsonify({'conversation_id': conv.id})

        # 创建新的私聊会话
        conv = Conversation(id=generate_next_id(Conversation), conversation_type='private', created_by=g.user.user_id)
        db.session.add(conv)
        db.session.flush()

        m1 = ConversationMember(id=generate_next_id(ConversationMember), conversation_id=conv.id, user_id=g.user.user_id, role='member')
        m2 = ConversationMember(id=generate_next_id(ConversationMember), conversation_id=conv.id, user_id=target_id, role='member')
        db.session.add_all([m1, m2])

        db.session.commit()

        return jsonify({'conversation_id': conv.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
