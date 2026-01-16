"""测试管理员API端点"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    """测试登录"""
    response = requests.post(f"{BASE_URL}/api/v1/login", json={
        "username": "admin",  # 使用实际的管理员账户
        "password": "123456"
    })
    print(f"登录响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户: {data.get('user')}")
        return response.cookies
    return None

def test_dashboard_stats(cookies):
    """测试仪表盘统计"""
    response = requests.get(f"{BASE_URL}/api/v1/admin/dashboard/stats", cookies=cookies)
    print(f"\n仪表盘统计响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户统计: {data.get('users')}")
        print(f"课程统计: {data.get('courses')}")
        print(f"活动统计: {data.get('activities')}")
    else:
        print(f"错误: {response.text}")

def test_get_users(cookies):
    """测试获取用户列表"""
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", 
                           params={"page": 1, "per_page": 5},
                           cookies=cookies)
    print(f"\n用户列表响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户数: {len(data.get('users', []))}")
        print(f"总数: {data.get('pagination', {}).get('total')}")
    else:
        print(f"错误: {response.text}")

def test_get_departments(cookies):
    """测试获取院系列表"""
    response = requests.get(f"{BASE_URL}/api/v1/admin/departments", cookies=cookies)
    print(f"\n院系列表响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"院系数: {len(data.get('departments', []))}")
    else:
        print(f"错误: {response.text}")

def test_user_stats(cookies):
    """测试用户统计"""
    response = requests.get(f"{BASE_URL}/api/v1/admin/stats/users", cookies=cookies)
    print(f"\n用户统计响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"统计数据: {len(data.get('stats', []))} 个院系")
    else:
        print(f"错误: {response.text}")

def test_course_stats(cookies):
    """测试课程统计"""
    response = requests.get(f"{BASE_URL}/api/v1/admin/stats/courses", cookies=cookies)
    print(f"\n课程统计响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"课程数: {len(data.get('stats', []))}")
    else:
        print(f"错误: {response.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("管理员API端点测试")
    print("=" * 60)
    
    # 登录
    cookies = test_login()
    if not cookies:
        print("\n❌ 登录失败，请检查管理员账户")
        exit(1)
    
    print("\n✅ 登录成功，开始测试API...")
    
    # 测试各个端点
    test_dashboard_stats(cookies)
    test_get_users(cookies)
    test_get_departments(cookies)
    test_user_stats(cookies)
    test_course_stats(cookies)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
