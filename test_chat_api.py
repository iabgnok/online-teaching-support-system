"""
聊天系统快速测试脚本
测试新创建的聊天API端点
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

def test_chat_api():
    """测试聊天API"""
    
    print("=" * 60)
    print("聊天系统API测试")
    print("=" * 60)
    
    # 假设已经有登录token
    headers = {
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "Content-Type": "application/json"
    }
    
    # 1. 测试获取对话列表
    print("\n1. 测试获取对话列表...")
    try:
        response = requests.get(f"{BASE_URL}/chat/conversations", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"对话数量: {len(data)}")
            print("✓ 获取对话列表成功")
        else:
            print(f"✗ 错误: {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 2. 测试创建私聊对话
    print("\n2. 测试创建私聊对话...")
    try:
        data = {
            "type": "private",
            "member_ids": [2]  # 假设用户ID 2存在
        }
        response = requests.post(
            f"{BASE_URL}/chat/conversations",
            headers=headers,
            json=data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"对话ID: {result.get('id')}")
            print("✓ 创建对话成功")
            return result.get('id')
        else:
            print(f"✗ 错误: {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    return None

def check_api_routes():
    """检查API路由是否注册"""
    print("\n" + "=" * 60)
    print("检查API路由注册")
    print("=" * 60)
    
    routes = [
        "/chat/conversations",
        "/chat/conversations/1",
        "/chat/conversations/1/messages",
        "/chat/messages/1",
        "/chat/search",
    ]
    
    for route in routes:
        print(f"\n检查路由: {route}")
        print(f"完整URL: {BASE_URL}{route}")

if __name__ == '__main__':
    print("\n⚠️  注意: 此脚本需要系统运行并且有有效的认证token")
    print("请先启动后端服务: python app.py")
    print("\n如果要实际测试，请更新脚本中的 YOUR_TOKEN_HERE")
    
    check_api_routes()
    
    # test_chat_api()  # 取消注释以运行实际测试
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    print("\n📝 手动测试建议:")
    print("1. 启动后端: python app.py")
    print("2. 启动前端: cd frontend && npm run dev")
    print("3. 登录系统")
    print("4. 访问: http://localhost:5173/chat")
    print("5. 测试创建对话、发送消息等功能")
