from flask import jsonify, request
from flask_login import login_required, current_user
from models import Message, Users, db, generate_next_id
from . import api_v1
from sqlalchemy import or_
from datetime import datetime

@api_v1.route('/messages', methods=['GET'])
@login_required
def get_messages():
    """获取所有消息 (收件箱)"""
    messages = Message.query.filter_by(recipient_id=current_user.user_id, is_deleted_by_recipient=False).order_by(Message.created_at.desc()).all()
    
    results = []
    for m in messages:
        results.append({
            'id': m.id,
            'sender_name': m.sender.real_name,
            'sender_id': m.sender_id,
            'content': m.content,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'is_read': m.read_at is not None
        })
    return jsonify(results)

@api_v1.route('/messages/sent', methods=['GET'])
@login_required
def get_sent_messages():
    """获取已发送消息"""
    messages = Message.query.filter_by(sender_id=current_user.user_id, is_deleted_by_sender=False).order_by(Message.created_at.desc()).all()
    
    results = []
    for m in messages:
        results.append({
            'id': m.id,
            'recipient_name': m.recipient.real_name,
            'recipient_id': m.recipient_id,
            'content': m.content,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'is_read': m.read_at is not None
        })
    return jsonify(results)

@api_v1.route('/messages', methods=['POST'])
@login_required
def send_message():
    """发送私信"""
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content:
        return jsonify({'error': 'Recipient and content are required'}), 400
        
    recipient = Users.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
        
    message = Message(
        id=generate_next_id(Message, 'id'),
        sender_id=current_user.user_id,
        recipient_id=recipient_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    return jsonify({'message': 'Message sent', 'id': message.id}), 201

@api_v1.route('/messages/<int:message_id>/read', methods=['PUT'])
@login_required
def mark_message_read(message_id):
    """标记消息为已读"""
    message = Message.query.get_or_404(message_id)
    if message.recipient_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not message.read_at:
        message.read_at = datetime.now()
        db.session.commit()
        
    return jsonify({'message': 'Marked as read'})
