"""
为现有课堂创建对应的聊天对话
注意：新系统已经不再使用 ChatMessage，所有消息直接保存到 IMMessage
此脚本只为旧课堂补充创建对话结构，不迁移消息数据
"""

from app import app
from models import (
    db, LiveClass, Conversation, ConversationMember,
    generate_next_id, StudentClass
)
from datetime import datetime


def create_conversations_for_existing_classes():
    """为现有课堂创建对应的对话"""
    with app.app_context():
        print("=" * 60)
        print("为现有课堂创建聊天对话")
        print("=" * 60)
        
        # 获取所有直播课堂
        live_classes = LiveClass.query.all()
        print(f"\n找到 {len(live_classes)} 个直播课堂")
        
        migrated_classes = 0
        skipped_classes = 0
        
        for live_class in live_classes:
            print(f"\n处理课堂: {live_class.title} (ID: {live_class.lesson_id})")
            
            # 检查是否已创建对话
            existing_conversation = Conversation.query.filter_by(
                live_class_id=live_class.id
            ).first()
            
            if existing_conversation:
                print(f"  ⚠️  已存在对话 (ID: {existing_conversation.id})，跳过...")
                skipped_classes += 1
                continue
            
            # 创建对应的聊天对话
            conversation = Conversation(
                id=generate_next_id(Conversation),
                conversation_type='live_class',
                title=f"📚 {live_class.title}",
                created_by=live_class.teacher_id,
                class_id=live_class.class_id,
                live_class_id=live_class.id,
                is_archived=(live_class.status == 'ended'),
                is_active=(live_class.status == 'active'),
                created_at=live_class.start_time,
                updated_at=live_class.end_time or datetime.now()
            )
            db.session.add(conversation)
            db.session.flush()
            
            print(f"  ✓ 创建对话 (ID: {conversation.id})")
            
            # 添加教师为管理员成员
            teacher_member = ConversationMember(
                id=generate_next_id(ConversationMember),
                conversation_id=conversation.id,
                user_id=live_class.teacher_id,
                role='admin',
                joined_at=live_class.start_time
            )
            db.session.add(teacher_member)
            
            # 添加所有班级学生为成员
            students = StudentClass.query.filter_by(class_id=live_class.class_id).all()
            print(f"  添加 {len(students)} 个学生成员")
            
            for sc in students:
                student_member = ConversationMember(
                    id=generate_next_id(ConversationMember),
                    conversation_id=conversation.id,
                    user_id=sc.student.user_id,
                    role='member',
                    joined_at=live_class.start_time
                )
                db.session.add(student_member)
            
            migrated_classes += 1
        
        # 最终提交
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("创建完成！")
        print("=" * 60)
        print(f"✓ 创建对话数: {migrated_classes}")
        print(f"⚠ 跳过课堂数: {skipped_classes}")
        print("=" * 60)
        
        # 验证结果
        print("\n验证结果:")
        total_conversations = Conversation.query.filter_by(
            conversation_type='live_class'
        ).count()
        
        print(f"  live_class 类型对话总数: {total_conversations}")
        
        return True


if __name__ == '__main__':
    try:
        create_conversations_for_existing_classes()
        print("\n✅ 脚本执行成功！")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
