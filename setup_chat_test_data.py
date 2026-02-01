"""
创建聊天系统测试数据
为教师和学生创建一些测试对话和消息
"""

import sys
import io
# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models import db, Conversation, ConversationMember, IMMessage, Users, generate_next_id
from datetime import datetime, timedelta
from app import app
import random

def create_test_conversations():
    """创建测试对话数据"""
    
    with app.app_context():
        print("=" * 60)
        print("开始创建聊天测试数据...")
        print("=" * 60)
        
        # 获取测试用户
        teacher = Users.query.filter_by(username='teacher001').first()
        student1 = Users.query.filter_by(username='3123004715').first()
        # 查找第二个学生（通过用户名）
        student2 = Users.query.filter_by(username='3123004716').first()
        if not student2:
            # 尝试查找任何其他学生
            student2 = Users.query.filter_by(role='student').filter(
                Users.user_id != (student1.user_id if student1 else 0)
            ).first()
        
        if not teacher or not student1:
            print("[ERROR] 未找到测试用户，请先运行 setup_test_data.py")
            return
        
        print(f"[OK] 找到测试用户:")
        print(f"  - 教师: {teacher.username} (ID: {teacher.user_id})")
        print(f"  - 学生1: {student1.username} (ID: {student1.user_id})")
        if student2:
            print(f"  - 学生2: {student2.username} (ID: {student2.user_id})")
        
        # 1. 创建教师与学生1的私聊
        print("\n1. 创建教师与学生1的私聊...")
        conv1 = Conversation.query.filter_by(
            conversation_type='private'
        ).join(ConversationMember).filter(
            ConversationMember.user_id.in_([teacher.user_id, student1.user_id])
        ).first()
        
        if not conv1:
            conv1_id = generate_next_id(Conversation)
            conv1 = Conversation(
                id=conv1_id,
                conversation_type='private',
                created_at=datetime.now() - timedelta(days=5),
                updated_at=datetime.now() - timedelta(hours=2)
            )
            db.session.add(conv1)
            db.session.flush()
            
            # 添加成员
            member1 = ConversationMember(
                conversation_id=conv1.id,
                user_id=teacher.user_id,
                joined_at=datetime.now() - timedelta(days=5),
                unread_count=0
            )
            member2 = ConversationMember(
                conversation_id=conv1.id,
                user_id=student1.user_id,
                joined_at=datetime.now() - timedelta(days=5),
                unread_count=3  # 学生有3条未读消息
            )
            db.session.add(member1)
            db.session.add(member2)
            db.session.flush()
            
            # 添加一些历史消息
            messages = [
                ("老师好，我想请教一下作业的问题", student1.user_id, datetime.now() - timedelta(days=5)),
                ("你好，什么问题呢？", teacher.user_id, datetime.now() - timedelta(days=5, hours=-1)),
                ("第三题不太理解解题思路", student1.user_id, datetime.now() - timedelta(days=5, hours=-2)),
                ("这道题需要先理解递归的概念...", teacher.user_id, datetime.now() - timedelta(days=4)),
                ("明白了，谢谢老师！", student1.user_id, datetime.now() - timedelta(days=4, hours=-1)),
                ("关于期末考试的复习范围是哪些章节？", student1.user_id, datetime.now() - timedelta(hours=2)),
                ("主要是1-8章，重点在3、5、7章", teacher.user_id, datetime.now() - timedelta(hours=1)),
                ("好的，谢谢老师", student1.user_id, datetime.now() - timedelta(minutes=30)),
            ]
            
            for content, sender_id, created_at in messages:
                msg_id = generate_next_id('IMMessage')
                message = IMMessage(
                    id=msg_id,
                    conversation_id=conv1.id,
                    sender_id=sender_id,
                    content=content,
                    message_type='text',
                    created_at=created_at,
                    is_deleted=False
                )
                db.session.add(message)
            
            print(f"[OK] 创建私聊对话 (ID: {conv1.id})，包含 {len(messages)} 条消息")
        else:
            print(f"[OK] 私聊对话已存在 (ID: {conv1.id})")
        
        # 2. 创建班级群聊（如果有多个学生）
        if student2:
            print("\n2. 创建班级群聊...")
            group_conv = Conversation.query.filter_by(
                conversation_type='group',
                title='软件工程201班'
            ).first()
            
            if not group_conv:
                group_id = generate_next_id(Conversation)
                group_conv = Conversation(
                    id=group_id,
                    conversation_type='group',
                    title='软件工程201班',
                    avatar='/static/default_group.png',
                    created_at=datetime.now() - timedelta(days=30),
                    updated_at=datetime.now() - timedelta(minutes=10)
                )
                db.session.add(group_conv)
                db.session.flush()
                
                # 添加成员：教师 + 2个学生
                members = [
                    (teacher.user_id, 0),  # 教师作为管理员，无未读
                    (student1.user_id, 5),  # 学生1有5条未读
                    (student2.user_id, 5),  # 学生2有5条未读
                ]
                
                for user_id, unread in members:
                    member = ConversationMember(
                        conversation_id=group_conv.id,
                        user_id=user_id,
                        joined_at=datetime.now() - timedelta(days=30),
                        role='admin' if user_id == teacher.user_id else 'member',
                        unread_count=unread
                    )
                    db.session.add(member)
                db.session.flush()
                
                # 添加群聊消息
                group_messages = [
                    ("欢迎大家加入班级群！", teacher.user_id, datetime.now() - timedelta(days=30)),
                    ("老师好！", student1.user_id, datetime.now() - timedelta(days=30, hours=-1)),
                    ("老师好！", student2.user_id, datetime.now() - timedelta(days=30, hours=-2)),
                    ("本周五的课程改为线上授课，请大家准时参加", teacher.user_id, datetime.now() - timedelta(days=3)),
                    ("收到！", student1.user_id, datetime.now() - timedelta(days=3, hours=-1)),
                    ("好的", student2.user_id, datetime.now() - timedelta(days=3, hours=-2)),
                    ("周末的作业请在周一前提交", teacher.user_id, datetime.now() - timedelta(days=1)),
                    ("明白", student1.user_id, datetime.now() - timedelta(days=1, hours=-1)),
                    ("期末考试定在下周三下午2点", teacher.user_id, datetime.now() - timedelta(minutes=10)),
                    ("收到", student1.user_id, datetime.now() - timedelta(minutes=5)),
                ]
                
                for content, sender_id, created_at in group_messages:
                    msg_id = generate_next_id('IMMessage')
                    message = IMMessage(
                        id=msg_id,
                        conversation_id=group_conv.id,
                        sender_id=sender_id,
                        content=content,
                        message_type='text',
                        created_at=created_at,
                        is_deleted=False
                    )
                    db.session.add(message)
                
                print(f"[OK] 创建群聊对话 (ID: {group_conv.id})，包含 {len(group_messages)} 条消息")
            else:
                print(f"[OK] 群聊对话已存在 (ID: {group_conv.id})")
        
        # 3. 创建学生之间的私聊
        if student2:
            print("\n3. 创建学生之间的私聊...")
            student_conv = Conversation.query.filter_by(
                conversation_type='private'
            ).join(ConversationMember).filter(
                ConversationMember.user_id.in_([student1.user_id, student2.user_id])
            ).first()
            
            if not student_conv:
                student_conv_id = generate_next_id(Conversation)
                student_conv = Conversation(
                    id=student_conv_id,
                    conversation_type='private',
                    created_at=datetime.now() - timedelta(days=7),
                    updated_at=datetime.now() - timedelta(hours=5)
                )
                db.session.add(student_conv)
                db.session.flush()
                
                # 添加成员
                member1 = ConversationMember(
                    conversation_id=student_conv.id,
                    user_id=student1.user_id,
                    joined_at=datetime.now() - timedelta(days=7),
                    unread_count=0
                )
                member2 = ConversationMember(
                    conversation_id=student_conv.id,
                    user_id=student2.user_id,
                    joined_at=datetime.now() - timedelta(days=7),
                    unread_count=2
                )
                db.session.add(member1)
                db.session.add(member2)
                db.session.flush()
                
                # 添加消息
                student_messages = [
                    ("嗨，明天的课你去吗？", student1.user_id, datetime.now() - timedelta(days=7)),
                    ("去的，我们一起吧", student2.user_id, datetime.now() - timedelta(days=7, hours=-1)),
                    ("好的，8点图书馆见", student1.user_id, datetime.now() - timedelta(days=6)),
                    ("👌", student2.user_id, datetime.now() - timedelta(days=6, hours=-1)),
                    ("今天的笔记你记了吗？能发我看看吗", student2.user_id, datetime.now() - timedelta(hours=5)),
                    ("好的，等我整理一下", student1.user_id, datetime.now() - timedelta(hours=4)),
                ]
                
                for content, sender_id, created_at in student_messages:
                    msg_id = generate_next_id('IMMessage')
                    message = IMMessage(
                        id=msg_id,
                        conversation_id=student_conv.id,
                        sender_id=sender_id,
                        content=content,
                        message_type='text',
                        created_at=created_at,
                        is_deleted=False
                    )
                    db.session.add(message)
                
                print(f"[OK] 创建学生私聊 (ID: {student_conv.id})，包含 {len(student_messages)} 条消息")
            else:
                print(f"[OK] 学生私聊已存在 (ID: {student_conv.id})")
        
        # 提交所有更改
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("[SUCCESS] 聊天测试数据创建成功！")
            print("=" * 60)
            print("\n测试账号:")
            print(f"  教师: teacher001 / 123456")
            print(f"  学生: {student1.username} / 123456")
            if student2:
                print(f"  学生: {student2.username} / 123456")
            print("\n你现在可以登录测试聊天功能了！")
            print("=" * 60)
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] 提交失败: {e}")
            raise

if __name__ == '__main__':
    create_test_conversations()
