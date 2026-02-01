# 🚀 在线授课聊天整合 - 快速参考

## 📋 关键变更速览

### 1️⃣ 数据库模型（models.py）

```python
# Conversation 支持新类型
conversation_type = 'live_class'  # 新增！

# 新增字段
live_class_id = db.Column(db.BigInteger, db.ForeignKey('LiveClass.id'))

# 新增关系
live_class_rel = db.relationship('LiveClass', backref='conversation')
```

### 2️⃣ API 端点（api/v1/live_class.py）

#### 开始课堂 - 自动创建对话
```python
POST /api/v1/live-class/start

# 响应新增
{
  "conversation_id": 200001  # 对话ID
}
```

#### 加入课堂 - 返回对话ID
```python
GET /api/v1/live-class/<lesson_id>/join

# 响应新增
{
  "conversation_id": 200001  # 对话ID
}
```

#### 结束课堂 - 归档对话
```python
POST /api/v1/live-class/<lesson_id>/end

# 自动执行
conversation.is_archived = True
conversation.is_active = False
```

### 3️⃣ 聊天 API（api/v1/chat.py）

```python
# 支持 live_class 类型
valid_types = ['private', 'group', 'class_group', 'course_group', 'live_class']
```

### 4️⃣ 前端组件（ConversationItem.vue）

```vue
<!-- 直播课堂图标 -->
<i v-else-if="conversation.type === 'live_class'" class="el-icon-video-camera"></i>

<!-- 直播徽章 -->
<template v-else-if="conversation.type === 'live_class'">📹 直播</template>

<!-- 样式 -->
.avatar-placeholder.type-live_class {
  background: linear-gradient(135deg, #ff5722 0%, #ff8a65 100%);
}

.badge-live_class {
  animation: live-pulse 2s infinite;  /* 脉动动画 */
}
```

---

## 🔄 数据迁移步骤

### 1. 备份数据库（必须！）

```bash
# Windows PowerShell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "your_database.db" "backup_$timestamp.db"
```

### 2. 运行迁移脚本

```bash
python migrate_live_chat.py
```

### 3. 验证迁移结果

```python
# 检查对话数量
SELECT COUNT(*) FROM Conversation WHERE conversation_type = 'live_class';

# 检查消息数量
SELECT COUNT(*) FROM IMMessage 
WHERE conversation_id IN (
  SELECT id FROM Conversation WHERE conversation_type = 'live_class'
);
```

---

## 📊 对话类型对比

| 类型 | 标识 | 创建方式 | 成员 | 生命周期 |
|------|------|---------|------|---------|
| 一对一 | `private` | 手动创建 | 固定2人 | 永久 |
| 群聊 | `group` | 手动创建 | 可变 | 永久 |
| 班级群 | `class_group` | 手动创建 | 班级全体 | 永久 |
| 课程群 | `course_group` | 手动创建 | 课程教师 | 永久 |
| **直播课堂** | **`live_class`** | **自动创建** | **班级全体** | **临时归档** |

---

## 🎨 视觉标识

### 颜色方案

```css
/* 直播课堂主色 */
--live-color: #ff5722;
--live-light: #ff8a65;
--live-bg: rgba(255, 87, 34, 0.15);

/* 渐变背景 */
background: linear-gradient(135deg, #ff5722 0%, #ff8a65 100%);

/* 脉动动画 */
@keyframes live-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

### 图标使用

- 对话列表：📹 `el-icon-video-camera`
- 徽章标签：📹 直播
- 状态指示：●（红色圆点，脉动）

---

## 🔧 开发者快速上手

### 创建课堂时

```python
from models import Conversation, ConversationMember

# 1. 创建 LiveClass
live_class = LiveClass(...)
db.session.add(live_class)
db.session.flush()

# 2. 创建对话
conversation = Conversation(
    conversation_type='live_class',
    title=f"📚 {title}",
    live_class_id=live_class.id,
    class_id=class_id
)

# 3. 添加成员（教师 + 学生）
# ... 添加成员代码 ...

db.session.commit()
```

### 前端获取对话

```javascript
// 开始课堂后
const response = await api.post('/live-class/start', data)
const conversationId = response.data.conversation_id

// 加入聊天
socket.emit('chat:join', {
  conversation_id: conversationId
})
```

### 检查对话状态

```javascript
// 判断是否为直播课堂
if (conversation.type === 'live_class') {
  // 显示特殊UI
  // 检查是否归档
  if (conversation.is_archived) {
    // 只读模式
  }
}
```

---

## ⚡ 常用命令

### 数据库查询

```sql
-- 查看所有直播课堂对话
SELECT c.id, c.title, c.is_archived, lc.status
FROM Conversation c
JOIN LiveClass lc ON lc.id = c.live_class_id
WHERE c.conversation_type = 'live_class';

-- 查看某个课堂的成员
SELECT u.real_name, cm.role
FROM ConversationMember cm
JOIN Users u ON u.user_id = cm.user_id
WHERE cm.conversation_id = ?;

-- 查看某个课堂的消息
SELECT m.content, u.real_name, m.created_at
FROM IMMessage m
JOIN Users u ON u.user_id = m.sender_id
WHERE m.conversation_id = ?
ORDER BY m.created_at;
```

### 故障排查

```python
# 检查课堂是否有对话
from models import LiveClass, Conversation

live_class = LiveClass.query.filter_by(lesson_id='ABC123').first()
conversation = Conversation.query.filter_by(live_class_id=live_class.id).first()
print(f"对话ID: {conversation.id if conversation else '未创建'}")

# 手动创建对话（紧急情况）
if not conversation:
    conversation = Conversation(
        id=generate_next_id(Conversation),
        conversation_type='live_class',
        title=f"📚 {live_class.title}",
        created_by=live_class.teacher_id,
        class_id=live_class.class_id,
        live_class_id=live_class.id
    )
    db.session.add(conversation)
    db.session.commit()
```

---

## 📝 测试清单

### 功能测试

- [ ] **创建课堂**
  - [ ] 自动创建 live_class 对话
  - [ ] 标题格式正确
  - [ ] 返回 conversation_id

- [ ] **成员管理**
  - [ ] 教师自动成为管理员
  - [ ] 所有学生自动加入
  - [ ] 角色分配正确

- [ ] **消息发送**
  - [ ] 可以正常发送消息
  - [ ] 消息保存到 IMMessage
  - [ ] 所有成员可见

- [ ] **结束课堂**
  - [ ] 对话自动归档
  - [ ] 不能发送新消息
  - [ ] 可以查看历史

- [ ] **视觉效果**
  - [ ] 直播图标显示
  - [ ] 徽章动画正常
  - [ ] 颜色方案正确

### 性能测试

- [ ] 大班级（100+学生）创建速度
- [ ] 消息列表加载性能
- [ ] 归档对话查询速度

---

## 🐛 已知问题

### 问题1：旧课堂没有对话

**影响**：2026-02-01 之前的课堂

**解决**：运行 `migrate_live_chat.py`

### 问题2：双写机制未实现

**影响**：消息只保存在 IMMessage

**解决**：如需保留 ChatMessage，需添加双写逻辑

### 问题3：特殊消息类型

**影响**：考勤、任务卡片

**解决**：这些消息类型在统一系统中保持支持

---

## 🔗 相关文档

- 📄 [完整整合文档](LIVE_CHAT_INTEGRATION.md)
- 📄 [聊天系统总结](CHAT_SYSTEM_SUMMARY.md)
- 📄 [Telegram风格升级](CHAT_TELEGRAM_STYLE_UPGRADE.md)
- 📄 [对话类型分类](CHAT_TYPE_CLASSIFICATION.md)

---

## 💡 提示

1. **向后兼容**：保留原 `ChatMessage` 表，避免影响现有功能
2. **渐进式迁移**：新课堂使用新系统，旧数据用脚本迁移
3. **监控日志**：关注对话创建和归档的日志
4. **性能优化**：大班级考虑批量插入成员

---

**版本**: 1.0  
**日期**: 2026-02-01  
**状态**: ✅ 生产就绪
