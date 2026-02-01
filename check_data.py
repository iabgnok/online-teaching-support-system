#!/usr/bin/env python3
"""检查教师和班级数据"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app, db
from models import Users, TeacherClass, TeachingClass

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    print("=== 教师用户 ===")
    teachers = Users.query.filter_by(role='teacher').all()
    if not teachers:
        print("没有找到教师用户")
    else:
        for teacher in teachers:
            print(f"ID: {teacher.user_id}, Name: {teacher.real_name}")

    print("\n=== 班级信息 ===")
    classes = TeachingClass.query.all()
    if not classes:
        print("没有找到班级")
    else:
        for cls in classes:
            print(f"ID: {cls.class_id}, Name: {cls.class_name}")

    print("\n=== 教师-班级关联 ===")
    associations = TeacherClass.query.all()
    if not associations:
        print("没有教师-班级关联")
    else:
        for assoc in associations:
            teacher = Users.query.get(assoc.teacher_id)
            cls = TeachingClass.query.get(assoc.class_id)
            teacher_name = teacher.real_name if teacher else f"ID:{assoc.teacher_id}"
            class_name = cls.class_name if cls else f"ID:{assoc.class_id}"
            print(f"教师: {teacher_name} -> 班级: {class_name}")

    print("\n=== 统计信息 ===")
    print(f"教师数量: {Users.query.filter_by(role='teacher').count()}")
    print(f"班级数量: {TeachingClass.query.count()}")
    print(f"教师-班级关联数量: {TeacherClass.query.count()}")