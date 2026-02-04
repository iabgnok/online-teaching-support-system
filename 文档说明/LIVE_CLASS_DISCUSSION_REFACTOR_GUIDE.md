# 课堂讨论区UI重构说明

## 重构目标

将课堂的聊天讨论区改造为可折叠、可切换的Telegram风格UI，提供更好的用户体验。

## 核心变更

### 1. 后端变更（已完成）

#### 数据库
- ✅ 添加 `conversation_subtype` 字段到 Conversation 表
- ✅ 将课堂对话类型从 `live_class` 改为 `group` + `conversation_subtype='live_class_discussion'`

#### API变更
- ✅ `api/v1/live_class.py` 第116-126行：创建课堂时，对话类型改为 `conversation_type='group'`，添加 `conversation_subtype='live_class_discussion'`
- ✅ `api/v1/chat.py` 第173-188行：过滤规则更新，隐藏 `conversation_subtype='live_class_discussion'` 的对话

#### 数据迁移
- ✅ 执行 `migrate_live_class_discussion.py` 迁移现有数据

### 2. 前端变更

#### 新组件：CollapsibleDiscussionPanel.vue
- ✅ 创建可折叠的讨论区父容器
- ✅ 实现切换按钮（课堂讨论区 ↔ 班级群聊）
- ✅ 复用Telegram风格聊天UI
- ✅ 角色适配功能：
  - 教师：考勤发布、任务发布、便捷指令
  - 学生：举手功能、参与考勤、提交任务

#### 组件Props
```vue
<CollapsibleDiscussionPanel
  :discussion-conversation-id="discussionConversationId"
  :class-group-conversation-id="classGroupConversationId"
  :role="'teacher'" // 或 'student'
  :current-user-id="currentUserId"
  :class-group-name="classGroupName"
  :total-participants="participantsCount"
  @send-message="handleSendMessage"
  @load-more="handleLoadMore"
  @view-attendance="viewAttendanceDetail"
  @view-task="viewTaskDetail"
  @remind-students="remindStudents"
  @start-attendance="startAttendance"
  @publish-task="publishTask"
  @share-board="shareBoard"
  @do-attendance="doAttendance"
  @submit-task="submitTask"
  @raise-hand="raiseHand"
/>
```

### 3. LiveClass.vue集成步骤

#### 步骤1：导入组件
```vue
import CollapsibleDiscussionPanel from '@/components/CollapsibleDiscussionPanel.vue'

export default {
  components: {
    CollapsibleDiscussionPanel
  },
  // ...
}
```

#### 步骤2：准备数据
```javascript
data() {
  return {
    // ... 现有数据
    discussionConversationId: null,  // 课堂讨论区ID
    classGroupConversationId: null,  // 班级群聊ID
    classGroupName: '',              // 班级群聊名称
  }
}
```

#### 步骤3：获取对话ID
在 `loadClassInfo()` 方法中：
```javascript
loadClassInfo() {
  api.get(`/live-class/${this.lessonId}/info`)
    .then(res => {
      this.classInfo = res.data
      this.discussionConversationId = res.data.conversation_id
      // 获取班级群聊ID（需要添加API）
      this.loadClassGroupInfo(res.data.class_id)
    })
}

loadClassGroupInfo(classId) {
  api.get(`/chat/class/${classId}/group`)
    .then(res => {
      this.classGroupConversationId = res.data.conversation_id
      this.classGroupName = res.data.name
    })
}
```

#### 步骤4：替换模板中的聊天区域
将原来的 `<div class="chat-section telegram-style">...</div>` 替换为：
```vue
<CollapsibleDiscussionPanel
  :discussion-conversation-id="discussionConversationId"
  :class-group-conversation-id="classGroupConversationId"
  :role="'teacher'"
  :current-user-id="currentUserId"
  :class-group-name="classGroupName"
  :total-participants="participantsCount"
  @send-message="handleSendMessage"
  @load-more="handleLoadMore"
  @view-attendance="viewAttendanceDetail"
  @view-task="viewTaskDetail"
  @remind-students="remindStudents"
  @start-attendance="startAttendance"
  @publish-task="publishTask"
  @share-board="shareBoard"
/>
```

#### 步骤5：修改事件处理
```javascript
methods: {
  handleSendMessage({ conversationId, message, chatType }) {
    this.socket.emit('chat_message', {
      conversation_id: conversationId,
      lesson_id: chatType === 'discussion' ? this.lessonId : null,
      user_id: this.currentUserId,
      user_name: this.currentUserName,
      message: message
    })
  },

  handleLoadMore({ conversationId, chatType }) {
    // 加载更多消息
    api.get(`/chat/messages/${conversationId}`, {
      params: { before: this.oldestMessageId, limit: 20 }
    }).then(res => {
      // 添加到对应的消息列表
    })
  },

  // ... 其他事件处理
}
```

### 4. 学生端集成

学生端集成类似，只需将 `role` prop 设置为 `'student'`，并且需要添加举手功能的事件处理：

```vue
<CollapsibleDiscussionPanel
  :role="'student'"
  @raise-hand="handleRaiseHand"
  @do-attendance="handleDoAttendance"
  @submit-task="handleSubmitTask"
  ...
/>
```

```javascript
methods: {
  handleRaiseHand(isRaised) {
    this.socket.emit('raise_hand', {
      lesson_id: this.lessonId,
      user_id: this.currentUserId,
      user_name: this.currentUserName,
      status: isRaised
    })
  },

  handleDoAttendance(msg) {
    // 处理签到
  },

  handleSubmitTask(msg) {
    // 处理任务提交
  }
}
```

## 样式调整

### 画板区域扩展
当讨论区收起时，画板区域应该自动扩展：

```css
.canvas-section {
  flex: 1;
  transition: flex 0.3s ease;
}

.right-panel.collapsed {
  width: 40px;
}

.canvas-section.expanded {
  flex: 1;
  /* 占据更多空间 */
}
```

## API接口需求

### 需要添加的API

#### 1. 获取班级群聊信息
```
GET /chat/class/{class_id}/group
Response: {
  conversation_id: 123,
  name: "软件工程2025秋01班",
  member_count: 45
}
```

#### 2. 发送消息到指定对话（已有，需确认）
```
POST /chat/messages
Body: {
  conversation_id: 123,
  message: "消息内容",
  message_type: "text"
}
```

#### 3. 获取对话历史消息（已有）
```
GET /chat/messages/{conversation_id}?before={message_id}&limit=20
```

## 测试清单

### 教师端测试
- [ ] 收起/展开讨论区，画板正确调整大小
- [ ] 切换到班级群聊，消息正确加载
- [ ] 在课堂讨论区发起考勤，学生能看到
- [ ] 发布任务，学生能看到
- [ ] 分享板书到讨论区
- [ ] 查看考勤详情
- [ ] 查看任务完成列表
- [ ] 提醒未完成学生

### 学生端测试
- [ ] 收起/展开讨论区
- [ ] 切换到班级群聊
- [ ] 举手功能正常工作
- [ ] 看到考勤卡片，能够签到
- [ ] 看到任务卡片，能够提交
- [ ] 接收教师消息
- [ ] 发送消息到讨论区

### Socket.IO事件测试
- [ ] chat_message 事件正确发送和接收
- [ ] raise_hand 事件正确发送
- [ ] attendance_update 事件正确接收
- [ ] task_update 事件正确接收
- [ ] typing 事件正常工作

## 注意事项

1. **消息分离**：课堂讨论区和班级群聊的消息应该分别存储和加载
2. **状态同步**：当切换聊天类型时，需要正确同步状态（如未读数、在线人数）
3. **Socket连接**：需要确保Socket.IO正确订阅两个对话的消息
4. **性能优化**：消息列表应该支持虚拟滚动（如果消息量很大）
5. **错误处理**：网络断开时应该有重连机制

## 后续优化

- [ ] 支持消息搜索
- [ ] 支持文件上传
- [ ] 支持语音消息
- [ ] 支持@提及功能
- [ ] 支持消息引用回复
- [ ] 支持表情反应
- [ ] 消息已读回执
- [ ] 历史消息分页加载优化
