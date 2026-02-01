"""测试chat conversations端点"""
import requests

# 从前端看到的token
token = "eyJ1c2VyX2lkIjoyMDAxfQ.X8h-eA.wn-CSe12vAyAnhnhtApD3CtbkSQ"

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

print("测试GET /api/v1/chat/conversations")
print(f"Token: {token}")
print()

try:
    response = requests.get('http://localhost:5000/api/v1/chat/conversations', headers=headers, timeout=5)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"请求失败: {e}")
