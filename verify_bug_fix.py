#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证bug修复 - 测试学生能否看到活跃课堂"""

from models import db, Users, StudentClass, LiveClass
from app import app

with app.app_context():
    print("=== 验证修复后的逻辑 ===\n")
    
    # 获取王芳的账号 (user_id: 3004, 在班级205中)
    student_user = Users.query.filter_by(user_id=3004).first()
    
    if not student_user:
        print("找不到测试学生")
        exit(1)
    
    print(f"测试学生: {student_user.real_name} (user_id: {student_user.user_id})")
    print(f"student_profile: {student_user.student_profile}")
    
    if not student_user.student_profile:
        print("错误: 没有 student_profile!")
        exit(1)
    
    student_id = student_user.student_profile.student_id
    print(f"student_id: {student_id}")
    
    # 使用修复后的逻辑
    print("\n=== 使用修复后的逻辑查询 ===")
    student_classes = StudentClass.query.filter_by(student_id=student_id).all()
    class_ids = [sc.class_id for sc in student_classes]
    
    print(f"学生所在班级: {class_ids}")
    
    if class_ids:
        lives = LiveClass.query.filter(
            LiveClass.class_id.in_(class_ids),
            LiveClass.status == 'active'
        ).all()
        
        print(f"\n找到 {len(lives)} 个活跃课堂:")
        for live in lives:
            print(f"  - {live.title}")
            print(f"    课堂ID: {live.lesson_id}")
            print(f"    班级ID: {live.class_id}")
            print(f"    教师: {live.teacher.real_name}")
            
        if len(lives) > 0:
            print("\n✓ 成功！学生现在可以看到活跃课堂了！")
        else:
            print("\n✗ 没有找到活跃课堂")
    else:
        print("\n✗ 学生没有加入任何班级")
