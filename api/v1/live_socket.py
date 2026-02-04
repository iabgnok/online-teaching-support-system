from flask_socketio import emit, join_room, leave_room
from flask import request
from models import (
    db, LiveClass, ChatMessage, DrawingData, LiveParticipant, Users, generate_next_id, 
    Attendance, AttendanceRecord, Conversation, ConversationMember, IMMessage, 
    MessageStatus, UserOnlineStatus
)
from datetime import datetime, date, timedelta
import json

def register_socket_events(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        # print(f"Client connected: {request.sid}")
        pass

    @socketio.on('join_class')
    def handle_join_class(data):
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        
        if not lesson_id or not user_id:
            return
            
        join_room(lesson_id)
        print(f"User {user_id} ({user_name}) joining class {lesson_id}")
        
        # Update database participant status
        try:
            live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
            if live_class:
                # Check if class is ended
                if live_class.status == 'ended':
                    emit('class_ended', {'message': 'Class has ended'}, room=request.sid)
                    return

                participant = LiveParticipant.query.filter_by(
                    live_class_id=live_class.id,
                    user_id=user_id
                ).first()
                
                if not participant:
                    participant = LiveParticipant(
                        id=generate_next_id(LiveParticipant),
                        live_class_id=live_class.id,
                        user_id=user_id,
                        role='teacher' if str(user_id) == str(live_class.teacher_id) else 'student',
                        joined_at=datetime.now()
                    )
                    db.session.add(participant)
                else:
                    participant.left_at = None # rejoined
                    participant.joined_at = datetime.now()
                    # Update role just in case
                    participant.role = 'teacher' if str(user_id) == str(live_class.teacher_id) else 'student'
                
                db.session.commit() # Commit first to ensure participant is saved

                # Update participant count
                count = LiveParticipant.query.filter_by(
                    live_class_id=live_class.id, 
                    left_at=None
                ).count()
                live_class.participants_count = count
                
                db.session.commit()
                
                emit('joined_class', {'lesson_id': lesson_id}, room=request.sid)
                emit('user_joined', {
                    'user_id': user_id,
                    'user_name': user_name,
                    'role': participant.role,
                    'timestamp': datetime.now().isoformat()
                }, room=lesson_id)
        except Exception as e:
            print(f"Error in join_class: {e}")
            db.session.rollback()

    @socketio.on('leave_class')
    def handle_leave_class(data):
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        
        leave_room(lesson_id)
        print(f"User {user_id} leaving class {lesson_id}")
        
        try:
            live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
            if live_class:
                participant = LiveParticipant.query.filter_by(
                    live_class_id=live_class.id,
                    user_id=user_id
                ).first()
                if participant:
                    participant.left_at = datetime.now()
                    db.session.commit()

                    # Update count
                    count = LiveParticipant.query.filter_by(
                        live_class_id=live_class.id,
                        left_at=None
                    ).count()
                    live_class.participants_count = count
                    
                    db.session.commit()
                
                emit('user_left', {
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }, room=lesson_id)
        except Exception as e:
            print(f"Error in leave_class: {e}")
            db.session.rollback()

    @socketio.on('chat_message')
    def handle_chat_message(data):
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        message = data.get('message')
        user_name = data.get('user_name')
        msg_type = data.get('message_type', 'text')
        
        # 保持实时性：立即广播，然后异步保存
        timestamp = datetime.now()
        
        # 只使用统一聊天系统（IMMessage）- 数据单一来源
        try:
            live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
            if live_class:
                # 获取对应的聊天对话
                conversation = Conversation.query.filter_by(live_class_id=live_class.id).first()
                
                if conversation:
                    # 保存消息到统一系统
                    im_message = IMMessage(
                        id=generate_next_id(IMMessage),
                        conversation_id=conversation.id,
                        sender_id=user_id,
                        content=message,
                        message_type=msg_type,
                        created_at=timestamp,
                        updated_at=timestamp,
                        is_deleted=False
                    )
                    db.session.add(im_message)
                    
                    # 更新对话最后消息时间
                    conversation.last_message_at = timestamp
                    conversation.updated_at = timestamp
                    
                    # 更新未读数（除发送者外）
                    members = ConversationMember.query.filter(
                        ConversationMember.conversation_id == conversation.id,
                        ConversationMember.user_id != user_id
                    ).all()
                    
                    for member in members:
                        member.unread_count = (member.unread_count or 0) + 1
                    
                    db.session.commit()
                else:
                    print(f"Warning: No conversation found for live_class {live_class.id}")
        except Exception as e:
            print(f"Error saving chat message: {e}")
            db.session.rollback()
        
        # 实时广播消息（Socket.IO机制完全不变，保证实时性）
        emit('new_message', {
            'user_id': user_id,
            'user_name': user_name,
            'message': message,
            'message_type': msg_type,
            'timestamp': timestamp.isoformat()
        }, room=lesson_id)

    @socketio.on('drawing')
    def handle_drawing(data):
        lesson_id = data.get('lesson_id')
        # Relay to others
        emit('drawing_update', data, room=lesson_id, include_self=False)
        
        # Optional: Save to DB (simplified, maybe async or batched in real prod)
        # Here we just save it for "Notes" generation later
        try:
            live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
            if live_class:
                drawing = DrawingData(
                    id=generate_next_id(DrawingData),
                    live_class_id=live_class.id,
                    user_id=data.get('user_id'),
                    x_percent=data.get('x', 0),
                    y_percent=data.get('y', 0),
                    color=data.get('color', '#000000'),
                    brush_size=data.get('brush_size', 2),
                    action=data.get('action', 'draw')
                )
                db.session.add(drawing)
                # Avoid frequent commits? 
                # For now commit every time for simplicity, though not efficient
                db.session.commit()
        except Exception as e:
            # print(f"Error saving drawing: {e}")
            pass

    @socketio.on('webrtc_offer')
    def handle_webrtc_offer(data):
        lesson_id = data.get('lesson_id')
        emit('webrtc_offer', data, room=lesson_id, include_self=False)

    @socketio.on('webrtc_answer')
    def handle_webrtc_answer(data):
        lesson_id = data.get('lesson_id')
        emit('webrtc_answer', data, room=lesson_id, include_self=False)

    @socketio.on('webrtc_ice_candidate')
    def handle_webrtc_ice_candidate(data):
        lesson_id = data.get('lesson_id')
        emit('webrtc_ice_candidate', data, room=lesson_id, include_self=False)

    @socketio.on('stop_screen_share')
    def handle_stop_screen_share(data):
        lesson_id = data.get('lesson_id')
        emit('screen_share_stopped', data, room=lesson_id, include_self=False)
        
    @socketio.on('set_background_image')
    def handle_set_background_image(data):
        lesson_id = data.get('lesson_id')
        # data should contain 'imageUrl'
        emit('background_image_update', data, room=lesson_id)

    @socketio.on('start_attendance')
    def handle_start_attendance(data):
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        title = data.get('title', f"考勤打卡 {datetime.now().strftime('%H:%M')}")
        duration = data.get('duration', 5)
        
        live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
        if not live_class or str(live_class.teacher_id) != str(user_id):
            return

        # Create Attendance Record
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=int(duration))
            
            att = Attendance(
                id=generate_next_id(Attendance),
                class_id=live_class.class_id,
                date=date.today(),
                is_self_checkin=True,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(att)
            db.session.commit()
            
            # Send Chat Message
            msg_content = json.dumps({
                "attendance_id": att.id,
                "title": title,
                "count": 0,
                "total": 0 # TODO: Get total students
            })
            
            chat_msg = ChatMessage(
                id=generate_next_id(ChatMessage),
                live_class_id=live_class.id,
                user_id=user_id,
                message=msg_content,
                message_type='attendance',
                timestamp=datetime.now()
            )
            db.session.add(chat_msg)
            db.session.commit()
            
            emit('new_message', {
                'id': chat_msg.id,
                'user_id': chat_msg.user_id,
                'user_name': 'Teacher', # Or resolve name
                'message': chat_msg.message,
                'message_type': 'attendance',
                'timestamp': chat_msg.timestamp.isoformat()
            }, room=lesson_id)
            
        except Exception as e:
            print(f"Error starting attendance: {e}")
            db.session.rollback()

    @socketio.on('submit_attendance')
    def handle_submit_attendance(data):
        attendance_id = data.get('attendance_id')
        user_id = data.get('user_id')
        lesson_id = data.get('lesson_id')
        
        # Check if already submitted
        existing = AttendanceRecord.query.filter_by(attendance_id=attendance_id, student_id=user_id).first()
        if existing:
            return # Already done
            
        try:
            record = AttendanceRecord(
                id=generate_next_id(AttendanceRecord),
                attendance_id=attendance_id,
                student_id=user_id,
                status='present',
                remarks='Live Check-in'
            )
            db.session.add(record)
            db.session.commit()
            
            # Count updates
            count = AttendanceRecord.query.filter_by(attendance_id=attendance_id, status='present').count()
            
            # Broadcast update
            emit('attendance_update', {
                'attendance_id': attendance_id,
                'count': count
            }, room=lesson_id)
            
        except Exception as e:
            print(f"Error submitting attendance: {e}")
            db.session.rollback()

    @socketio.on('publish_task')
    def handle_publish_task(data):
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        content = data.get('content') # Task description
        
        live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
        if not live_class: return
        
        try:
            msg_content = json.dumps({
                "desc": content,
                "completed_ids": []
            })
            
            chat_msg = ChatMessage(
                id=generate_next_id(ChatMessage),
                live_class_id=live_class.id,
                user_id=user_id,
                message=msg_content,
                message_type='task',
                timestamp=datetime.now()
            )
            db.session.add(chat_msg)
            db.session.commit()
            
            emit('new_message', {
                'id': chat_msg.id,
                'user_id': chat_msg.user_id,
                'user_name': 'Teacher',
                'message': chat_msg.message,
                'message_type': 'task',
                'timestamp': chat_msg.timestamp.isoformat()
            }, room=lesson_id)
        except Exception as e:
            print(f"Error publishing task: {e}")
            db.session.rollback()

    @socketio.on('complete_task')
    def handle_complete_task(data):
        message_id = data.get('message_id')
        user_id = data.get('user_id')
        lesson_id = data.get('lesson_id')
        
        try:
            chat_msg = ChatMessage.query.get(message_id)
            if not chat_msg: return
            
            content_data = json.loads(chat_msg.message)
            completed_ids = content_data.get('completed_ids', [])
            
            # We store IDs as strings to be safe with json
            str_id = str(user_id)
            if str_id not in map(str, completed_ids):
                completed_ids.append(str_id)
                content_data['completed_ids'] = completed_ids
                chat_msg.message = json.dumps(content_data)
                db.session.commit()
                
                emit('task_update', {
                    'message_id': message_id,
                    'completed_count': len(completed_ids),
                    'completed_ids': completed_ids
                }, room=lesson_id)
                
        except Exception as e:
            print(f"Error completing task: {e}")
            db.session.rollback()

    @socketio.on('delete_message')
    def handle_delete_message(data):
        try:
            message_id = data.get('message_id')
            user_id = data.get('user_id')
            lesson_id = data.get('lesson_id')
            
            msg = ChatMessage.query.get(message_id)
            if not msg:
                return

            # Permission check
            live_class = LiveClass.query.get(msg.live_class_id)
            is_teacher = str(live_class.teacher_id) == str(user_id)
            is_author = str(msg.user_id) == str(user_id)

            if not (is_teacher or is_author):
                return # Unauthorized
            
            if msg.message_type == 'attendance':
                try:
                    content = json.loads(msg.message)
                    att_id = content.get('attendance_id')
                    if att_id:
                        att = Attendance.query.get(att_id)
                        if att:
                            att.close_time = datetime.now() 
                            db.session.add(att)
                except:
                    pass

            db.session.delete(msg)
            db.session.commit()
            
            emit('message_deleted', {'message_id': message_id}, room=lesson_id)
            
        except Exception as e:
            print(f"Error deleting message: {e}")
            db.session.rollback()


    # ==================== 即时通讯 WebSocket 事件 ====================
    
    @socketio.on('chat:connect')
    def handle_chat_connect(data):
        """聊天连接事件"""
        user_id = data.get('user_id')
        token = data.get('token')  # 可选的token验证
        
        if not user_id:
            return
        
        print(f"User {user_id} connected to chat")
        
        # 更新用户在线状态
        try:
            online_status = UserOnlineStatus.query.get(user_id)
            if not online_status:
                online_status = UserOnlineStatus(
                    user_id=user_id,
                    is_online=True,
                    last_seen=datetime.now(),
                    socket_id=request.sid
                )
                db.session.add(online_status)
            else:
                online_status.is_online = True
                online_status.last_seen = datetime.now()
                online_status.socket_id = request.sid
            
            db.session.commit()
            
            # 广播用户上线
            emit('chat:user_online', {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            
        except Exception as e:
            print(f"Error in chat:connect: {e}")
            db.session.rollback()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """用户断开连接"""
        try:
            # 查找断开连接的用户
            online_status = UserOnlineStatus.query.filter_by(socket_id=request.sid).first()
            if online_status:
                online_status.is_online = False
                online_status.last_seen = datetime.now()
                online_status.socket_id = None
                db.session.commit()
                
                # 广播用户离线
                emit('chat:user_offline', {
                    'user_id': online_status.user_id,
                    'last_seen': online_status.last_seen.isoformat()
                }, broadcast=True)
        except Exception as e:
            print(f"Error in disconnect: {e}")
            db.session.rollback()
    
    @socketio.on('chat:join')
    def handle_chat_join(data):
        """加入对话房间"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        
        if not conversation_id or not user_id:
            return
        
        # 验证用户是否是该对话成员
        membership = ConversationMember.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            left_at=None
        ).first()
        
        if not membership:
            emit('chat:error', {'message': '无权加入该对话'}, room=request.sid)
            return
        
        room_name = f'chat_{conversation_id}'
        join_room(room_name)
        
        print(f"User {user_id} joined conversation {conversation_id}")
        
        emit('chat:joined', {
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat()
        }, room=request.sid)
    
    @socketio.on('chat:leave')
    def handle_chat_leave(data):
        """离开对话房间"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        
        room_name = f'chat_{conversation_id}'
        leave_room(room_name)
        
        print(f"User {user_id} left conversation {conversation_id}")
    
    @socketio.on('chat:send_message')
    def handle_chat_send_message(data):
        """发送聊天消息（实时）"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to_id')
        root_message_id = data.get('root_message_id')  # Telegram式评论
        parent_message_id = data.get('parent_message_id')  # 评论回复
        
        if not conversation_id or not user_id:
            return
        
        # 验证权限
        membership = ConversationMember.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            left_at=None
        ).first()
        
        if not membership:
            emit('chat:error', {'message': '无权发送消息'}, room=request.sid)
            return
        
        try:
            # 创建消息
            message = IMMessage(
                id=generate_next_id(IMMessage),
                conversation_id=conversation_id,
                sender_id=user_id,
                content=content,
                message_type=message_type,
                reply_to_id=reply_to_id,
                root_message_id=root_message_id,
                parent_message_id=parent_message_id,
                media_url=data.get('media_url'),
                file_name=data.get('file_name'),
                file_size=data.get('file_size'),
                extra_data=data.get('extra_data')
            )
            db.session.add(message)
            
            # 更新对话最后消息时间
            conversation = Conversation.query.get(conversation_id)
            conversation.last_message_at = datetime.now()
            conversation.updated_at = datetime.now()
            
            # 获取发送者信息
            sender = Users.query.get(user_id)
            
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
            
            # 如果是频道评论，更新根消息的评论计数
            if root_message_id:
                root_message = IMMessage.query.get(root_message_id)
                if root_message:
                    root_message.comment_count = (root_message.comment_count or 0) + 1
            
            db.session.commit()
            
            # 构建消息数据
            message_data = {
                'id': message.id,
                'conversation_id': conversation_id,
                'sender_id': user_id,
                'sender_name': sender.real_name,
                'content': content,
                'message_type': message_type,
                'reply_to_id': reply_to_id,
                'root_message_id': root_message_id,
                'parent_message_id': parent_message_id,
                'media_url': message.media_url,
                'file_name': message.file_name,
                'created_at': message.created_at.isoformat()
            }
            
            # 如果是回复消息，添加被回复的消息信息
            if reply_to_id:
                reply_to = IMMessage.query.get(reply_to_id)
                if reply_to:
                    message_data['reply_to'] = {
                        'id': reply_to.id,
                        'sender_name': reply_to.sender.real_name,
                        'content': reply_to.content[:50] + '...' if len(reply_to.content) > 50 else reply_to.content
                    }
            
            # 广播到对话房间
            room_name = f'chat_{conversation_id}'
            emit('chat:new_message', message_data, room=room_name)
            
            # 向发送者确认
            emit('chat:message_sent', {
                'id': message.id,
                'temp_id': data.get('temp_id'),  # 客户端临时ID，用于匹配
                'created_at': message.created_at.isoformat()
            }, room=request.sid)
            
        except Exception as e:
            print(f"Error sending message: {e}")
            db.session.rollback()
            emit('chat:error', {'message': '发送失败'}, room=request.sid)
    
    @socketio.on('chat:typing')
    def handle_chat_typing(data):
        """正在输入状态"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        
        if not conversation_id or not user_id:
            return
        
        # 获取用户信息
        user = Users.query.get(user_id)
        if not user:
            return
        
        # 广播到对话房间（排除发送者自己）
        room_name = f'chat_{conversation_id}'
        emit('chat:user_typing', {
            'user_id': user_id,
            'user_name': user.real_name,
            'timestamp': datetime.now().isoformat()
        }, room=room_name, include_self=False)
    
    @socketio.on('chat:stop_typing')
    def handle_chat_stop_typing(data):
        """停止输入状态"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        
        if not conversation_id or not user_id:
            return
        
        room_name = f'chat_{conversation_id}'
        emit('chat:user_stop_typing', {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }, room=room_name, include_self=False)
    
    @socketio.on('chat:message_read')
    def handle_chat_message_read(data):
        """标记消息已读（实时）"""
        message_id = data.get('message_id')
        user_id = data.get('user_id')
        conversation_id = data.get('conversation_id')
        
        if not message_id or not user_id:
            return
        
        try:
            message = IMMessage.query.get(message_id)
            if not message:
                return
            
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
                if status.status != 'read':
                    status.status = 'read'
                    status.timestamp = datetime.now()
            
            # 更新成员的最后已读消息ID
            membership = ConversationMember.query.filter_by(
                conversation_id=conversation_id,
                user_id=user_id
            ).first()
            
            if membership:
                membership.last_read_message_id = message_id
                membership.last_read_at = datetime.now()
                if membership.unread_count > 0:
                    membership.unread_count -= 1
            
            db.session.commit()
            
            # 通知消息发送者（已读回执）
            room_name = f'chat_{conversation_id}'
            emit('chat:message_status', {
                'message_id': message_id,
                'user_id': user_id,
                'status': 'read',
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
            
        except Exception as e:
            print(f"Error marking message read: {e}")
            db.session.rollback()
    
    @socketio.on('chat:delete_message')
    def handle_chat_delete_message(data):
        """删除消息（实时）"""
        message_id = data.get('message_id')
        user_id = data.get('user_id')
        conversation_id = data.get('conversation_id')
        
        if not message_id or not user_id:
            return
        
        try:
            message = IMMessage.query.get(message_id)
            if not message:
                return
            
            # 只能删除自己的消息
            if message.sender_id != user_id:
                emit('chat:error', {'message': '无权删除该消息'}, room=request.sid)
                return
            
            message.is_deleted = True
            message.deleted_at = datetime.now()
            message.content = '[消息已删除]'
            
            db.session.commit()
            
            # 广播删除事件
            room_name = f'chat_{conversation_id}'
            emit('chat:message_deleted', {
                'message_id': message_id,
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
            
        except Exception as e:
            print(f"Error deleting message: {e}")
            db.session.rollback()
    
    @socketio.on('chat:edit_message')
    def handle_chat_edit_message(data):
        """编辑消息（实时）"""
        message_id = data.get('message_id')
        user_id = data.get('user_id')
        conversation_id = data.get('conversation_id')
        new_content = data.get('content', '').strip()
        
        if not message_id or not user_id or not new_content:
            return
        
        try:
            message = IMMessage.query.get(message_id)
            if not message:
                return
            
            # 只能编辑自己的消息
            if message.sender_id != user_id:
                emit('chat:error', {'message': '无权编辑该消息'}, room=request.sid)
                return
            
            # 只能编辑文本消息
            if message.message_type != 'text':
                emit('chat:error', {'message': '只能编辑文本消息'}, room=request.sid)
                return
            
            message.content = new_content
            message.is_edited = True
            message.edited_at = datetime.now()
            
            db.session.commit()
            
            # 广播编辑事件
            room_name = f'chat_{conversation_id}'
            emit('chat:message_edited', {
                'message_id': message_id,
                'content': new_content,
                'edited_at': message.edited_at.isoformat()
            }, room=room_name)
            
        except Exception as e:
            print(f"Error editing message: {e}")
            db.session.rollback()


