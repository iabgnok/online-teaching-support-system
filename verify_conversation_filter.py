#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证对话过滤修复"""

from models import db, Users, Conversation, ConversationMember, LiveClass
from app import app

with app.app_context():
    print("=== 验证对话过滤逻辑 ===\n")
    
    # 获取学生（王芳）
    student = Users.query.filter_by(user_id=3004).first()
    
    if not student:
        print("找不到测试学生")
        exit(1)
    
    print(f"测试学生: {student.real_name} (user_id: {student.user_id})\n")
    
    # 获取所有成员关系
    memberships = ConversationMember.query.filter_by(
        user_id=student.user_id,
        left_at=None
    ).all()
    
    print(f"参与的对话总数: {len(memberships)}\n")
    
    # 模拟API的过滤逻辑
    visible_conversations = []
    hidden_conversations = []
    
    for membership in memberships:
        conv = membership.conversation
        should_hide = False
        hide_reason = ""
        
        # 过滤逻辑1: 讨论组
        if conv.group_subtype == 'discussion':
            should_hide = True
            hide_reason = "讨论组"
        
        # 过滤逻辑2: 所有live_class类型（不论活跃或已结束）
        elif conv.conversation_type == 'live_class':
            should_hide = True
            hide_reason = "课堂临时群组（live_class类型）"
        
        # 过滤逻辑3: ended_live_class类型
        elif conv.conversation_type == 'ended_live_class':
            should_hide = True
            hide_reason = "ended_live_class类型"
        
        if should_hide:
            hidden_conversations.append({
                'id': conv.id,
                'type': conv.conversation_type,
                'subtype': conv.group_subtype,
                'title': conv.title,
                'reason': hide_reason
            })
        else:
            visible_conversations.append({
                'id': conv.id,
                'type': conv.conversation_type,
                'subtype': conv.group_subtype,
                'title': conv.title
            })
    
    print("=== 应该显示的对话 ===")
    for conv in visible_conversations:
        print(f"✓ [{conv['type']}] {conv['title']}")
        if conv['subtype'] == 'channel':
            print(f"  (频道)")
    
    print(f"\n=== 应该隐藏的对话 ===")
    for conv in hidden_conversations:
        print(f"✗ [{conv['type']}] {conv['title']}")
        print(f"  原因: {conv['reason']}")
    
    print(f"\n=== 统计 ===")
    print(f"应显示: {len(visible_conversations)}")
    print(f"应隐藏: {len(hidden_conversations)}")
    print(f"总计: {len(memberships)}")
    
    # 验证频道是否显示
    channels = [c for c in visible_conversations if c['subtype'] == 'channel']
    if channels:
        print(f"\n✓ 频道正常显示 ({len(channels)}个)")
    else:
        print(f"\n⚠ 没有频道显示")
