"""
测试学生签到功能
验证考勤创建和学生签到流程
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Attendance, AttendanceRecord, Student, Users
from datetime import datetime, date

def test_attendance_checkin():
    with app.app_context():
        print("=" * 60)
        print("学生签到功能测试")
        print("=" * 60)
        
        # 1. 查找最近的考勤记录
        recent_attendance = Attendance.query.filter_by(
            date=datetime.now().date()
        ).first()
        
        if not recent_attendance:
            print("\n⚠️  今天没有考勤记录")
            print("提示：请先通过教师端创建一个自助签到的考勤记录")
            print("   1. 登录教师账号")
            print("   2. 进入班级详情页")
            print("   3. 点击'发起考勤'")
            print("   4. 选择'学生自助签到'方式")
            return
        
        print(f"\n✓ 找到今天的考勤记录:")
        print(f"  - 考勤ID: {recent_attendance.id}")
        print(f"  - 班级ID: {recent_attendance.class_id}")
        print(f"  - 日期: {recent_attendance.date}")
        print(f"  - 自助签到: {'是' if recent_attendance.is_self_checkin else '否'}")
        
        # 2. 获取该考勤的记录
        records = AttendanceRecord.query.filter_by(
            attendance_id=recent_attendance.id
        ).limit(5).all()
        
        print(f"\n✓ 考勤记录统计:")
        total_records = AttendanceRecord.query.filter_by(
            attendance_id=recent_attendance.id
        ).count()
        
        present_count = AttendanceRecord.query.filter_by(
            attendance_id=recent_attendance.id,
            status='present'
        ).count()
        
        absent_count = AttendanceRecord.query.filter_by(
            attendance_id=recent_attendance.id,
            status='absent'
        ).count()
        
        print(f"  - 总人数: {total_records}")
        print(f"  - 已签到(present): {present_count}")
        print(f"  - 未签到(absent): {absent_count}")
        
        # 3. 显示前5条记录详情
        print(f"\n✓ 前5条记录详情:")
        for i, record in enumerate(records, 1):
            student = Student.query.get(record.student_id)
            user = Users.query.get(student.user_id) if student else None
            student_name = user.real_name if user else "未知"
            student_no = student.student_no if student else "未知"
            
            # 判断是否可以签到
            can_checkin = (
                recent_attendance.is_self_checkin and 
                record.status == 'absent' and 
                recent_attendance.date == datetime.now().date()
            )
            
            status_emoji = {
                'present': '✓',
                'absent': '✗',
                'late': '△',
                'leave': '○'
            }.get(record.status, '?')
            
            print(f"  {i}. {student_name}({student_no})")
            print(f"     状态: {status_emoji} {record.status}")
            print(f"     可签到: {'是 ⭐' if can_checkin else '否'}")
        
        # 4. 验证逻辑
        print(f"\n✓ 签到逻辑验证:")
        if recent_attendance.is_self_checkin:
            print(f"  ✓ 考勤已开启自助签到")
            if absent_count > 0:
                print(f"  ✓ 有 {absent_count} 名学生尚未签到")
                print(f"  ✓ 这些学生应该能看到'签到'按钮")
            else:
                print(f"  ℹ️  所有学生已签到")
        else:
            print(f"  ⚠️  该考勤未开启自助签到（教师点名模式）")
            print(f"  ℹ️  学生无法自助签到")
        
        # 5. 给出前端测试建议
        print(f"\n" + "=" * 60)
        print("前端测试建议:")
        print("=" * 60)
        if recent_attendance.is_self_checkin and absent_count > 0:
            print("1. 使用学生账号登录系统")
            print("2. 进入课程详情页")
            print("3. 切换到'我的考勤'标签")
            print("4. 应该能看到今天的考勤记录，状态为'缺勤'")
            print("5. 应该能看到蓝色的'签到'按钮")
            print("6. 点击'签到'按钮后，状态应变为'出勤'")
        else:
            print("⚠️  当前没有可测试的自助签到记录")
            print("请按以下步骤创建测试数据:")
            print("1. 使用教师账号登录")
            print("2. 进入任一班级详情页")
            print("3. 点击'发起考勤'")
            print("4. 考勤方式选择'学生自助签到'")
            print("5. 点击发起")
            print("6. 然后使用学生账号测试签到功能")

if __name__ == '__main__':
    test_attendance_checkin()
