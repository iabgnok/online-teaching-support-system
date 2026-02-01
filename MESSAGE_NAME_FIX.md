# 消息显示用户名问题修复说明

## 问题描述

用户登录后，在聊天界面发送消息时：
- 测试数据中的历史消息显示正确的真实姓名（如"吴颢岚"）
- 但新发送的消息显示用户ID（如"3"）或学号（如"3123004715"）

## 根本原因

登录时 localStorage 存储的 `user_name` 使用的是 `username`（学号/工号）而不是 `real_name`（真实姓名）。

## 已修复内容

### 1. 登录逻辑修复 (Login.vue)
```javascript
// 修改前
localStorage.setItem('user_name', user.username)

// 修改后
localStorage.setItem('user_name', user.real_name || user.username)
localStorage.setItem('username', user.username)
localStorage.setItem('real_name', user.real_name)
```

### 2. Chat.vue 消息发送
```javascript
// 添加用户名常量
const userName = localStorage.getItem('user_name') || 
                 localStorage.getItem('real_name') || 
                 localStorage.getItem('username')

// 发送消息时使用
sender_name: userName
```

### 3. MessageList.vue 显示
```javascript
// 获取当前用户名时添加后备方案
const currentUserName = localStorage.getItem('user_name') || 
                        localStorage.getItem('real_name') || 
                        localStorage.getItem('username')
```

### 4. WebSocket 消息处理
- 添加 `chat:message_sent` 监听器，处理服务器确认
- 改进 `handleNewMessage` 逻辑，避免重复消息
- 使用 `==` 而不是 `===` 比较 ID（处理字符串/数字类型差异）

## 修复步骤

### 方法1：重新登录（推荐）

1. 退出当前账号
2. 重新登录
3. 系统会自动使用正确的 real_name

### 方法2：手动修复 localStorage

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 运行以下命令：

```javascript
// 查看当前值
console.log('user_name:', localStorage.getItem('user_name'))
console.log('real_name:', localStorage.getItem('real_name'))

// 手动修复
localStorage.setItem('user_name', localStorage.getItem('real_name'))

// 验证
console.log('修复后 user_name:', localStorage.getItem('user_name'))
```

4. 刷新页面

### 方法3：使用检查工具

访问：http://localhost:5173/check-storage.html

这个页面会：
- 显示所有 localStorage 存储的用户信息
- 自动诊断问题
- 提供一键清除并重新登录的选项

## 验证修复

重新登录后，检查：

1. **localStorage 检查**
```javascript
localStorage.getItem('user_name')  // 应该显示真实姓名，如"吴颢岚"
localStorage.getItem('username')   // 应该显示学号，如"3123004715"
localStorage.getItem('real_name')  // 应该显示真实姓名，如"吴颢岚"
```

2. **发送测试消息**
- 新发送的消息应该显示真实姓名
- 消息气泡应该在右侧（己方消息）
- 头像应该显示姓名的首字母

3. **消息列表检查**
- 己方消息：右侧蓝色气泡，显示首字母头像
- 对方消息：左侧白色气泡，显示对方姓名和头像

## 后端数据正确性

后端 API 已正确返回 `sender.real_name`：

```python
# api/v1/chat.py
message_data = {
    'sender_name': msg.sender.real_name,  # ✅ 使用 real_name
    ...
}

# api/v1/live_socket.py
message_data = {
    'sender_name': sender.real_name,  # ✅ 使用 real_name
    ...
}
```

## 相关文件

修改的文件：
- `frontend/src/views/Login.vue` - 登录时存储 real_name
- `frontend/src/views/Chat.vue` - 发送消息时使用 real_name
- `frontend/src/components/MessageList.vue` - 显示时获取 real_name

新增工具：
- `frontend/public/check-storage.html` - localStorage 检查工具
- `fix_message_names.py` - 消息名称修复脚本（仅供参考）

## 常见问题

### Q1: 历史消息显示正确，新消息显示错误？
A: 旧数据来自后端 API（已正确返回 real_name），新消息来自本地 localStorage（可能存储了 username）。重新登录即可修复。

### Q2: 为什么有时显示"3"？
A: "3"可能是 user_id 的最后一位或某个计数器。检查 localStorage.getItem('user_name') 是否正确。

### Q3: 群聊中如何显示发送者？
A: 群聊消息都会显示 sender_name，无论是否是己方消息。只是己方消息在右侧，对方消息在左侧。

### Q4: 头像显示的是什么？
A: 显示真实姓名的第一个字符。例如"吴颢岚"显示"吴"，"张明"显示"张"。

## 技术细节

### localStorage 键值对照表

| 键名 | 来源 | 用途 | 示例值 |
|------|------|------|--------|
| user_id | login API | 用户ID | "3001" |
| user_name | login API | **显示名称** | "吴颢岚" ✅ |
| username | login API | 登录账号 | "3123004715" |
| real_name | login API | 真实姓名 | "吴颢岚" |
| user_role | login API | 用户角色 | "student" |
| user_token | login API | 认证令牌 | "eyJ..." |

### 消息数据结构

```javascript
{
  id: 20,                           // 消息ID
  conversation_id: 3,               // 对话ID
  sender_id: "3001",                // 发送者ID
  sender_name: "吴颢岚",            // 发送者姓名 ✅
  content: "测试消息",              // 消息内容
  message_type: "text",             // 消息类型
  created_at: "2026-02-01T15:08:00", // 发送时间
  pending: false                    // 是否待确认
}
```

## 总结

- ✅ 代码已修复，确保使用 real_name 而不是 username
- ✅ 后端 API 正确返回 sender.real_name
- ✅ WebSocket 消息处理已优化
- ⚠️ 已登录用户需要重新登录以更新 localStorage
- 📝 新用户登录会自动使用正确的配置

---

**修复完成时间**: 2026年2月1日  
**影响范围**: 所有已登录用户需重新登录  
**向后兼容**: ✅ 代码包含后备方案，不会导致崩溃
