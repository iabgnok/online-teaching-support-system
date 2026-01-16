"""
快速测试学生成绩详情API
"""
import sys
sys.path.insert(0, 'E:/online_teaching_support_system')

from app import app, db
from models import Users, Student, TeachingClass, GradeCategory, GradeItem, StudentGradeScore
from flask_login import login_user

def test_api():
    with app.test_client() as client:
        # 登录
        with client.session_transaction() as sess:
            # 使用测试上下文
            pass
        
        # 直接测试数据库查询
        print("=== 测试数据库查询 ===")
        
        # 查找一个教学班级
        teaching_class = TeachingClass.query.first()
        if not teaching_class:
            print("❌ 没有找到教学班级")
            return
        print(f"✓ 找到教学班级: ID={teaching_class.class_id}, 名称={teaching_class.class_name}")
        
        # 查找一个学生
        student = Student.query.first()
        if not student:
            print("❌ 没有找到学生")
            return
        print(f"✓ 找到学生: ID={student.id}, 姓名={student.name}")
        
        # 查找成绩分类
        categories = GradeCategory.query.filter_by(class_id=teaching_class.class_id).all()
        print(f"✓ 找到 {len(categories)} 个成绩分类")
        
        for category in categories:
            print(f"  - 分类: {category.name} (权重: {category.weight}%)")
            items = GradeItem.query.filter_by(category_id=category.id).all()
            print(f"    包含 {len(items)} 个成绩项")
            
            for item in items:
                score_record = StudentGradeScore.query.filter_by(
                    grade_item_id=item.id,
                    student_id=student.id
                ).first()
                
                score_text = f"{score_record.score}" if score_record and score_record.score is not None else "未录入"
                print(f"    - {item.name}: {score_text}/{item.max_score}")
        
        print("\n=== 测试API端点 ===")
        # 现在测试实际的API
        # 首先需要登录
        login_response = client.post('/api/v1/login', json={
            'username': 'admin',
            'password': 'admin_password'
        })
        print(f"登录状态: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.get_json()}")
            return
        
        # 测试API
        api_url = f'/api/v1/grades/class/{teaching_class.class_id}/student/{student.id}/scores'
        print(f"调用API: {api_url}")
        response = client.get(api_url)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ 成功获取 {len(data)} 条成绩记录")
            for item in data[:3]:  # 只显示前3条
                print(f"  - {item['category_name']}/{item['item_name']}: {item['score']}/{item['max_score']}")
        else:
            print(f"❌ API调用失败: {response.get_json()}")

if __name__ == '__main__':
    with app.app_context():
        test_api()
