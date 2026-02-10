"""线上授课API模块"""

from flask import Blueprint, request, jsonify, g, current_app, send_file
from werkzeug.utils import secure_filename
import os
from models import (
    db, LiveClass, DrawingData, ChatMessage, LiveParticipant, ClassNote,
    TeachingClass, Announcement, generate_next_id, Conversation, ConversationMember,
    StudentClass, IMMessage, MessageStatus
)
from datetime import datetime, timedelta
import uuid
from .auth import api_login_required

live_class_bp = Blueprint('live_class', __name__)

# ==================== 辅助函数 ====================

def generate_lesson_id():
    """生成唯一的课堂ID"""
    return str(uuid.uuid4())[:8].upper()

def check_class_permission(user, class_id):
    """检查用户是否有权限访问指定班级"""
    print(f"=== Permission Check Debug ===")
    print(f"User ID: {user.user_id}, Role: {user.role}")
    print(f"Class ID: {class_id}")
    
    if user.role == 'admin':
        print("User is admin, permission granted")
        return True
    
    if user.role == 'teacher':
        # 检查教师是否被分配到这个班级
        from models import Teacher, TeacherClass
        teacher = Teacher.query.filter_by(user_id=user.user_id).first()
        print(f"Teacher found: {teacher}")
        if teacher:
            print(f"Teacher ID: {teacher.teacher_id}")
            tc_count = TeacherClass.query.filter_by(
                teacher_id=teacher.teacher_id, 
                class_id=class_id
            ).count()
            print(f"TeacherClass count: {tc_count}")
            return tc_count > 0
        print("Teacher not found")
        return False
    
    if user.role == 'student':
        # 检查学生是否在这个班级
        from models import StudentClass
        student = user.student_profile
        if not student:
            return False
        return StudentClass.query.filter_by(
            student_id=student.student_id, 
            class_id=class_id
        ).count() > 0
    
    return False

# ==================== API端点 ====================

@live_class_bp.route('/start', methods=['POST'])
@api_login_required
def start_live_class():
    """开始线上授课"""
    data = request.get_json()
    
    print(f"=== Start Live Class Request ===")
    print(f"Request data: {data}")
    print(f"User: {g.user.user_id}, Role: {g.user.role}")
    
    class_id = data.get('class_id')
    title = data.get('title', '线上授课')
    description = data.get('description', '')
    duration = data.get('duration', 45)
    notify_methods = data.get('notify_methods', [])
    conversation_id = data.get('conversation_id')  # 班级群对话ID
    
    print(f"Class ID: {class_id}, Title: {title}")
    
    if not class_id:
        print("ERROR: Class ID is missing")
        return jsonify({'error': 'Class ID is required'}), 400
    
    # 检查教师权限
    has_permission = check_class_permission(g.user, class_id)
    print(f"Permission check result: {has_permission}")
    
    if not has_permission:
        print("ERROR: Permission denied")
        return jsonify({'error': 'No permission for this class'}), 403
    
    # 生成课堂ID
    lesson_id = generate_lesson_id()
    
    # 创建课堂记录
    print(f"Debug start: g.user.user_id = {g.user.user_id} (type: {type(g.user.user_id)})")
    print(f"Debug start: g.user.role = {g.user.role}")
    live_class = LiveClass(
        id=generate_next_id(LiveClass),
        lesson_id=lesson_id,
        teacher_id=g.user.user_id,
        class_id=class_id,
        title=title,
        start_time=datetime.now()
    )
    
    print(f"Debug: Created LiveClass with teacher_id = {live_class.teacher_id}")
    
    db.session.add(live_class)
    db.session.flush()  # 获取 live_class.id
    
    # 创建对应的聊天对话（group类型，带live_class_discussion子类型标签）
    conversation = Conversation(
        id=generate_next_id(Conversation),
        conversation_type='group',  # 改为普通群组类型
        group_subtype='normal',
        conversation_subtype='live_class_discussion',  # 特殊标签：课堂讨论区
        title=f"📚 {title} - 课堂讨论",
        created_by=g.user.user_id,
        class_id=class_id,
        live_class_id=live_class.id,
        is_archived=False,
        is_active=True
    )
    db.session.add(conversation)
    db.session.flush()
    
    # 自动添加所有班级成员（学生+教师）到对话
    # 添加教师
    teacher_member = ConversationMember(
        id=generate_next_id(ConversationMember),
        conversation_id=conversation.id,
        user_id=g.user.user_id,
        role='admin',
        joined_at=datetime.now()
    )
    db.session.add(teacher_member)
    
    # 添加所有学生
    students = StudentClass.query.filter_by(class_id=class_id).all()
    for sc in students:
        student_member = ConversationMember(
            id=generate_next_id(ConversationMember),
            conversation_id=conversation.id,
            user_id=sc.student.user_id,
            role='member',
            joined_at=datetime.now()
        )
        db.session.add(student_member)
    
    db.session.commit()
    
    # 如果指定了群消息通知，在班级群中发送课堂入口消息
    if conversation_id and '群消息' in notify_methods:
        class_message = IMMessage(
            id=generate_next_id(IMMessage),
            conversation_id=conversation_id,
            sender_id=g.user.user_id,
            message_type='live_class_entry',
            content=f'{{"lesson_id": "{lesson_id}", "title": "{title}", "description": "{description}", "duration": {duration}, "status": "active"}}',
            created_at=datetime.now()
        )
        db.session.add(class_message)
    
    # 发布公告（如果选择了群公告）
    if '群公告' in notify_methods:
        announcement = Announcement(
            id=generate_next_id(Announcement),
            title=f"📚 {title} - 课堂开始",
            content=f"{description}\n\n课堂ID: {lesson_id}\n预计时长: {duration}分钟",
            author_id=g.user.user_id,
            target_class_id=class_id,
            scope_type='class'
        )
        db.session.add(announcement)
    
    db.session.commit()
    
    return jsonify({
        'lesson_id': lesson_id,
        'live_class_id': live_class.id,
        'conversation_id': conversation.id,  # 返回对话ID
        'message': 'Live class started successfully'
    })

@live_class_bp.route('/<lesson_id>/check', methods=['GET'])
@api_login_required
def check_live_class(lesson_id):
    """验证加入课堂权限"""
    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404
    
    if live_class.status == 'ended':
        return jsonify({'error': 'Live class has ended', 'status': 'ended'}), 403
    
    # 检查用户是否属于该班级
    has_permission = check_class_permission(
        g.user, 
        live_class.class_id
    )
    
    if not has_permission:
        return jsonify({'error': 'No permission to join this class'}), 403
    
    return jsonify({
        'status': live_class.status,
        'title': live_class.title,
        'start_time': live_class.start_time.isoformat()
    })

@live_class_bp.route('/<lesson_id>/join', methods=['GET'])
@api_login_required
def join_live_class(lesson_id):
    """验证加入课堂权限"""
    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404
    
    if live_class.status == 'ended':
        return jsonify({'error': 'Live class has ended'}), 403
    
    # 检查用户是否属于该班级
    has_permission = check_class_permission(
        g.user, 
        live_class.class_id
    )
    
    if not has_permission:
        return jsonify({'error': 'No permission to join this class'}), 403
    
    # 获取对应的聊天对话
    conversation = Conversation.query.filter_by(live_class_id=live_class.id).first()
    print(f"Debug: Found conversation for live_class {live_class.id}: {conversation.id if conversation else None}")
    
    # 从统一聊天系统获取历史消息
    history_messages = []
    if conversation:
        messages = IMMessage.query.filter_by(
            conversation_id=conversation.id,
            is_deleted=False
        ).order_by(IMMessage.created_at.asc()).all()
        
        for m in messages:
            history_messages.append({
                'user_id': m.sender_id,
                'user_name': m.sender.real_name or m.sender.username,
                'message': m.content,
                'message_type': m.message_type,
                'timestamp': m.created_at.isoformat()
            })
    
    # 获取班级群对话ID
    class_group_conversation = Conversation.query.filter_by(
        class_id=live_class.class_id,
        conversation_type='class_group'
    ).first()
    
    # 获取当前在线参与者
    participants = []
    live_participants = LiveParticipant.query.filter_by(
        live_class_id=live_class.id,
        left_at=None  # 只获取未离开的参与者
    ).all()
    
    for p in live_participants:
        participants.append({
            'id': p.user_id,
            'name': p.user.real_name or p.user.username,
            'role': p.role,
            'joined_at': p.joined_at.isoformat(),
            'online': True,  # 假设所有记录都是在线的
            'hand_raised': False,
            'can_speak': p.role == 'teacher'  # 教师默认可以发言
        })
    
    # 确定用户角色
    user_role = g.user.role
    if user_role == 'admin':
        # 管理员以教师身份进入
        user_role = 'teacher'
    
    return jsonify({
        'live_class_id': live_class.id,
        'class_id': live_class.class_id,
        'title': live_class.title,
        'teacher_name': live_class.teacher.real_name,
        'start_time': live_class.start_time.isoformat(),
        'participants_count': live_class.participants_count,
        'participants': participants,  # 添加参与者列表
        'conversation_id': conversation.id if conversation else None,
        'class_group_conversation_id': class_group_conversation.id if class_group_conversation else None,
        'user_role': user_role,
        'history': history_messages
    })

@live_class_bp.route('/<lesson_id>/end', methods=['POST'])
@api_login_required
def end_live_class(lesson_id):
    print("=== End Live Class Request ===")
    print(f"Lesson ID: {lesson_id}")
    print(f"User: {g.user.user_id}, Role: {g.user.role}")

    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404

    print(f"Found live class: {live_class.id}, status: {live_class.status}")

    is_teacher = str(live_class.teacher_id) == str(g.user.user_id)
    is_admin = g.user.role == 'admin'
    if not (is_teacher or is_admin):
        return jsonify({'error': 'Only teacher or admin can end the class'}), 403

    try:
        live_class.end_time = datetime.now()
        live_class.status = 'ended'

        import json
        from extensions import socketio
        import traceback

        updated_conversations = set()
        all_entry_messages = IMMessage.query.filter_by(message_type='live_class_entry').all()
        for msg in all_entry_messages:
            try:
                content = json.loads(msg.content)
                if content.get('lesson_id') == lesson_id:
                    content['status'] = 'ended'
                    msg.content = json.dumps(content, ensure_ascii=False)
                    updated_conversations.add(msg.conversation_id)
            except Exception:
                pass

        conversations = Conversation.query.filter_by(live_class_id=live_class.id).all()
        if conversations:
            try:
                from sqlalchemy import text, bindparam
                from models import PinnedMessage, ConversationFolderItem

                conv_ids = [c.id for c in conversations]

                # Gather all message IDs across these conversations
                message_ids = db.session.query(IMMessage.id).filter(IMMessage.conversation_id.in_(conv_ids)).all()
                message_ids = [mid[0] for mid in message_ids]

                # Delete MessageStatus records for these messages using raw SQL
                if message_ids:
                    params = {f'id{i}': mid for i, mid in enumerate(message_ids)}
                    placeholders = ','.join([f":id{i}" for i in range(len(message_ids))])
                    db.session.execute(text(f"DELETE FROM MessageStatus WHERE message_id IN ({placeholders})"), params)

                # Delete pinned messages and folder items referencing these conversations
                PinnedMessage.query.filter(PinnedMessage.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
                ConversationFolderItem.query.filter(ConversationFolderItem.conversation_id.in_(conv_ids)).delete(synchronize_session=False)

                # Delete other related records
                ConversationMember.query.filter(ConversationMember.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
                IMMessage.query.filter(IMMessage.conversation_id.in_(conv_ids)).delete(synchronize_session=False)

                # Finally delete the conversations themselves
                for c in conversations:
                    db.session.delete(c)

            except Exception as e:
                import traceback
                traceback.print_exc()
                db.session.rollback()
                return jsonify({'error': 'Failed to clean up conversations', 'detail': str(e)}), 500

            # Notify clients in the class room that these conversations were deleted
            try:
                for cid in conv_ids:
                    socketio.emit('chat:conversation_deleted', {'conversation_id': cid}, room=lesson_id)
            except Exception:
                pass

        db.session.commit()

        socketio.emit('class_ended', {'message': 'Class has ended'}, room=lesson_id)

        for conv_id in updated_conversations:
            socketio.emit('chat:message_updated', {
                'conversation_id': conv_id,
                'lesson_id': lesson_id,
                'status': 'ended'
            }, room=f'conversation_{conv_id}')

    # End of try block
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

    drawings = DrawingData.query.filter_by(live_class_id=live_class.id).order_by(DrawingData.timestamp).all()
    messages = []
    # Collect messages across all conversations linked to this live_class (if any remain before deletion)
    convs_for_messages = Conversation.query.filter_by(live_class_id=live_class.id).all()
    if convs_for_messages:
        conv_ids_for_messages = [c.id for c in convs_for_messages]
        messages = IMMessage.query.filter(IMMessage.conversation_id.in_(conv_ids_for_messages), IMMessage.is_deleted==False).order_by(IMMessage.created_at).all()

    note_content = f"课堂主题: {live_class.title}\n"
    note_content += f"开始时间: {live_class.start_time}\n"
    note_content += f"结束时间: {live_class.end_time}\n"
    note_content += f"参与人数: {live_class.participants_count}\n\n"

    if drawings:
        note_content += f"画板操作次数: {len(drawings)}\n"

    if messages:
        note_content += f"聊天消息数: {len(messages)}\n"
        note_content += "\n聊天记录摘要:\n"
        for msg in messages[:10]:
            note_content += f"- {msg.user.real_name}: {msg.message[:50]}...\n"

    note = ClassNote(
        id=generate_next_id(ClassNote),
        live_class_id=live_class.id,
        teacher_id=g.user.user_id,
        title=f"{live_class.title} - 课堂笔记",
        content=note_content
    )

    db.session.add(note)
    db.session.commit()

    return jsonify({
        'message': 'Live class ended successfully',
        'note_id': note.id
    })

@live_class_bp.route('/<lesson_id>/notes', methods=['GET'])
@api_login_required
def get_class_notes(lesson_id):
    """获取课堂笔记"""
    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404
    
    # 检查权限（教师或同班学生）
    if g.user.user_id != live_class.teacher_id:
        has_permission = check_class_permission(g.user, live_class.class_id)
        if not has_permission:
            return jsonify({'error': 'No permission to view notes'}), 403
    
    notes = ClassNote.query.filter_by(live_class_id=live_class.id).all()
    
    result = []
    for note in notes:
        result.append({
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'is_published': note.is_published,
            'created_at': note.created_at.isoformat()
        })
    
    return jsonify(result)

@live_class_bp.route('/notes/<int:note_id>/publish', methods=['POST'])
@api_login_required
def publish_note(note_id):
    """发布课堂笔记"""
    note = ClassNote.query.get_or_404(note_id)
    
    # 检查是否为教师
    if note.teacher_id != g.user.user_id:
        return jsonify({'error': 'Only teacher can publish notes'}), 403
    
    note.is_published = True
    db.session.commit()
    
    # 可以选择发布为公告
    publish_to_announcement = request.get_json().get('publish_to_announcement', False)
    
    if publish_to_announcement:
        announcement = Announcement(
            id=generate_next_id(Announcement),
            title=f"📝 {note.title}",
            content=note.content,
            publisher_id=g.user.user_id,
            class_id=note.live_class.class_id,
            announcement_type='material'
        )
        db.session.add(announcement)
        db.session.commit()
    
    return jsonify({'message': 'Note published successfully'})

@live_class_bp.route('/active', methods=['GET'])
@api_login_required
def get_active_classes():
    """获取活跃的线上课堂和最近结束的课堂"""
    # 过滤掉超过24小时的"僵尸"课堂
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    if g.user.role == 'teacher':
        # 教师：获取自己创建的活跃课堂和最近结束的课堂
        classes = LiveClass.query.filter(
            LiveClass.teacher_id == g.user.user_id,
            LiveClass.start_time > cutoff_time
        ).all()
    else:
        # 学生：获取所属班级的活跃课堂和最近结束的课堂
        from models import StudentClass
        student = g.user.student_profile
        if not student:
            return jsonify([])
        student_classes = StudentClass.query.filter_by(student_id=student.student_id).all()
        class_ids = [sc.class_id for sc in student_classes]
        classes = LiveClass.query.filter(
            LiveClass.class_id.in_(class_ids),
            LiveClass.start_time > cutoff_time
        ).all()
    
    result = []
    for cls in classes:
        result.append({
            'lesson_id': cls.lesson_id,
            'title': cls.title,
            'teacher_name': cls.teacher.real_name,
            'class_name': cls.teaching_class.class_name,
            'class_id': cls.class_id,
            'start_time': cls.start_time.isoformat(),
            'participants_count': cls.participants_count,
            'status': cls.status  # 添加状态字段
        })
    
    return jsonify(result)

@live_class_bp.route('/upload-image', methods=['POST'])
@api_login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filename = f"{int(datetime.now().timestamp())}_{filename}"
        
        save_path = os.path.join(current_app.config['MATERIALS_FOLDER'], filename)
        file.save(save_path)
        
        return jsonify({'url': f'/api/v1/live-class/materials/{filename}'})

@live_class_bp.route('/materials/<filename>')
def get_material(filename):
    return send_file(os.path.join(current_app.config['MATERIALS_FOLDER'], filename))