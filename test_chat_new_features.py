"""
聊天系统新功能测试脚本
测试消息反应、置顶、转发、@提及等功能

执行方式: python test_chat_new_features.py
"""

import requests
import json

# 配置
BASE_URL = 'http://localhost:5000/api/v1'
USERNAME = 'admin'
PASSWORD = 'admin123'

class ChatFeatureTester:
    def __init__(self):
        self.token = None
        self.conversation_id = None
        self.message_id = None
        
    def login(self):
        """登录获取token"""
        print("=" * 60)
        print("1. 登录测试")
        print("=" * 60)
        
        response = requests.post(
            f'{BASE_URL}/auth/login',
            json={'username': USERNAME, 'password': PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            print(f"✓ 登录成功，Token: {self.token[:20]}...")
            return True
        else:
            print(f"✗ 登录失败: {response.text}")
            return False
    
    def get_headers(self):
        """获取请求头"""
        return {'Authorization': f'Bearer {self.token}'}
    
    def test_conversations(self):
        """测试获取对话列表"""
        print("\n" + "=" * 60)
        print("2. 获取对话列表")
        print("=" * 60)
        
        response = requests.get(
            f'{BASE_URL}/chat/conversations',
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✓ 获取成功，共 {len(conversations)} 个对话")
            if conversations:
                self.conversation_id = conversations[0]['id']
                print(f"  使用对话ID: {self.conversation_id}")
                print(f"  对话标题: {conversations[0]['title']}")
            return True
        else:
            print(f"✗ 获取失败: {response.text}")
            return False
    
    def test_send_message(self):
        """测试发送消息"""
        print("\n" + "=" * 60)
        print("3. 发送测试消息")
        print("=" * 60)
        
        response = requests.post(
            f'{BASE_URL}/chat/conversations/{self.conversation_id}/messages',
            headers=self.get_headers(),
            json={'content': '这是一条测试消息，用于测试新功能 👍'}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.message_id = data.get('id')
            print(f"✓ 发送成功，消息ID: {self.message_id}")
            return True
        else:
            print(f"✗ 发送失败: {response.text}")
            return False
    
    def test_message_reactions(self):
        """测试消息反应"""
        print("\n" + "=" * 60)
        print("4. 测试消息反应功能")
        print("=" * 60)
        
        # 添加反应
        print("\n4.1 添加 👍 反应")
        response = requests.post(
            f'{BASE_URL}/chat/messages/{self.message_id}/reactions',
            headers=self.get_headers(),
            json={'reaction': '👍'}
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ 添加成功: {response.json()['message']}")
        else:
            print(f"✗ 添加失败: {response.text}")
        
        # 添加另一个反应
        print("\n4.2 添加 ❤️ 反应")
        response = requests.post(
            f'{BASE_URL}/chat/messages/{self.message_id}/reactions',
            headers=self.get_headers(),
            json={'reaction': '❤️'}
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ 添加成功: {response.json()['message']}")
        else:
            print(f"✗ 添加失败: {response.text}")
        
        # 获取反应列表
        print("\n4.3 获取消息反应列表")
        response = requests.get(
            f'{BASE_URL}/chat/messages/{self.message_id}/reactions',
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            reactions = response.json()
            print(f"✓ 获取成功，共 {len(reactions)} 种反应")
            for r in reactions:
                print(f"  {r['reaction']}: {r['count']} 人")
        else:
            print(f"✗ 获取失败: {response.text}")
    
    def test_pin_message(self):
        """测试置顶消息"""
        print("\n" + "=" * 60)
        print("5. 测试消息置顶功能")
        print("=" * 60)
        
        # 置顶消息
        print("\n5.1 置顶消息")
        response = requests.post(
            f'{BASE_URL}/chat/messages/{self.message_id}/pin',
            headers=self.get_headers()
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ 置顶成功: {response.json()['message']}")
        else:
            print(f"✗ 置顶失败: {response.text}")
        
        # 获取置顶消息列表
        print("\n5.2 获取置顶消息列表")
        response = requests.get(
            f'{BASE_URL}/chat/conversations/{self.conversation_id}/pinned_messages',
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            pinned = response.json()
            print(f"✓ 获取成功，共 {len(pinned)} 条置顶消息")
            for p in pinned:
                print(f"  消息: {p['content'][:50]}")
                print(f"  置顶人: {p['pinned_by']}")
        else:
            print(f"✗ 获取失败: {response.text}")
    
    def test_mention(self):
        """测试@提及功能"""
        print("\n" + "=" * 60)
        print("6. 测试 @ 提及功能")
        print("=" * 60)
        
        # 搜索成员
        print("\n6.1 搜索对话成员")
        response = requests.get(
            f'{BASE_URL}/chat/conversations/{self.conversation_id}/members/search?q=',
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            members = response.json()
            print(f"✓ 搜索成功，找到 {len(members)} 个成员")
            for m in members[:3]:
                print(f"  @{m['username']} ({m['real_name']})")
        else:
            print(f"✗ 搜索失败: {response.text}")
        
        # 发送带@的消息
        if members:
            print("\n6.2 发送带 @ 的消息")
            response = requests.post(
                f'{BASE_URL}/chat/conversations/{self.conversation_id}/messages',
                headers=self.get_headers(),
                json={'content': f"@{members[0]['username']} 你好，这是一条测试消息"}
            )
            
            if response.status_code == 201:
                print(f"✓ 发送成功")
            else:
                print(f"✗ 发送失败: {response.text}")
    
    def test_forward(self):
        """测试转发功能"""
        print("\n" + "=" * 60)
        print("7. 测试消息转发功能")
        print("=" * 60)
        
        # 获取其他对话
        response = requests.get(
            f'{BASE_URL}/chat/conversations',
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            conversations = response.json()
            if len(conversations) > 1:
                target_id = conversations[1]['id']
                
                print(f"\n7.1 转发消息到对话: {conversations[1]['title']}")
                response = requests.post(
                    f'{BASE_URL}/chat/messages/{self.message_id}/forward',
                    headers=self.get_headers(),
                    json={'conversation_ids': [target_id]}
                )
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"✓ 转发成功: {data['message']}")
                else:
                    print(f"✗ 转发失败: {response.text}")
            else:
                print("⚠ 只有一个对话，无法测试转发")
        else:
            print(f"✗ 获取对话列表失败: {response.text}")
    
    def test_link_preview(self):
        """测试链接预览"""
        print("\n" + "=" * 60)
        print("8. 测试链接预览功能")
        print("=" * 60)
        
        test_url = "https://www.baidu.com"
        print(f"\n8.1 获取链接预览: {test_url}")
        
        response = requests.post(
            f'{BASE_URL}/chat/link_preview',
            headers=self.get_headers(),
            json={'url': test_url}
        )
        
        if response.status_code == 200:
            preview = response.json()
            print(f"✓ 获取成功")
            print(f"  标题: {preview.get('title')}")
            print(f"  描述: {preview.get('description', '')[:100]}")
            print(f"  域名: {preview.get('domain')}")
            print(f"  图片: {preview.get('image', '无')[:50]}")
        else:
            print(f"✗ 获取失败: {response.text}")
    
    def test_unsend(self):
        """测试撤回消息"""
        print("\n" + "=" * 60)
        print("9. 测试消息撤回功能")
        print("=" * 60)
        
        # 先发送一条新消息
        print("\n9.1 发送一条新消息")
        response = requests.post(
            f'{BASE_URL}/chat/conversations/{self.conversation_id}/messages',
            headers=self.get_headers(),
            json={'content': '这条消息将被撤回'}
        )
        
        if response.status_code == 201:
            data = response.json()
            new_msg_id = data.get('id')
            print(f"✓ 发送成功，消息ID: {new_msg_id}")
            
            # 撤回消息
            print("\n9.2 撤回消息")
            response = requests.post(
                f'{BASE_URL}/chat/messages/{new_msg_id}/unsend',
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                print(f"✓ 撤回成功: {response.json()['message']}")
            else:
                print(f"⚠ 撤回失败（可能超时）: {response.text}")
        else:
            print(f"✗ 发送失败: {response.text}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("聊天系统新功能测试")
        print("=" * 60)
        
        if not self.login():
            print("\n✗ 登录失败，终止测试")
            return
        
        if not self.test_conversations():
            print("\n✗ 获取对话失败，终止测试")
            return
        
        if not self.conversation_id:
            print("\n✗ 没有可用的对话，请先创建对话")
            return
        
        if not self.test_send_message():
            print("\n✗ 发送消息失败，终止测试")
            return
        
        self.test_message_reactions()
        self.test_pin_message()
        self.test_mention()
        self.test_forward()
        self.test_link_preview()
        self.test_unsend()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

if __name__ == '__main__':
    tester = ChatFeatureTester()
    tester.run_all_tests()
