"""
创建一个测试用的自助签到考勤记录
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Attendance, AttendanceRecord, StudentClass, TeacherClass, generate_next_id
from datetime import datetime, date

def create_test_attendance():
    with app.app_context():
        print("=" * 60)
        print("创建测试考勤记录")
        print("=" * 60)
        
        # 找一个有学生的班级
        class_id = 201  # 使用班级ID 201
        
        # 检查班级是否有学生
        students = StudentClass.query.filter_by(class_id=class_id, status=1).all()
        if not students:
            print(f"⚠️  班级 {class_id} 没有学生")
            return
        
        print(f"\n✓ 找到班级 {class_id}，共有 {len(students)} 名学生")
        
        # 删除今天已有的考勤记录（避免重复）
        today = datetime.now().date()
        existing = Attendance.query.filter_by(class_id=class_id, date=today).all()
        for att in existing:
            # 删除相关记录
            AttendanceRecord.query.filter_by(attendance_id=att.id).delete()
            db.session.delete(att)
        
        if existing:
            print(f"✓ 已删除今天的 {len(existing)} 条旧考勤记录")
        
        # 创建新的自助签到考勤
        att_id = generate_next_id(Attendance)
        new_att = Attendance(
            id=att_id,
            class_id=class_id,
            date=today,
            is_self_checkin=True  # 开启自助签到
        )
        db.session.add(new_att)
        
        # 为所有学生创建考勤记录，状态设为 absent（未签到）
        current_max_id = db.session.query(db.func.max(AttendanceRecord.id)).scalar() or 0
        
        record_objects = []
        for i, s in enumerate(students):
            rec = AttendanceRecord(
                id=current_max_id + i + 1,
                attendance_id=att_id,
                student_id=s.student_id,
                status='absent'  # 默认未签到
            )
            record_objects.append(rec)
        
        db.session.add_all(record_objects)
        db.session.commit()
        
        print(f"\n✅ 成功创建考勤记录:")
        print(f"  - 考勤ID: {att_id}")
        print(f"  - 班级ID: {class_id}")
        print(f"  - 日期: {today}")
        print(f"  - 自助签到: 是")
        print(f"  - 学生数量: {len(students)}")
        print(f"  - 初始状态: absent（未签到）")
        
        print(f"\n" + "=" * 60)
        print("测试步骤:")
        print("=" * 60)
        print("1. 使用学生账号登录前端（如：3123004715 / 123456）")
        print("2. 进入该班级的课程详情页")
        print("3. 切换到'我的考勤'标签")
        print("4. 应该能看到今天的考勤记录，状态显示'缺勤'")
        print("5. 应该能看到蓝色的'签到'按钮 ⭐")
        print("6. 点击'签到'按钮")
        print("7. 签到成功后，状态应变为'出勤'，按钮消失")

if __name__ == '__main__':
    create_test_attendance()
