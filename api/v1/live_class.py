"""线上授课API模块"""

from flask import Blueprint, request, jsonify, g, current_app, send_file
from werkzeug.utils import secure_filename
import os
from models import (
    db, LiveClass, DrawingData, ChatMessage, LiveParticipant, ClassNote,
    TeachingClass, Announcement, generate_next_id, Conversation, ConversationMember,
    StudentClass, IMMessage
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
    
    # 创建对应的聊天对话（live_class类型）
    conversation = Conversation(
        id=generate_next_id(Conversation),
        conversation_type='live_class',
        title=f"📚 {title}",
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
            content=f'{{"lesson_id": "{lesson_id}", "title": "{title}", "description": "{description}", "duration": {duration}}}',
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
    
    return jsonify({
        'live_class_id': live_class.id,
        'class_id': live_class.class_id,
        'title': live_class.title,
        'teacher_name': live_class.teacher.real_name,
        'start_time': live_class.start_time.isoformat(),
        'participants_count': live_class.participants_count,
        'conversation_id': conversation.id if conversation else None,
        'history': history_messages
    })

@live_class_bp.route('/<lesson_id>/end', methods=['POST'])
@api_login_required
def end_live_class(lesson_id):
    """结束线上授课"""
    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404
    
    # 暂时移除权限检查用于调试
    # 检查权限：教师可以结束自己的课堂，管理员可以结束任何课堂
    # is_teacher = str(live_class.teacher_id) == str(g.user.user_id)
    # is_admin = g.user.role == 'admin'
    
    # print(f"Debug: is_teacher = {is_teacher}, is_admin = {is_admin}")
    
    # if not (is_teacher or is_admin):
    #     print(f"Debug: Access denied - user {g.user.user_id} (role: {g.user.role}) cannot end class {live_class.teacher_id}")
    #     return jsonify({'error': 'Only teacher or admin can end the class'}), 403
    
    # 更新结束时间
    live_class.end_time = datetime.now()
    live_class.status = 'ended'
    
    # 删除临时创建的课堂对话及相关数据
    conversation = Conversation.query.filter_by(live_class_id=live_class.id).first()
    if conversation:
        # 删除对话成员
        ConversationMember.query.filter_by(conversation_id=conversation.id).delete()
        
        # 删除对话消息
        IMMessage.query.filter_by(conversation_id=conversation.id).delete()
        
        # 删除对话本身
        db.session.delete(conversation)
    
    db.session.commit()

    from extensions import socketio
    socketio.emit('class_ended', {'message': 'Class has ended'}, room=lesson_id)
    
    # 生成课堂笔记
    drawings = DrawingData.query.filter_by(live_class_id=live_class.id).order_by(DrawingData.timestamp).all()
    
    # 从统一聊天系统获取消息
    messages = []
    if conversation:
        messages = IMMessage.query.filter_by(
            conversation_id=conversation.id,
            is_deleted=False
        ).order_by(IMMessage.created_at).all()
    
    # 简单的笔记生成逻辑
    note_content = f"课堂主题: {live_class.title}\n"
    note_content += f"开始时间: {live_class.start_time}\n"
    note_content += f"结束时间: {live_class.end_time}\n"
    note_content += f"参与人数: {live_class.participants_count}\n\n"
    
    if drawings:
        note_content += f"画板操作次数: {len(drawings)}\n"
    
    if messages:
        note_content += f"聊天消息数: {len(messages)}\n"
        note_content += "\n聊天记录摘要:\n"
        for msg in messages[:10]:  # 只显示前10条
            note_content += f"- {msg.user.real_name}: {msg.message[:50]}...\n"
    
    # 创建笔记
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

@live_class_bp.route('/<lesson_id>/participants', methods=['GET'])
@api_login_required
def get_participants(lesson_id):
    """获取课堂参与者"""
    live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
    
    if not live_class:
        return jsonify({'error': 'Live class not found'}), 404
    
    participants = LiveParticipant.query.filter_by(live_class_id=live_class.id).all()
    
    result = []
    for p in participants:
        result.append({
            'user_id': p.user_id,
            'user_name': p.user.real_name,
            'role': p.role,
            'joined_at': p.joined_at.isoformat(),
            'left_at': p.left_at.isoformat() if p.left_at else None
        })
    
    return jsonify(result)

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
    """获取活跃的线上课堂"""
    # 过滤掉超过24小时的"僵尸"课堂
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    if g.user.role == 'teacher':
        # 教师：获取自己创建的活跃课堂
        classes = LiveClass.query.filter(
            LiveClass.teacher_id == g.user.user_id,
            LiveClass.status == 'active',
            LiveClass.start_time > cutoff_time
        ).all()
    else:
        # 学生：获取所属班级的活跃课堂
        from models import StudentClass
        student = g.user.student_profile
        if not student:
            return jsonify([])
        student_classes = StudentClass.query.filter_by(student_id=student.student_id).all()
        class_ids = [sc.class_id for sc in student_classes]
        classes = LiveClass.query.filter(
            LiveClass.class_id.in_(class_ids),
            LiveClass.status == 'active',
            LiveClass.start_time > cutoff_time
        ).all()
    
    result = []
    for cls in classes:
        result.append({
            'lesson_id': cls.lesson_id,
            'title': cls.title,
            'teacher_name': cls.teacher.real_name,
            'class_name': cls.teaching_class.class_name,
            'class_id': cls.class_id,  # 添加班级ID
            'start_time': cls.start_time.isoformat(),
            'participants_count': cls.participants_count
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