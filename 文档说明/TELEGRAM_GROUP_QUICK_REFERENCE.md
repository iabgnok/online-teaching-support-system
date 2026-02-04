# Telegram 式群组功能升级 - 快速参考

## 核心概念对照

| 概念 | Telegram | 你的系统 | 数据库字段 |
|------|----------|----------|-----------|
| 频道 | Channel | `group_subtype='channel'` | `Conversation.group_subtype` |
| 讨论组 | Discussion Group | `group_subtype='discussion'` | `Conversation.group_subtype` |
| 普通群 | Group Chat | `group_subtype='normal'` | `Conversation.group_subtype` |
| 频道帖子 | Channel Post | `root_message_id IS NULL` | `IMMessage.root_message_id` |
| 评论 | Comment | `root_message_id = 主贴ID` | `IMMessage.root_message_id` |
| 引用回复 | Reply | `parent_message_id = 父消息ID` | `IMMessage.parent_message_id` |

---

## 快速实施清单

### ✅ 数据库更改（优先级：高）

```sql
-- 1. 扩展 Conversation 表
ALTER TABLE Conversation ADD group_subtype NVARCHAR(20) DEFAULT 'normal';
ALTER TABLE Conversation ADD linked_discussion_id BIGINT NULL;
ALTER TABLE Conversation ADD linked_channel_id BIGINT NULL;

-- 2. 扩展 IMMessage 表
ALTER TABLE IMMessage ADD root_message_id BIGINT NULL;
ALTER TABLE IMMessage ADD parent_message_id BIGINT NULL;
ALTER TABLE IMMessage ADD comment_count INT DEFAULT 0;

-- 3. 添加索引
CREATE INDEX idx_message_root ON IMMessage(root_message_id) WHERE root_message_id IS NOT NULL;
CREATE INDEX idx_message_parent ON IMMessage(parent_message_id) WHERE parent_message_id IS NOT NULL;
CREATE INDEX idx_conversation_subtype ON Conversation(group_subtype);

-- 4. 添加外键
ALTER TABLE Conversation ADD CONSTRAINT FK_Conversation_LinkedDiscussion 
  FOREIGN KEY (linked_discussion_id) REFERENCES Conversation(id);
  
ALTER TABLE IMMessage ADD CONSTRAINT FK_IMMessage_Root 
  FOREIGN KEY (root_message_id) REFERENCES IMMessage(id);
```

**迁移脚本：** `migrate_telegram_style_groups.py`

---

### ✅ 后端 API 端点（优先级：高）

#### 1. 频道管理
```python
# 创建频道
POST /api/v1/chat/channels
{
  "title": "班级公告",
  "auto_create_discussion": true
}

# 绑定讨论组
POST /api/v1/chat/channels/{id}/bind-discussion
{
  "discussion_id": 123  # 或 "create_new": true
}

# 获取频道详情
GET /api/v1/chat/channels/{id}
```

#### 2. 消息与评论
```python
# 发送频道消息（自动转发到讨论组）
POST /api/v1/chat/conversations/{id}/messages
{
  "content": "新公告",
  "message_type": "text"
}

# 获取频道帖子列表（带评论数）
GET /api/v1/chat/channels/{id}/posts
# 返回: [{ id, content, comment_count, ... }]

# 获取某条消息的评论
GET /api/v1/chat/messages/{msg_id}/comments
# 自动从绑定的讨论组查询

# 发表评论
POST /api/v1/chat/messages/{msg_id}/comments
{
  "content": "我的评论",
  "parent_message_id": 456  # 可选：回复某条评论
}
```

#### 3. 权限检查
```python
def can_post_in_channel(user_id, channel_id):
    member = ConversationMember.query.filter_by(
        conversation_id=channel_id,
        user_id=user_id
    ).first()
    
    conversation = Conversation.query.get(channel_id)
    if conversation.group_subtype == 'channel':
        return member.role in ['owner', 'admin']
    return True
```

**关键文件：** `api/v1/chat.py` + `api/v1/chat_enhanced.py`

---

### ✅ 前端组件改造（优先级：中）

#### 1. 对话列表识别频道
```vue
<!-- ConversationItem.vue -->
<i v-if="conversation.group_subtype === 'channel'" 
   class="el-icon-broadcast channel-icon"></i>

<span v-if="conversation.group_subtype === 'channel'" 
      class="channel-badge">频道</span>
```

#### 2. 消息列表显示评论入口
```vue
<!-- MessageList.vue -->
<div v-if="isChannelMode && !msg.root_message_id" 
     class="comment-bar"
     @click="openComments(msg)">
  <svg class="comment-icon">...</svg>
  <span>{{ msg.comment_count || 0 }} 条评论</span>
</div>
```

#### 3. 引用回复预览
```vue
<div v-if="msg.parent_message" 
     class="reply-preview"
     @click="scrollToMessage(msg.parent_message_id)">
  <div class="reply-line"></div>
  <div class="reply-content">
    <span class="reply-author">{{ msg.parent_message.sender_name }}</span>
    <span class="reply-text">{{ msg.parent_message.content }}</span>
  </div>
</div>
```

#### 4. 讨论模式切换
```vue
<!-- Chat.vue -->
<script>
computed: {
  discussionMode() {
    return !!this.$route.query.rootId;
  },
  
  effectiveConversationId() {
    if (this.discussionMode) {
      return this.currentConversation.linked_discussion_id;
    }
    return this.currentConversationId;
  },
  
  displayMessages() {
    if (this.discussionMode) {
      return this.messages.filter(m => m.root_message_id === this.rootMessageId);
    }
    if (this.isChannelMode) {
      return this.messages.filter(m => !m.root_message_id);
    }
    return this.messages;
  }
}
</script>
```

**关键文件：** `Chat.vue`, `MessageList.vue`, `MessageInput.vue`

---

## 逻辑流程图

### 频道发帖 → 自动转发到讨论组
```
管理员在频道发消息
    ↓
保存到 IMMessage (conversation_id=频道ID, root_message_id=NULL)
    ↓
查找 Channel.linked_discussion_id
    ↓
在讨论组插入副本消息 (conversation_id=讨论组ID, root_message_id=频道消息ID)
    ↓
Socket.IO 推送新消息事件
```

### 用户点击"评论" → 进入讨论区
```
点击频道消息的"评论"按钮
    ↓
路由跳转: /chat?id={讨论组ID}&rootId={消息ID}
    ↓
Chat.vue 检测到 rootId 参数 → 进入 discussionMode
    ↓
显示原帖固定卡片
    ↓
加载评论: WHERE root_message_id = {消息ID}
    ↓
输入框提示: "发表你的评论..."
```

### 普通群引用回复
```
右键消息 → 点击"回复"
    ↓
replyingTo = { id, content, sender_name }
    ↓
输入框上方显示引用预览条
    ↓
发送消息时携带 parent_message_id
    ↓
消息气泡上方显示被引用消息预览（可点击定位）
```

---

## 权限矩阵

| 操作 | 频道 Owner | 频道 Admin | 频道 Member | 讨论组 Member |
|------|-----------|-----------|------------|--------------|
| 发布频道帖子 | ✅ | ✅ | ❌ | ❌ |
| 编辑频道帖子 | ✅ | ✅ | ❌ | ❌ |
| 删除频道帖子 | ✅ | ✅ | ❌ | ❌ |
| 查看评论 | ✅ | ✅ | ✅ | ✅ |
| 发表评论 | ✅ | ✅ | ✅ | ✅ |
| 删除任意评论 | ✅ | ✅ | ❌ | 只能删自己 |
| 绑定讨论组 | ✅ | ❌ | ❌ | ❌ |

---

## SQL 查询速查

### 获取频道帖子（带评论数）
```sql
SELECT 
    m.id, 
    m.content, 
    m.created_at,
    u.real_name AS sender_name,
    COUNT(comments.id) AS comment_count
FROM IMMessage m
LEFT JOIN IMMessage comments ON comments.root_message_id = m.id
LEFT JOIN Users u ON m.sender_id = u.user_id
WHERE m.conversation_id = @channel_id 
  AND m.root_message_id IS NULL
  AND m.is_deleted = 0
GROUP BY m.id, m.content, m.created_at, u.real_name
ORDER BY m.created_at DESC;
```

### 获取某条消息的评论
```sql
SELECT 
    c.id,
    c.content,
    c.created_at,
    c.parent_message_id,  -- 用于嵌套回复
    u.real_name AS sender_name,
    u.avatar AS sender_avatar
FROM IMMessage c
JOIN Conversation ch ON ch.id = @channel_id
LEFT JOIN Users u ON c.sender_id = u.user_id
WHERE c.conversation_id = ch.linked_discussion_id
  AND c.root_message_id = @message_id
  AND c.is_deleted = 0
ORDER BY c.created_at ASC;
```

### 更新评论计数（触发器或定时任务）
```sql
UPDATE IMMessage 
SET comment_count = (
    SELECT COUNT(*) 
    FROM IMMessage comments 
    WHERE comments.root_message_id = IMMessage.id
)
WHERE id = @message_id;
```

---

## Socket.IO 事件定义

### 客户端 → 服务器
```javascript
// 发送消息
socket.emit('send_message', {
  conversation_id: 123,
  content: '消息内容',
  parent_message_id: 456,  // 可选
  root_message_id: 789     // 可选
});

// 进入讨论模式
socket.emit('join_discussion', {
  root_message_id: 789
});
```

### 服务器 → 客户端
```javascript
// 新消息
socket.on('new_message', (data) => {
  // { message: {...}, conversation_id: 123 }
});

// 评论计数更新
socket.on('comment_count_update', (data) => {
  // { message_id: 789, new_count: 15 }
  // 更新频道消息气泡的评论数显示
});

// 消息已读
socket.on('message_read', (data) => {
  // { message_id: 789, reader_id: 456 }
});
```

---

## 前端状态管理

### Vuex Store 结构（建议）
```javascript
// store/chat.js
state: {
  currentConversationId: null,
  discussionMode: {
    active: false,
    rootMessageId: null,
    rootMessage: null
  },
  replyingTo: null,  // { id, content, sender_name }
  conversations: [],
  messages: [],
  messageCache: {}  // 消息缓存，避免重复加载
}

mutations: {
  ENTER_DISCUSSION_MODE(state, { rootMessageId, rootMessage }) {
    state.discussionMode = { active: true, rootMessageId, rootMessage };
  },
  
  EXIT_DISCUSSION_MODE(state) {
    state.discussionMode = { active: false, rootMessageId: null, rootMessage: null };
  },
  
  SET_REPLYING_TO(state, message) {
    state.replyingTo = message;
  },
  
  UPDATE_COMMENT_COUNT(state, { messageId, newCount }) {
    const message = state.messages.find(m => m.id === messageId);
    if (message) {
      message.comment_count = newCount;
    }
  }
}

actions: {
  async openComments({ commit, dispatch }, message) {
    // 加载原始消息
    const rootMessage = await api.get(`/messages/${message.id}`);
    commit('ENTER_DISCUSSION_MODE', {
      rootMessageId: message.id,
      rootMessage: rootMessage.data
    });
    
    // 加载评论
    await dispatch('loadComments', message.id);
    
    // 更新路由
    router.push({ query: { rootId: message.id } });
  }
}
```

---

## 测试检查清单

### 功能测试
- [ ] 创建频道 + 自动创建讨论组
- [ ] 频道消息自动转发到讨论组
- [ ] 点击评论进入讨论区
- [ ] 讨论区显示原帖卡片
- [ ] 发表评论并实时显示
- [ ] 评论计数实时更新
- [ ] 普通群引用回复
- [ ] 点击引用预览定位原消息
- [ ] 退出讨论模式返回频道
- [ ] 权限控制（非管理员无法在频道发帖）

### 边界情况
- [ ] 删除频道帖子，评论如何处理？
- [ ] 讨论组成员不在频道中，能否查看原帖？
- [ ] 评论的评论（嵌套回复）如何显示？
- [ ] 超长评论列表分页加载
- [ ] 网络断开时消息发送失败提示
- [ ] 多人同时评论的并发处理

### 性能测试
- [ ] 1000 条消息加载时间
- [ ] 100 条评论渲染性能
- [ ] 评论计数查询优化（JOIN vs 子查询）
- [ ] Socket.IO 事件频率控制（防止刷屏）

---

## 常见问题 FAQ

### Q1: 频道和讨论组是独立的群组吗？
**A:** 是的。频道和讨论组在数据库中是两条独立的 `Conversation` 记录，通过 `linked_discussion_id` 关联。这种设计允许讨论组独立存在，甚至可以解绑。

### Q2: 讨论组的消息能独立查看吗？
**A:** 可以。讨论组本质上就是一个普通群组，在对话列表中会显示。用户可以直接进入讨论组查看所有评论，不必通过频道入口。

### Q3: 如何区分"评论"和"普通群消息"？
**A:** 通过 `root_message_id` 字段：
- **评论**：`root_message_id` 指向频道消息 ID
- **普通群消息**：`root_message_id` 为 NULL

### Q4: 评论能再评论吗（嵌套回复）？
**A:** 可以。使用 `parent_message_id` 实现链式回复：
- 评论 A（root_message_id=主贴ID, parent_message_id=NULL）
- 回复评论 A（root_message_id=主贴ID, parent_message_id=评论A的ID）

### Q5: 删除频道消息后，评论怎么办？
**A:** 两种策略：
1. **级联删除**：删除主贴时，自动删除所有评论（设置 `is_deleted=True`）
2. **保留评论**：只标记主贴删除，评论保留但显示"原帖已删除"

建议采用策略 1，符合 Telegram 逻辑。

### Q6: 频道能解绑讨论组吗？
**A:** 可以。将 `linked_discussion_id` 设为 NULL 即可。已有的评论消息不受影响，只是后续新帖不再自动转发。

### Q7: 能否对每条消息都创建讨论组？
**A:** 技术上可行，但不推荐。Telegram 采用"一个频道 + 一个共享讨论组"的设计，所有帖子的评论都在同一个群里，通过 `root_message_id` 区分。这样更易管理。

---

## 快速调试命令

### 检查频道绑定关系
```sql
SELECT 
    ch.id AS channel_id,
    ch.title AS channel_title,
    dis.id AS discussion_id,
    dis.title AS discussion_title
FROM Conversation ch
LEFT JOIN Conversation dis ON ch.linked_discussion_id = dis.id
WHERE ch.group_subtype = 'channel';
```

### 查看评论统计
```sql
SELECT 
    m.id,
    m.content,
    m.comment_count AS cached_count,
    (SELECT COUNT(*) FROM IMMessage WHERE root_message_id = m.id) AS actual_count
FROM IMMessage m
WHERE m.conversation_id = @channel_id 
  AND m.root_message_id IS NULL;
```

### 修复评论计数
```sql
UPDATE IMMessage 
SET comment_count = (
    SELECT COUNT(*) 
    FROM IMMessage c 
    WHERE c.root_message_id = IMMessage.id
)
WHERE conversation_id = @channel_id 
  AND root_message_id IS NULL;
```

---

## 下一步行动

1. ✅ **阅读完整方案**：`TELEGRAM_GROUP_UPGRADE_PLAN.md`
2. ⬜ **运行数据库迁移**：`python migrate_telegram_style_groups.py`
3. ⬜ **测试后端 API**：`python test_telegram_groups.py`
4. ⬜ **启动开发服务器**：测试前端组件
5. ⬜ **创建测试数据**：`python create_test_channel.py`
6. ⬜ **验收测试**：按检查清单逐项测试

---

**提示：** 本文档是快速参考，完整设计方案请查看主文档。
