#!/usr/bin/env python3
"""导入测试数据到数据库"""

import sys
import os
import csv
sys.path.append(os.path.dirname(__file__))

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Users, Department, Course, TeachingClass, TeacherClass

def import_teachers():
    """导入教师数据"""
    print("导入教师数据...")
    try:
        with open('test_import_samples/import_teachers.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"处理教师: {row.get('username', 'unknown')}")
                # 检查是否已存在
                if Users.query.filter_by(username=row['username']).first():
                    print(f"教师 {row['username']} 已存在，跳过")
                    continue

                # 创建用户
                user = Users(
                    username=row['username'],
                    real_name=row['real_name'],
                    phone=row['phone'],
                    email=row['email'],
                    role='teacher',
                    status=1
                )
                user.set_password(row['password'])
                db.session.add(user)
                print(f"添加教师: {row['real_name']}")
    except Exception as e:
        print(f"导入教师数据失败: {e}")

def import_teaching_classes():
    """导入教学班级"""
    print("导入教学班级...")
    try:
        with open('test_import_samples/import_teaching_classes.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"处理班级: {row.get('class_name', 'unknown')}")
                # 检查是否已存在
                if TeachingClass.query.filter_by(class_name=row['class_name']).first():
                    print(f"班级 {row['class_name']} 已存在，跳过")
                    continue

                # 创建班级
                cls = TeachingClass(
                    class_name=row['class_name'],
                    semester=row['semester'],
                    class_time=row['class_time'],
                    classroom=row['classroom'],
                    capacity=int(row['capacity']),
                    status=int(row['status'])
                )
                db.session.add(cls)
                print(f"添加班级: {row['class_name']}")
    except Exception as e:
        print(f"导入班级数据失败: {e}")

def import_teacher_classes():
    """导入教师-班级关联"""
    print("导入教师-班级关联...")
    try:
        with open('test_import_samples/import_teacher_classes.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"处理关联: {row.get('teacher_no', 'unknown')} -> {row.get('class_name', 'unknown')}")
                # 查找教师和班级
                teacher = Users.query.filter_by(username=row['teacher_no']).first()
                cls = TeachingClass.query.filter_by(class_name=row['class_name']).first()

                if not teacher:
                    print(f"教师 {row['teacher_no']} 不存在，跳过")
                    continue
                if not cls:
                    print(f"班级 {row['class_name']} 不存在，跳过")
                    continue

                # 检查关联是否已存在
                if TeacherClass.query.filter_by(teacher_id=teacher.user_id, class_id=cls.class_id).first():
                    print(f"教师-班级关联已存在，跳过")
                    continue

                # 创建关联
                assoc = TeacherClass(
                    teacher_id=teacher.user_id,
                    class_id=cls.class_id,
                    role=row['role']
                )
                db.session.add(assoc)
                print(f"添加关联: {teacher.real_name} -> {cls.class_name}")
    except Exception as e:
        print(f"导入关联数据失败: {e}")

def main():
    with app.app_context():
        try:
            import_teachers()
            import_teaching_classes()
            import_teacher_classes()
            db.session.commit()
            print("数据导入完成！")
        except Exception as e:
            db.session.rollback()
            print(f"导入失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()