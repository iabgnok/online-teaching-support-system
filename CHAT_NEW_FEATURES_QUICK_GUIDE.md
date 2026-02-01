# 聊天系统新功能快速参考

## 🚀 新功能概览

| 功能 | 状态 | API 端点 | 说明 |
|------|------|----------|------|
| 消息反应 | ✅ 已完成 | POST/GET/DELETE `/chat/messages/<id>/reactions` | 表情快速反馈 |
| 消息置顶 | ✅ 已完成 | GET/POST/DELETE `/chat/conversations/<id>/pinned_messages` | 群组公告 |
| @ 提及 | ✅ 已完成 | GET `/chat/mentions` | 精确通知 |
| 消息转发 | ✅ 已完成 | POST `/chat/messages/<id>/forward` | 分享内容 |
| 撤回消息 | ✅ 已完成 | POST `/chat/messages/<id>/unsend` | 5分钟内撤回 |
| 删除消息 | ✅ 已完成 | POST `/chat/messages/<id>/delete_for_me` | 仅对我删除 |
| 链接预览 | ✅ 已完成 | POST `/chat/link_preview` | 自动预览 |

---

## 📚 API 使用示例

### 1. 消息反应

#### 添加反应
```http
POST /api/v1/chat/messages/123/reactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "reaction": "👍"
}
```

**支持的表情**：👍 ❤️ 😂 😮 😢 🙏 🔥 👏

**返回**：
```json
{
  "message": "已添加反应",
  "action": "added"  // 或 "updated"（更换）、"removed"（取消）
}
```

#### 获取消息反应
```http
GET /api/v1/chat/messages/123/reactions
Authorization: Bearer <token>
```

**返回**：
```json
[
  {
    "reaction": "👍",
    "count": 5,
    "users": [
      {"user_id": 1, "real_name": "张三"},
      {"user_id": 2, "real_name": "李四"}
    ]
  }
]
```

---

### 2. 消息置顶

#### 置顶消息（需要管理员权限）
```http
POST /api/v1/chat/messages/123/pin
Authorization: Bearer <token>
```

#### 获取置顶消息列表
```http
GET /api/v1/chat/conversations/456/pinned_messages
Authorization: Bearer <token>
```

**返回**：
```json
[
  {
    "pin_id": 1,
    "message_id": 123,
    "content": "欢迎加入课程群！",
    "sender_name": "王老师",
    "message_type": "text",
    "pinned_by": "管理员",
    "pinned_at": "2026-02-01T10:00:00"
  }
]
```

#### 取消置顶
```http
DELETE /api/v1/chat/pinned_messages/1
Authorization: Bearer <token>
```

---

### 3. @ 提及功能

#### 搜索对话成员（用于自动补全）
```http
GET /api/v1/chat/conversations/456/members/search?q=张
Authorization: Bearer <token>
```

**返回**：
```json
[
  {
    "user_id": 1,
    "username": "zhangsan",
    "real_name": "张三",
    "role": "member"
  }
]
```

#### 发送带 @ 的消息
```http
POST /api/v1/chat/conversations/456/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "@zhangsan 你好，请查看作业"
}
```

**自动行为**：
- 解析消息中的 `@username`
- 验证用户是否是对话成员
- 创建提及通知记录
- 在 `extra_data.mentioned_users` 存储被提及用户ID

#### 获取我的提及通知
```http
GET /api/v1/chat/mentions?unread_only=true
Authorization: Bearer <token>
```

**返回**：
```json
{
  "mentions": [
    {
      "mention_id": 1,
      "message_id": 123,
      "conversation_id": 456,
      "conversation_title": "课程群",
      "sender_name": "王老师",
      "content": "@zhangsan 你好，请查看作业",
      "is_read": false,
      "created_at": "2026-02-01T10:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "has_next": true
}
```

#### 标记提及为已读
```http
POST /api/v1/chat/mentions/1/read
Authorization: Bearer <token>
```

---

### 4. 消息转发

```http
POST /api/v1/chat/messages/123/forward
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_ids": [456, 789]
}
```

**返回**：
```json
{
  "message": "已转发到 2 个对话",
  "count": 2
}
```

**转发消息特征**：
- `forward_from_id` 指向原消息
- `extra_data.forwarded_from` 包含来源信息：
  - `sender_name`：原发送者
  - `conversation_title`：原对话标题
  - `original_time`：原发送时间

---

### 5. 撤回与删除

#### 撤回消息（对所有人删除，5分钟内）
```http
POST /api/v1/chat/messages/123/unsend
Authorization: Bearer <token>
```

**限制**：
- 只能撤回自己的消息
- 发送后 5 分钟内有效
- 撤回后创建系统通知

**返回**：
```json
{
  "message": "已撤回消息"
}
```

#### 仅对我删除
```http
POST /api/v1/chat/messages/123/delete_for_me
Authorization: Bearer <token>
```

**特性**：
- 消息在 `extra_data.hidden_for_users` 中记录
- 其他人仍可见
- 获取消息时自动过滤

---

### 6. 链接预览

```http
POST /api/v1/chat/link_preview
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://www.example.com"
}
```

**返回**：
```json
{
  "url": "https://www.example.com",
  "title": "示例网站",
  "description": "这是一个示例网站的描述",
  "image": "https://www.example.com/image.jpg",
  "domain": "www.example.com"
}
```

**支持的协议**：
- Open Graph (og:title, og:description, og:image)
- HTML meta 标签
- 自动降级到域名

---

## 🔄 消息列表增强字段

`GET /api/v1/chat/conversations/<id>/messages` 返回的消息对象新增：

```json
{
  "id": 123,
  "content": "消息内容",
  
  // 新增：反应统计
  "reactions": [
    {
      "reaction": "👍",
      "count": 5,
      "users": [1, 2, 3, 4, 5],
      "i_reacted": true  // 我是否已反应
    }
  ],
  
  // 新增：是否置顶
  "is_pinned": false,
  
  // 新增：转发来源
  "forward_from_id": 100,
  
  // 新增：扩展数据
  "extra_data": {
    "mentioned_users": [2, 3],  // 被提及的用户
    "forwarded_from": {  // 转发来源信息
      "sender_name": "张三",
      "conversation_title": "课程群",
      "original_time": "2026-02-01T10:00:00"
    }
  }
}
```

---

## 🎨 前端开发提示

### 消息反应组件
```javascript
// 点击反应按钮
const addReaction = async (messageId, emoji) => {
  const response = await fetch(`/api/v1/chat/messages/${messageId}/reactions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ reaction: emoji })
  });
  
  const data = await response.json();
  
  if (data.action === 'added') {
    // 添加动画效果
  } else if (data.action === 'removed') {
    // 移除效果
  }
};
```

### @ 提及自动补全
```javascript
// 监听输入框
const handleInput = (text) => {
  // 检测 @ 符号
  const atIndex = text.lastIndexOf('@');
  if (atIndex !== -1) {
    const query = text.substring(atIndex + 1);
    
    // 搜索成员
    fetch(`/api/v1/chat/conversations/${convId}/members/search?q=${query}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(members => {
      // 显示下拉菜单
      showMemberList(members);
    });
  }
};
```

### 置顶消息栏
```vue
<template>
  <div v-if="pinnedMessages.length > 0" class="pinned-bar">
    <div v-for="msg in pinnedMessages" :key="msg.pin_id" class="pinned-item">
      <span class="pin-icon">📌</span>
      <span class="content" @click="scrollToMessage(msg.message_id)">
        {{ msg.content }}
      </span>
    </div>
  </div>
</template>
```

---

## 📝 数据库表结构

### MessageReaction（消息反应）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| message_id | BigInteger | 消息ID |
| user_id | BigInteger | 用户ID |
| reaction | String(10) | 表情符号 |
| created_at | DateTime | 创建时间 |

**索引**：
- UNIQUE(message_id, user_id)
- INDEX(message_id, reaction)

### PinnedMessage（置顶消息）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| conversation_id | BigInteger | 对话ID |
| message_id | BigInteger | 消息ID |
| pinned_by | BigInteger | 置顶人 |
| pinned_at | DateTime | 置顶时间 |
| order_index | Integer | 顺序 |

**索引**：
- UNIQUE(conversation_id, message_id)
- INDEX(conversation_id, order_index)

### MentionNotification（提及通知）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| message_id | BigInteger | 消息ID |
| mentioned_user_id | BigInteger | 被提及用户 |
| is_read | Boolean | 是否已读 |
| created_at | DateTime | 创建时间 |

**索引**：
- INDEX(mentioned_user_id, is_read)

---

## ⚠️ 注意事项

1. **消息反应**
   - 每个用户对每条消息只能有一个反应
   - 再次点击相同表情会取消反应
   - 切换不同表情会自动更新

2. **消息置顶**
   - 需要 owner 或 admin 权限
   - 支持多条消息置顶
   - 按 order_index 排序

3. **@ 提及**
   - 只能提及对话内的成员
   - 自动解析 @username 格式
   - 支持用户名和真实姓名

4. **消息转发**
   - 可以一次转发到多个对话
   - 保留原消息所有属性
   - 自动标记来源信息

5. **撤回消息**
   - 5分钟时间限制
   - 只能撤回自己的消息
   - 创建系统通知

6. **链接预览**
   - 5秒超时保护
   - 支持 HTTPS 和 HTTP
   - 失败时返回基本信息

---

## 🔧 故障排查

### 问题：反应没有显示
**检查**：
1. 消息列表是否包含 `reactions` 字段
2. 前端是否正确渲染反应组件

### 问题：@ 提及无法触发
**检查**：
1. 消息内容是否包含 `@username` 格式
2. 被提及用户是否是对话成员
3. `extra_data.mentioned_users` 是否正确存储

### 问题：置顶失败
**检查**：
1. 用户是否有管理员权限
2. 消息是否已被置顶

### 问题：链接预览失败
**检查**：
1. URL 格式是否正确
2. 网站是否可访问
3. 是否被防火墙拦截

---

## 📞 技术支持

- 查看完整文档：[CHAT_NEW_FEATURES_SUMMARY.md](CHAT_NEW_FEATURES_SUMMARY.md)
- 功能分析报告：[CHAT_FEATURE_ANALYSIS.md](CHAT_FEATURE_ANALYSIS.md)
- 测试脚本：`python test_chat_new_features.py`
