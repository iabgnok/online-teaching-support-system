"""
测试考勤API端点
"""
import requests

def test_api():
    print("=" * 60)
    print("测试考勤API端点")
    print("=" * 60)
    
    # 测试未登录访问（应返回401或重定向）
    print("\n1. 测试API端点可达性...")
    try:
        response = requests.get('http://localhost:5000/api/v1/attendance/class/201/me', 
                               allow_redirects=False, timeout=3)
        print(f"   状态码: {response.status_code}")
        if response.status_code in [302, 401]:
            print("   ✓ API端点正常（需要登录）")
        elif response.status_code == 404:
            print("   ✗ API端点未找到（路由问题）")
        else:
            print(f"   ? 意外状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ 连接失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("结论:")
    print("=" * 60)
    if response.status_code in [302, 401]:
        print("✅ 后端API路由配置正确")
        print("✅ 前端应该可以正常调用考勤接口")
        print("\n请在浏览器中测试:")
        print("  1. 打开 http://localhost:5173")
        print("  2. 使用学生账号登录: 3123004715 / 123456")
        print("  3. 进入课程详情 → 我的考勤")
        print("  4. 查看是否有'签到'按钮")
    else:
        print("⚠️  API端点可能有问题，请检查后端日志")

if __name__ == '__main__':
    test_api()
