"""
测试新增的成绩管理API端点
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

def test_grade_apis():
    with app.app_context():
        print("=" * 60)
        print("测试成绩管理API端点")
        print("=" * 60)
        
        # 列出所有grades相关的路由
        print("\n✓ Grades相关的API路由:")
        for rule in app.url_map.iter_rules():
            if 'grades' in rule.rule or 'assignments' in rule.rule:
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                print(f"  [{methods:6}] {rule.rule}")
        
        print("\n" + "=" * 60)
        print("新增的API端点应该包括:")
        print("=" * 60)
        print("  [GET   ] /api/v1/grades/class/<class_id>/items")
        print("  [GET   ] /api/v1/grades/class/<class_id>/final")
        print("  [POST  ] /api/v1/grades/item/<item_id>/score")
        print("  [GET   ] /api/v1/assignments/<assignment_id>/grades")
        
        print("\n✅ 后端API已更新，请在浏览器中刷新页面测试")

if __name__ == '__main__':
    test_grade_apis()
