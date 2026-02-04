# 教学群组模块 Telegram 式升级方案

## 📋 项目概述

基于 Telegram 的频道(Channel)和讨论组(Discussion Group)设计理念，升级现有教学群组模块，实现：
1. **频道模式**：管理员单向发布 + 独立讨论区
2. **普通群组**：多人聊天 + 消息引用回复
3. **代码复用**：统一聊天组件，通过参数区分模式

---

## 📊 现状分析

### 已有基础设施 ✅

#### 数据库模型
- ✅ `Conversation` 表 - 对话/群组管理
  - 已有 `conversation_type` 字段支持多种类型
  - 支持 `class_id` 和 `live_class_id` 关联
  
- ✅ `IMMessage` 表 - 统一消息模型
  - 已有 `reply_to_id` 字段（可用于引用回复）
  - 支持多种消息类型和媒体
  - 已支持 Unicode/Emoji
  
- ✅ `ConversationMember` 表 - 成员管理
  - 角色权限系统 (owner/admin/member)
  - 阅读状态追踪
  - 置顶/静音功能

#### 前端组件
- ✅ `Chat.vue` - 主聊天视图
- ✅ `ConversationItem.vue` - 对话列表项
- ✅ `MessageList.vue` - 消息列表
- ✅ `MessageInput.vue` - 消息输入框
- ✅ 已实现右键菜单系统

#### 后端 API
- ✅ `/api/v1/chat/` - 基础聊天 API
- ✅ Socket.IO 实时通信
- ✅ 消息状态追踪系统

### 需要补充的功能 ⚠️

#### 数据库层
1. 群组类型区分 (频道 vs 普通群)
2. 频道-讨论组绑定关系
3. 消息树状关联 (RootMsgID)
4. 评论计数字段

#### 后端层
1. 频道消息自动转发到讨论组
2. 消息过滤 API (按 RootMsgID 筛选)
3. 评论统计接口
4. 权限控制逻辑

#### 前端层
1. 频道消息样式 + 评论入口
2. 引用回复 UI (带点击定位)
3. 讨论视图模式切换
4. 右键菜单功能扩展

---

## 🎯 升级任务大纲

### 阶段一：数据库结构扩展 (1-2天)

#### Task 1.1: 扩展 Conversation 表
```sql
-- 新增字段
ALTER TABLE Conversation 
ADD group_subtype NVARCHAR(20) DEFAULT 'normal';
-- 'normal': 普通群组
-- 'channel': 频道（只有管理员能发帖）
-- 'discussion': 讨论组（用于频道评论）

ALTER TABLE Conversation 
ADD linked_discussion_id BIGINT NULL;
-- 频道绑定的讨论组 ID

ALTER TABLE Conversation
ADD linked_channel_id BIGINT NULL;
-- 讨论组关联的频道 ID（反向关联）

-- 添加外键约束
ALTER TABLE Conversation 
ADD CONSTRAINT FK_Conversation_LinkedDiscussion 
FOREIGN KEY (linked_discussion_id) REFERENCES Conversation(id);

ALTER TABLE Conversation 
ADD CONSTRAINT FK_Conversation_LinkedChannel 
FOREIGN KEY (linked_channel_id) REFERENCES Conversation(id);
```

#### Task 1.2: 扩展 IMMessage 表
```sql
-- 新增字段
ALTER TABLE IMMessage 
ADD root_message_id BIGINT NULL;
-- 用于频道讨论：指向频道中的原始消息

ALTER TABLE IMMessage 
ADD parent_message_id BIGINT NULL;
-- 用于普通群引用：指向被回复的消息（链式）

ALTER TABLE IMMessage
ADD comment_count INT DEFAULT 0;
-- 频道消息的评论总数（冗余字段，提升性能）

-- 添加外键和索引
ALTER TABLE IMMessage 
ADD CONSTRAINT FK_IMMessage_Root 
FOREIGN KEY (root_message_id) REFERENCES IMMessage(id);

ALTER TABLE IMMessage 
ADD CONSTRAINT FK_IMMessage_Parent 
FOREIGN KEY (parent_message_id) REFERENCES IMMessage(id);

CREATE INDEX idx_message_root ON IMMessage(root_message_id) 
WHERE root_message_id IS NOT NULL;

CREATE INDEX idx_message_parent ON IMMessage(parent_message_id) 
WHERE parent_message_id IS NOT NULL;
```

#### Task 1.3: 创建迁移脚本
- 文件：`migrate_telegram_style_groups.py`
- 功能：
  - 为现有群组设置默认 `group_subtype = 'normal'`
  - 检查数据完整性
  - 生成升级报告

---

### 阶段二：后端业务逻辑 (3-4天)

#### Task 2.1: 频道管理 API

**新增接口：**

1. **创建频道** `POST /api/v1/chat/channels`
   ```python
   {
     "title": "班级公告频道",
     "description": "发布重要通知",
     "auto_create_discussion": true,  # 自动创建讨论组
     "class_id": 123  # 可选：关联班级
   }
   ```

2. **绑定讨论组** `POST /api/v1/chat/channels/{channel_id}/bind-discussion`
   ```python
   {
     "discussion_id": 456,  # 现有群组ID
     # 或者
     "create_new": true,
     "discussion_title": "公告讨论区"
   }
   ```

3. **获取频道信息** `GET /api/v1/chat/channels/{channel_id}`
   - 返回频道详情 + 绑定的讨论组信息

#### Task 2.2: 消息发送逻辑增强

**修改文件：** `api/v1/chat.py`

1. **频道发帖权限检查**
   ```python
   def can_post_in_channel(user_id, conversation_id):
       """检查用户是否有权在频道发帖"""
       conversation = Conversation.query.get(conversation_id)
       if conversation.group_subtype != 'channel':
           return True
       
       # 频道只允许 owner 和 admin 发帖
       member = ConversationMember.query.filter_by(
           conversation_id=conversation_id,
           user_id=user_id
       ).first()
       
       return member and member.role in ['owner', 'admin']
   ```

2. **自动转发到讨论组**
   ```python
   def post_channel_message(channel_id, content, sender_id, **kwargs):
       """在频道发消息时自动转发到讨论组"""
       # 1. 保存频道消息
       channel_msg = IMMessage(
           conversation_id=channel_id,
           sender_id=sender_id,
           content=content,
           **kwargs
       )
       db.session.add(channel_msg)
       db.session.flush()
       
       # 2. 查找绑定的讨论组
       channel = Conversation.query.get(channel_id)
       if channel.linked_discussion_id:
           # 3. 在讨论组创建副本（作为评论的"根"）
           discussion_msg = IMMessage(
               conversation_id=channel.linked_discussion_id,
               sender_id=sender_id,
               content=content,
               root_message_id=channel_msg.id,  # 关键：指向频道消息
               message_type='channel_mirror',  # 标记为频道镜像
               extra_data={
                   'channel_id': channel_id,
                   'channel_title': channel.title,
                   'is_mirror': True
               }
           )
           db.session.add(discussion_msg)
       
       db.session.commit()
       return channel_msg
   ```

#### Task 2.3: 评论系统 API

1. **获取频道消息列表（带评论数）** `GET /api/v1/chat/channels/{id}/posts`
   ```python
   def get_channel_posts(channel_id):
       """获取频道帖子，附带评论统计"""
       posts = db.session.query(
           IMMessage,
           func.count(discussion_replies.id).label('comment_count')
       ).outerjoin(
           discussion_replies,
           discussion_replies.root_message_id == IMMessage.id
       ).filter(
           IMMessage.conversation_id == channel_id,
           IMMessage.root_message_id == None,  # 只要主帖
           IMMessage.is_deleted == False
       ).group_by(IMMessage.id).order_by(
           desc(IMMessage.created_at)
       ).all()
       
       return [
           {
               'id': post.id,
               'content': post.content,
               'sender': {...},
               'created_at': post.created_at,
               'comment_count': comment_count,
               'has_comments': comment_count > 0
           }
           for post, comment_count in posts
       ]
   ```

2. **获取消息的评论列表** `GET /api/v1/chat/messages/{msg_id}/comments`
   ```python
   def get_message_comments(message_id):
       """获取某条频道消息的所有评论"""
       # 1. 查找原始消息
       original_msg = IMMessage.query.get(message_id)
       channel = Conversation.query.get(original_msg.conversation_id)
       
       # 2. 从讨论组中查询评论
       comments = IMMessage.query.filter_by(
           conversation_id=channel.linked_discussion_id,
           root_message_id=message_id,
           is_deleted=False
       ).order_by(IMMessage.created_at).all()
       
       return comments
   ```

3. **发表评论** `POST /api/v1/chat/messages/{msg_id}/comments`
   ```python
   {
     "content": "这是我的评论",
     "reply_to_id": 789  # 可选：回复某条评论
   }
   ```

#### Task 2.4: 引用回复功能

**修改消息发送接口：** `POST /api/v1/chat/conversations/{id}/messages`

```python
# 请求体新增参数
{
  "content": "消息内容",
  "parent_message_id": 123,  # 普通群：引用回复
  "root_message_id": 456     # 频道讨论：评论根消息
}

# 业务逻辑
def send_message():
    data = request.json
    parent_id = data.get('parent_message_id')
    
    # 如果是引用回复，验证父消息存在
    if parent_id:
        parent_msg = IMMessage.query.get(parent_id)
        if not parent_msg or parent_msg.conversation_id != conversation_id:
            return jsonify({'error': '无效的父消息'}), 400
    
    # 创建消息...
```

---

### 阶段三：前端界面改造 (4-5天)

#### Task 3.1: 群组类型识别与图标

**修改文件：** `frontend/src/components/ConversationItem.vue`

```vue
<template>
  <div class="conversation-item" :class="itemClasses">
    <div class="avatar-wrapper">
      <!-- 频道图标 -->
      <i v-if="conversation.group_subtype === 'channel'" 
         class="el-icon-broadcast channel-icon"></i>
      <!-- 普通群图标 -->
      <i v-else-if="conversation.type === 'group'" 
         class="el-icon-s-comment"></i>
      <!-- 其他类型... -->
    </div>
    
    <div class="conversation-info">
      <div class="title-row">
        <span class="conv-title">{{ conversation.title }}</span>
        <!-- 频道标识 -->
        <span v-if="conversation.group_subtype === 'channel'" 
              class="channel-badge">频道</span>
      </div>
      <!-- ... -->
    </div>
  </div>
</template>

<style scoped>
.channel-icon {
  color: #3b82f6;
  font-size: 20px;
}

.channel-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
}
</style>
```

#### Task 3.2: 频道消息样式 + 评论入口

**修改文件：** `frontend/src/components/MessageList.vue`

```vue
<template>
  <div class="message-list">
    <div v-for="msg in messages" :key="msg.id" class="message-wrapper">
      <!-- 普通消息气泡 -->
      <div class="message-bubble" :class="messageClasses(msg)">
        <!-- 引用回复预览 -->
        <div v-if="msg.parent_message" 
             class="reply-preview"
             @click="scrollToMessage(msg.parent_message_id)">
          <div class="reply-line"></div>
          <div class="reply-content">
            <span class="reply-author">{{ msg.parent_message.sender_name }}</span>
            <span class="reply-text">{{ truncate(msg.parent_message.content, 50) }}</span>
          </div>
        </div>
        
        <!-- 消息内容 -->
        <div class="message-content" v-html="formatContent(msg.content)"></div>
        
        <!-- 频道消息：评论入口 -->
        <div v-if="isChannelMode && !msg.root_message_id" 
             class="comment-bar"
             @click="openComments(msg)">
          <svg class="comment-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 .97 4.29L2 22l5.71-.97C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.38 0-2.68-.32-3.85-.89l-.27-.15-2.83.48.48-2.83-.15-.27C4.82 14.68 4.5 13.38 4.5 12 4.5 7.86 7.86 4.5 12 4.5S19.5 7.86 19.5 12 16.14 19.5 12 19.5z"/>
          </svg>
          <span v-if="msg.comment_count > 0" class="comment-count">
            {{ msg.comment_count }} 条评论
          </span>
          <span v-else class="comment-hint">发表评论...</span>
        </div>
      </div>
      
      <!-- 时间戳、已读状态等 -->
    </div>
  </div>
</template>

<script>
export default {
  props: {
    conversationId: Number,
    messages: Array,
    isChannelMode: Boolean,  // 是否为频道模式
    rootMessageId: Number    // 讨论模式：根消息ID
  },
  
  methods: {
    openComments(message) {
      // 方法1: 路由跳转
      this.$router.push({
        name: 'Chat',
        params: { id: message.channel_discussion_id },
        query: { rootId: message.id }
      });
      
      // 方法2: 触发事件由父组件处理
      this.$emit('open-comments', message);
    },
    
    scrollToMessage(messageId) {
      const element = document.getElementById(`msg-${messageId}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // 闪烁动画
        element.classList.add('highlight');
        setTimeout(() => element.classList.remove('highlight'), 2000);
      }
    }
  }
}
</script>

<style scoped>
.reply-preview {
  display: flex;
  margin-bottom: 8px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.reply-preview:hover {
  background: rgba(0, 0, 0, 0.06);
}

.reply-line {
  width: 3px;
  background: #3b82f6;
  border-radius: 2px;
  margin-right: 8px;
}

.reply-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reply-author {
  font-weight: 600;
  font-size: 13px;
  color: #3b82f6;
}

.reply-text {
  font-size: 13px;
  color: #6b7280;
}

.comment-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(59, 130, 246, 0.08);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.comment-bar:hover {
  background: rgba(59, 130, 246, 0.15);
  transform: translateX(2px);
}

.comment-icon {
  color: #3b82f6;
}

.comment-count {
  font-weight: 600;
  color: #3b82f6;
  font-size: 13px;
}

.comment-hint {
  color: #9ca3af;
  font-size: 13px;
}

/* 高亮动画 */
@keyframes highlight-pulse {
  0%, 100% { background-color: transparent; }
  50% { background-color: rgba(59, 130, 246, 0.2); }
}

.message-bubble.highlight {
  animation: highlight-pulse 1s ease 2;
}
</style>
```

#### Task 3.3: 讨论视图模式（复用聊天组件）

**修改文件：** `frontend/src/views/Chat.vue`

```vue
<template>
  <div class="chat-window">
    <!-- 左侧对话列表 -->
    <div class="chat-sidebar"><!-- 保持原样 --></div>
    
    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <!-- 讨论模式：显示原帖 -->
      <div v-if="discussionMode" class="discussion-header">
        <button class="btn-back" @click="exitDiscussionMode">
          <i class="el-icon-arrow-left"></i> 返回频道
        </button>
        
        <div class="root-message-card">
          <div class="root-author">
            <img :src="rootMessage.sender.avatar" />
            <span>{{ rootMessage.sender.name }}</span>
            <span class="root-time">{{ formatTime(rootMessage.created_at) }}</span>
          </div>
          <div class="root-content" v-html="formatContent(rootMessage.content)"></div>
        </div>
      </div>
      
      <!-- 消息列表（复用组件） -->
      <MessageList 
        :conversation-id="effectiveConversationId"
        :messages="displayMessages"
        :is-channel-mode="isChannelMode"
        :root-message-id="rootMessageId"
        @open-comments="handleOpenComments"
      />
      
      <!-- 输入框 -->
      <MessageInput 
        :disabled="!canSendMessage"
        :placeholder="inputPlaceholder"
        :reply-to="replyingTo"
        @send="handleSendMessage"
        @cancel-reply="replyingTo = null"
      />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      currentConversationId: null,
      rootMessageId: null,  // 讨论模式的根消息ID
      rootMessage: null,
      replyingTo: null
    }
  },
  
  computed: {
    discussionMode() {
      return !!this.rootMessageId;
    },
    
    isChannelMode() {
      const conv = this.conversations.find(c => c.id === this.currentConversationId);
      return conv?.group_subtype === 'channel';
    },
    
    effectiveConversationId() {
      // 讨论模式下切换到讨论组ID
      if (this.discussionMode && this.currentConversation?.linked_discussion_id) {
        return this.currentConversation.linked_discussion_id;
      }
      return this.currentConversationId;
    },
    
    displayMessages() {
      if (this.discussionMode) {
        // 只显示该主题的评论
        return this.messages.filter(m => m.root_message_id === this.rootMessageId);
      }
      // 频道模式：只显示主贴（没有 root_message_id）
      if (this.isChannelMode) {
        return this.messages.filter(m => !m.root_message_id);
      }
      // 普通群：显示全部
      return this.messages;
    },
    
    canSendMessage() {
      if (this.discussionMode) {
        return true;  // 讨论区所有人都能发言
      }
      if (this.isChannelMode) {
        // 频道只有管理员能发帖
        return this.currentMemberRole in ['owner', 'admin'];
      }
      return true;
    },
    
    inputPlaceholder() {
      if (this.discussionMode) {
        return '发表你的评论...';
      }
      if (this.isChannelMode && !this.canSendMessage) {
        return '只有管理员可以在频道发布内容';
      }
      return '输入消息...';
    }
  },
  
  watch: {
    '$route.query.rootId': {
      immediate: true,
      handler(newRootId) {
        if (newRootId) {
          this.enterDiscussionMode(parseInt(newRootId));
        } else {
          this.exitDiscussionMode();
        }
      }
    }
  },
  
  methods: {
    async enterDiscussionMode(rootMessageId) {
      this.rootMessageId = rootMessageId;
      // 加载原始消息
      const res = await api.get(`/api/v1/chat/messages/${rootMessageId}`);
      this.rootMessage = res.data;
      // 加载评论
      await this.loadComments(rootMessageId);
    },
    
    exitDiscussionMode() {
      this.rootMessageId = null;
      this.rootMessage = null;
      this.$router.replace({ query: {} });
    },
    
    handleOpenComments(message) {
      this.$router.push({
        query: { rootId: message.id }
      });
    },
    
    async handleSendMessage(content) {
      const payload = {
        content,
        conversation_id: this.effectiveConversationId
      };
      
      if (this.discussionMode) {
        payload.root_message_id = this.rootMessageId;
      }
      
      if (this.replyingTo) {
        payload.parent_message_id = this.replyingTo.id;
      }
      
      await api.post(`/api/v1/chat/conversations/${this.effectiveConversationId}/messages`, payload);
      this.replyingTo = null;
    }
  }
}
</script>

<style scoped>
.discussion-header {
  border-bottom: 1px solid #e5e7eb;
  padding: 16px;
  background: #f9fafb;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}

.btn-back:hover {
  background: #e5e7eb;
  color: #111827;
}

.root-message-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.root-author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.root-author img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.root-content {
  font-size: 15px;
  line-height: 1.6;
  color: #111827;
}
</style>
```

#### Task 3.4: 右键菜单功能扩展

**修改文件：** `frontend/src/components/MessageList.vue`

```vue
<script>
export default {
  methods: {
    showMessageContextMenu(message, event) {
      event.preventDefault();
      
      const menuItems = [];
      
      // 普通群：回复功能
      if (!this.isChannelMode || this.discussionMode) {
        menuItems.push({
          label: '回复',
          icon: 'el-icon-chat-round',
          action: () => this.replyToMessage(message)
        });
      }
      
      // 频道：查看讨论
      if (this.isChannelMode && !this.discussionMode) {
        menuItems.push({
          label: `查看 ${message.comment_count || 0} 条评论`,
          icon: 'el-icon-chat-dot-square',
          action: () => this.$emit('open-comments', message)
        });
      }
      
      // 其他功能：编辑、删除、转发...
      menuItems.push(
        { label: '复制', icon: 'el-icon-document-copy', action: () => this.copyMessage(message) },
        { label: '转发', icon: 'el-icon-share', action: () => this.forwardMessage(message) },
        { divider: true },
        { label: '删除', icon: 'el-icon-delete', danger: true, action: () => this.deleteMessage(message) }
      );
      
      this.contextMenu = {
        visible: true,
        x: event.clientX,
        y: event.clientY,
        items: menuItems
      };
    },
    
    replyToMessage(message) {
      this.$emit('reply-to', {
        id: message.id,
        content: message.content,
        sender_name: message.sender.name
      });
    }
  }
}
</script>
```

#### Task 3.5: 消息输入框引用状态

**修改文件：** `frontend/src/components/MessageInput.vue`

```vue
<template>
  <div class="message-input-container">
    <!-- 引用回复预览条 -->
    <transition name="slide-up">
      <div v-if="replyTo" class="reply-banner">
        <div class="reply-info">
          <i class="el-icon-back reply-icon"></i>
          <div class="reply-details">
            <span class="reply-to-user">回复 {{ replyTo.sender_name }}</span>
            <span class="reply-to-content">{{ truncate(replyTo.content, 60) }}</span>
          </div>
        </div>
        <button class="btn-cancel-reply" @click="$emit('cancel-reply')">
          <i class="el-icon-close"></i>
        </button>
      </div>
    </transition>
    
    <!-- 输入框 -->
    <div class="input-wrapper">
      <el-input
        v-model="message"
        type="textarea"
        :placeholder="placeholder"
        :disabled="disabled"
        :autosize="{ minRows: 1, maxRows: 6 }"
        @keydown.enter.exact="handleSend"
      />
      <button class="btn-send" :disabled="!canSend" @click="handleSend">
        <i class="el-icon-s-promotion"></i>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    replyTo: Object,  // { id, content, sender_name }
    disabled: Boolean,
    placeholder: { type: String, default: '输入消息...' }
  },
  
  data() {
    return {
      message: ''
    };
  },
  
  computed: {
    canSend() {
      return this.message.trim().length > 0 && !this.disabled;
    }
  },
  
  methods: {
    handleSend() {
      if (!this.canSend) return;
      
      this.$emit('send', {
        content: this.message,
        parent_message_id: this.replyTo?.id
      });
      
      this.message = '';
    }
  }
}
</script>

<style scoped>
.reply-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.05));
  border-left: 3px solid #3b82f6;
}

.reply-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.reply-icon {
  color: #3b82f6;
  font-size: 18px;
  transform: rotate(180deg);
}

.reply-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reply-to-user {
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
}

.reply-to-content {
  font-size: 12px;
  color: #6b7280;
}

.btn-cancel-reply {
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #9ca3af;
  transition: color 0.2s;
}

.btn-cancel-reply:hover {
  color: #ef4444;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
```

---

### 阶段四：权限与安全 (1-2天)

#### Task 4.1: 权限管理器

**新建文件：** `permission_manager.py` (已存在，需扩展)

```python
class ConversationPermissions:
    """对话权限管理"""
    
    @staticmethod
    def can_post(user_id, conversation_id):
        """检查用户能否在对话中发帖"""
        conversation = Conversation.query.get(conversation_id)
        member = ConversationMember.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            left_at=None
        ).first()
        
        if not member:
            return False
        
        # 频道：只有管理员能发帖
        if conversation.group_subtype == 'channel':
            return member.role in ['owner', 'admin']
        
        # 普通群/讨论组：所有成员都能发言
        return True
    
    @staticmethod
    def can_view_conversation(user_id, conversation_id):
        """检查用户能否查看对话"""
        member = ConversationMember.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id
        ).first()
        return member is not None
    
    @staticmethod
    def can_manage_channel(user_id, channel_id):
        """检查用户能否管理频道（绑定讨论组等）"""
        member = ConversationMember.query.filter_by(
            conversation_id=channel_id,
            user_id=user_id,
            left_at=None
        ).first()
        return member and member.role == 'owner'
```

#### Task 4.2: API 接口权限装饰器

```python
from functools import wraps
from flask import g, jsonify

def require_conversation_access(f):
    """要求用户有对话访问权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conversation_id = kwargs.get('conversation_id')
        if not ConversationPermissions.can_view_conversation(g.user.user_id, conversation_id):
            return jsonify({'error': '无权访问该对话'}), 403
        return f(*args, **kwargs)
    return decorated_function

def require_post_permission(f):
    """要求用户有发帖权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conversation_id = kwargs.get('conversation_id') or request.json.get('conversation_id')
        if not ConversationPermissions.can_post(g.user.user_id, conversation_id):
            return jsonify({'error': '无权在此发帖'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

---

### 阶段五：测试与优化 (2-3天)

#### Task 5.1: 单元测试

**新建文件：** `test_telegram_groups.py`

```python
import unittest
from app import create_app, db
from models import Conversation, IMMessage, ConversationMember, Users

class TelegramGroupTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_channel_with_discussion(self):
        """测试创建频道并自动绑定讨论组"""
        # 创建用户
        admin = Users(username='admin', role='admin')
        db.session.add(admin)
        db.session.commit()
        
        # 创建频道
        channel = Conversation(
            title='测试频道',
            conversation_type='group',
            group_subtype='channel',
            created_by=admin.user_id
        )
        db.session.add(channel)
        db.session.flush()
        
        # 创建讨论组
        discussion = Conversation(
            title=f'{channel.title} 讨论区',
            conversation_type='group',
            group_subtype='discussion',
            created_by=admin.user_id,
            linked_channel_id=channel.id
        )
        db.session.add(discussion)
        db.session.flush()
        
        # 绑定
        channel.linked_discussion_id = discussion.id
        db.session.commit()
        
        # 验证
        self.assertIsNotNone(channel.linked_discussion_id)
        self.assertEqual(discussion.linked_channel_id, channel.id)
    
    def test_channel_message_auto_forward(self):
        """测试频道消息自动转发到讨论组"""
        # ... 完整测试逻辑
    
    def test_comment_count_update(self):
        """测试评论计数更新"""
        # ... 完整测试逻辑
```

#### Task 5.2: 性能优化

1. **数据库查询优化**
   - 为 `root_message_id` 和 `parent_message_id` 添加索引 ✅
   - 使用 JOIN 查询减少 N+1 问题
   - 评论计数缓存策略

2. **前端渲染优化**
   - 虚拟滚动（处理超长消息列表）
   - 图片懒加载
   - 消息分页加载

3. **Socket.IO 事件优化**
   ```python
   # 新评论实时推送
   @socketio.on('new_comment')
   def handle_new_comment(data):
       message_id = data['root_message_id']
       # 更新频道消息的评论计数
       emit('comment_count_update', {
           'message_id': message_id,
           'new_count': get_comment_count(message_id)
       }, room=f'channel_{channel_id}')
   ```

#### Task 5.3: 用户体验细节

1. **骨架屏加载**
2. **消息发送失败重试**
3. **离线消息同步**
4. **评论区滚动位置记忆**
5. **键盘快捷键（Esc 退出讨论模式）**

---

## 📅 实施时间表

| 阶段 | 任务 | 预计时间 | 负责人 | 状态 |
|------|------|---------|--------|------|
| 一 | 数据库结构扩展 | 1-2天 | - | 待开始 |
| 二 | 后端业务逻辑 | 3-4天 | - | 待开始 |
| 三 | 前端界面改造 | 4-5天 | - | 待开始 |
| 四 | 权限与安全 | 1-2天 | - | 待开始 |
| 五 | 测试与优化 | 2-3天 | - | 待开始 |
| **总计** | - | **11-16天** | - | - |

---

## 🎁 额外功能建议（可选）

### 1. 频道统计面板
- 总订阅人数
- 平均评论数
- 热门帖子排行

### 2. 评论过滤与排序
- 按时间/热度排序
- 只看作者回复
- 关键词搜索

### 3. 消息置顶与公告
- 频道可置顶重要公告
- 讨论组可置顶精华评论

### 4. 通知优化
- 频道新帖推送
- 被回复时通知
- @提及通知

### 5. 富文本支持
- Markdown 渲染
- 代码高亮
- LaTeX 公式

---

## ⚠️ 注意事项

### 数据迁移风险
- ✅ 新增字段均有默认值，不影响旧数据
- ✅ 外键约束允许 NULL
- ⚠️ 大表迁移需要评估锁表时间

### 兼容性考虑
- 旧客户端如何处理频道消息？
- API 版本兼容策略
- 数据库回滚方案

### 用户引导
- 新功能使用教程
- 管理员培训文档
- 常见问题 FAQ

---

## 📊 成功指标

1. **功能完整性**
   - [ ] 频道创建与管理
   - [ ] 讨论组自动绑定
   - [ ] 评论系统正常运作
   - [ ] 引用回复功能

2. **性能指标**
   - 消息加载时间 < 200ms
   - 评论计数查询 < 50ms
   - 实时推送延迟 < 100ms

3. **用户体验**
   - UI 响应流畅（60fps）
   - 交互逻辑符合直觉
   - 错误提示清晰

---

## 📚 参考文档

- [Telegram API Documentation](https://core.telegram.org/bots/api)
- [Flask-SocketIO Real-time Events](https://flask-socketio.readthedocs.io/)
- [Vue Router Query Parameters](https://router.vuejs.org/guide/essentials/passing-props.html)
- [SQL Server Index Optimization](https://docs.microsoft.com/en-us/sql/relational-databases/indexes/)

---

## 🚀 快速开始

### Step 1: 运行数据库迁移
```bash
python migrate_telegram_style_groups.py
```

### Step 2: 创建测试频道
```bash
python create_test_channel.py
```

### Step 3: 启动开发服务器
```bash
# 后端
python app.py

# 前端
cd frontend
npm run dev
```

### Step 4: 访问测试页面
- 频道列表：`http://localhost:3000/chat?type=channel`
- 创建频道：`http://localhost:3000/chat/new-channel`

---

**最后更新：** 2026-02-03  
**文档版本：** v1.0  
**维护者：** GitHub Copilot
