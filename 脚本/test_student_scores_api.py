"""
测试学生成绩详情API
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 测试教师登录
def test_teacher_login():
    """教师登录"""
    response = requests.post(f"{BASE_URL}/api/v1/login", json={
        'username': 'admin',
        'password': 'admin_password'
    })
    print("\n=== 教师登录 ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("登录成功!")
        return response.cookies
    else:
        print(f"登录失败: {response.json()}")
        return None

def test_get_student_scores(cookies, class_id=201, student_id=3123004715):
    """测试获取学生所有成绩"""
    response = requests.get(
        f"{BASE_URL}/api/v1/grades/class/{class_id}/student/{student_id}/scores",
        cookies=cookies
    )
    print(f"\n=== 获取学生成绩 (班级ID: {class_id}, 学生ID: {student_id}) ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"获取到 {len(data)} 条成绩记录:")
        for score in data:
            print(f"  - {score['category_name']} / {score['item_name']}: "
                  f"{score['score'] if score['score'] is not None else '未录入'} / {score['max_score']}")
        return data
    else:
        print(f"请求失败: {response.text}")
        return None

def test_get_final_grades(cookies, class_id=201):
    """测试获取总成绩列表"""
    response = requests.get(
        f"{BASE_URL}/api/v1/grades/class/{class_id}/final",
        cookies=cookies
    )
    print(f"\n=== 获取总成绩列表 (班级ID: {class_id}) ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        students = data.get('students', [])
        print(f"获取到 {len(students)} 名学生的总成绩:")
        for student in students[:3]:  # 只显示前3名
            print(f"  - {student['student_name']} ({student['student_no']}): "
                  f"{student['final_score']} 分 ({student['grade_level']})")
        return data
    else:
        print(f"请求失败: {response.text}")
        return None

if __name__ == '__main__':
    print("开始测试学生成绩详情API...")
    
    # 教师登录
    cookies = test_teacher_login()
    if not cookies:
        print("登录失败，终止测试")
        exit(1)
    
    # 测试获取总成绩列表
    final_grades = test_get_final_grades(cookies)
    
    # 测试获取单个学生的所有成绩
    if final_grades and final_grades.get('students'):
        student = final_grades['students'][0]
        test_get_student_scores(cookies, 201, student['student_id'])
    
    print("\n测试完成!")
