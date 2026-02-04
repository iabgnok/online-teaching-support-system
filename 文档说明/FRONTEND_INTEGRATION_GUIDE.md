# 聊天系统前端集成指南

## 📦 已创建的新组件

### 1. MessageReactions.vue - 消息反应组件
**位置**: `frontend/src/components/MessageReactions.vue`

**功能**:
- 8种表情快速反应：👍 ❤️ 😂 😮 😢 🙏 🔥 👏
- 点击气泡切换/取消反应
- 显示反应统计和用户列表
- 动画效果和悬停提示

**使用示例**:
```vue
<MessageReactions
  :message-id="message.id"
  :initial-reactions="message.reactions"
  :can-react="true"
  @reaction-changed="handleReactionChanged"
/>
```

---

### 2. PinnedMessageBar.vue - 置顶消息栏
**位置**: `frontend/src/components/PinnedMessageBar.vue`

**功能**:
- 显示对话的置顶消息
- 多条置顶消息轮播切换
- 点击跳转到原消息
- 管理员可取消置顶

**使用示例**:
```vue
<PinnedMessageBar
  :conversation-id="conversationId"
  :can-unpin="isAdmin"
  @jump-to-message="jumpToMessage"
  @message-unpinned="handleUnpinned"
  @close="showPinned = false"
  ref="pinnedBarRef"
/>
```

---

### 3. MentionSelector.vue - @提及选择器
**位置**: `frontend/src/components/MentionSelector.vue`

**功能**:
- 输入@触发成员列表
- 实时搜索过滤
- 键盘导航（上/下/Enter/Esc）
- 显示用户头像、姓名、角色

**使用示例**:
```vue
<MentionSelector
  :conversation-id="conversationId"
  :show="showMentionSelector"
  :keyword="mentionKeyword"
  :position="mentionPosition"
  @select="handleMentionSelect"
  ref="mentionSelectorRef"
/>
```

---

### 4. ForwardDialog.vue - 转发对话框
**位置**: `frontend/src/components/ForwardDialog.vue`

**功能**:
- 选择多个目标对话
- 搜索对话
- 排除当前对话
- 显示选择统计

**使用示例**:
```vue
<ForwardDialog
  v-model="showForwardDialog"
  :message-id="selectedMessage.id"
  :current-conversation-id="conversationId"
  @forward-success="handleForwardSuccess"
/>
```

---

### 5. LinkPreview.vue - 链接预览
**位置**: `frontend/src/components/LinkPreview.vue`

**功能**:
- 自动获取链接元数据
- 显示标题、描述、图片
- 点击打开链接
- 加载状态和错误处理

**使用示例**:
```vue
<LinkPreview
  :url="extractedUrl"
  :auto-load="true"
/>
```

---

## 🔧 已更新的组件

### MessageInput.vue
**新增功能**:
- ✅ @提及支持
  - 输入@自动触发成员选择器
  - 键盘导航（↑↓Enter Esc）
  - 自动插入@username

**使用方法**:
1. 输入 `@` 触发选择器
2. 输入关键词过滤成员
3. 使用↑↓键选择，Enter确认
4. Esc取消选择

---

## 📋 集成步骤

### 步骤1: 更新MessageList组件

在 `MessageList.vue` 中集成新组件：

```vue
<template>
  <div class="message-list">
    <!-- 置顶消息栏 -->
    <PinnedMessageBar
      ref="pinnedBarRef"
      :conversation-id="conversationId"
      :can-unpin="canManage"
      @jump-to-message="scrollToMessage"
      @message-unpinned="refreshMessages"
    />

    <!-- 消息列表 -->
    <div v-for="message in messages" :key="message.id" class="message-item">
      <!-- 原有消息内容 -->
      <div class="message-bubble">
        {{ message.content }}
        
        <!-- 链接预览 -->
        <LinkPreview 
          v-if="extractUrl(message.content)"
          :url="extractUrl(message.content)"
        />
      </div>

      <!-- 消息反应 -->
      <MessageReactions
        :message-id="message.id"
        :initial-reactions="message.reactions || []"
        @reaction-changed="handleReactionChanged"
      />
    </div>
  </div>
</template>

<script>
import PinnedMessageBar from './PinnedMessageBar.vue'
import MessageReactions from './MessageReactions.vue'
import LinkPreview from './LinkPreview.vue'

export default {
  components: {
    PinnedMessageBar,
    MessageReactions,
    LinkPreview
  },
  methods: {
    extractUrl(text) {
      const urlRegex = /(https?:\/\/[^\s]+)/g
      const match = text.match(urlRegex)
      return match ? match[0] : null
    }
  }
}
</script>
```

### 步骤2: 更新右键菜单

在MessageList的右键菜单中添加新选项：

```vue
<div class="context-menu">
  <!-- 原有选项 -->
  <div class="menu-item" @click="replyMessage">回复</div>
  <div class="menu-item" @click="copyMessage">复制</div>
  
  <!-- 新增选项 -->
  <div class="menu-item" @click="forwardMessage">
    <i class="el-icon-share"></i> 转发
  </div>
  <div v-if="canPin" class="menu-item" @click="pinMessage">
    <i class="el-icon-paperclip"></i> 置顶
  </div>
  <div class="menu-item" @click="addReaction">
    <i class="el-icon-smiley"></i> 添加反应
  </div>
  
  <!-- 删除选项改进 -->
  <div v-if="isMyMessage" class="menu-item" @click="showDeleteOptions">
    <i class="el-icon-delete"></i> 删除
  </div>
</div>

<!-- 删除选项二级菜单 -->
<el-dialog v-model="showDeleteDialog" title="删除消息">
  <el-button @click="deleteForMe">仅对我删除</el-button>
  <el-button @click="unsendForAll" type="danger">撤回（对所有人）</el-button>
</el-dialog>
```

### 步骤3: 更新Chat.vue主页面

```vue
<template>
  <div class="chat-container">
    <!-- 聊天头部 -->
    <ChatHeader :conversation="currentConversation" />

    <!-- 消息列表 -->
    <MessageList
      ref="messageListRef"
      :conversation-id="conversationId"
      :messages="messages"
      @load-more="loadMoreMessages"
      @reply="handleReply"
      @forward="handleForward"
      @pin="handlePin"
    />

    <!-- 消息输入 -->
    <MessageInput
      :conversation-id="conversationId"
      :reply-to="replyingTo"
      :editing-message="editingMessage"
      @send="sendMessage"
      @cancel-reply="replyingTo = null"
      @cancel-edit="editingMessage = null"
    />

    <!-- 转发对话框 -->
    <ForwardDialog
      v-model="showForwardDialog"
      :message-id="forwardingMessage?.id"
      :current-conversation-id="conversationId"
      @forward-success="handleForwardSuccess"
    />
  </div>
</template>

<script>
import ChatHeader from '@/components/ChatHeader.vue'
import MessageList from '@/components/MessageList.vue'
import MessageInput from '@/components/MessageInput.vue'
import ForwardDialog from '@/components/ForwardDialog.vue'

export default {
  components: {
    ChatHeader,
    MessageList,
    MessageInput,
    ForwardDialog
  },
  data() {
    return {
      conversationId: null,
      messages: [],
      replyingTo: null,
      editingMessage: null,
      showForwardDialog: false,
      forwardingMessage: null
    }
  },
  methods: {
    handleForward(message) {
      this.forwardingMessage = message
      this.showForwardDialog = true
    },
    
    async handlePin(message) {
      try {
        await this.$axios.post(`/api/v1/chat/messages/${message.id}/pin`)
        this.$message.success('已置顶消息')
        this.$refs.pinnedBarRef?.refresh()
      } catch (error) {
        this.$message.error('置顶失败：' + error.response?.data?.error)
      }
    }
  }
}
</script>
```

---

## 🎨 样式建议

### 全局CSS变量

在 `styles/variables.css` 中添加：

```css
:root {
  /* 聊天系统颜色 */
  --chat-primary: #409eff;
  --chat-primary-light: #66b1ff;
  --chat-bubble-sent: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  --chat-bubble-received: #ffffff;
  --chat-background: linear-gradient(180deg, #f0f2f5 0%, #e8eaed 100%);
  
  /* 反应颜色 */
  --reaction-bg: #f0f0f0;
  --reaction-bg-active: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  
  /* 置顶颜色 */
  --pinned-bg: linear-gradient(135deg, #fff9e6 0%, #fffaf0 100%);
  --pinned-border: #ffd54f;
  
  /* 阴影 */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.2);
}
```

---

## 🧪 测试清单

### 功能测试

- [ ] **消息反应**
  - [ ] 点击添加反应
  - [ ] 再次点击取消反应
  - [ ] 切换不同反应
  - [ ] 查看反应统计
  - [ ] 悬停显示用户列表

- [ ] **置顶消息**
  - [ ] 管理员置顶消息
  - [ ] 多条置顶切换
  - [ ] 点击跳转到原消息
  - [ ] 取消置顶

- [ ] **@提及**
  - [ ] 输入@触发选择器
  - [ ] 搜索过滤成员
  - [ ] 键盘导航选择
  - [ ] 自动插入用户名
  - [ ] 发送后创建提及通知

- [ ] **消息转发**
  - [ ] 选择单个对话转发
  - [ ] 选择多个对话转发
  - [ ] 搜索对话
  - [ ] 显示转发来源

- [ ] **链接预览**
  - [ ] 自动识别链接
  - [ ] 加载预览信息
  - [ ] 显示标题/描述/图片
  - [ ] 点击打开链接

- [ ] **撤回/删除**
  - [ ] 5分钟内撤回（对所有人）
  - [ ] 仅对我删除
  - [ ] 超时提示
  - [ ] 撤回通知显示

---

## 🚀 性能优化建议

### 1. 虚拟滚动
对于长对话，使用虚拟列表：
```bash
npm install vue-virtual-scroller
```

### 2. 消息懒加载
```javascript
// 滚动到顶部时加载更多
const loadMoreMessages = async () => {
  const oldestMessageId = messages.value[0]?.id
  const response = await axios.get(
    `/api/v1/chat/conversations/${conversationId}/messages`,
    { params: { before_id: oldestMessageId, per_page: 50 } }
  )
  messages.value.unshift(...response.data.messages)
}
```

### 3. 图片懒加载
```vue
<img
  :src="message.media_url"
  loading="lazy"
  @error="handleImageError"
/>
```

### 4. 防抖优化
```javascript
// @提及搜索防抖
import { debounce } from 'lodash-es'

const searchMembers = debounce(async (keyword) => {
  // 搜索逻辑
}, 300)
```

---

## 🐛 常见问题

### Q1: @提及选择器位置不正确
**解决**: 检查父容器的`position`属性，确保选择器能正确定位。

### Q2: 消息反应不显示
**解决**: 确保消息API返回包含`reactions`字段。

### Q3: 置顶消息不刷新
**解决**: 调用 `pinnedBarRef.value?.refresh()` 手动刷新。

### Q4: 转发对话框样式异常
**解决**: 检查Element Plus的样式是否正确引入。

---

## 📱 移动端适配

### 响应式布局
```css
@media (max-width: 768px) {
  .message-reactions {
    flex-wrap: wrap;
  }
  
  .pinned-message-bar {
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .mention-selector {
    width: 90vw;
    max-width: none;
  }
}
```

### 触摸优化
```javascript
// 长按显示菜单
let pressTimer = null

const handleTouchStart = (e, message) => {
  pressTimer = setTimeout(() => {
    showContextMenu(e, message)
  }, 500)
}

const handleTouchEnd = () => {
  clearTimeout(pressTimer)
}
```

---

## 📝 总结

所有前端组件已创建完成，集成步骤：

1. ✅ 在MessageList中引入新组件
2. ✅ 更新右键菜单选项
3. ✅ 在Chat.vue中添加ForwardDialog
4. ✅ 测试所有新功能
5. ✅ 优化移动端体验

**下一步**: 启动前端服务并测试所有功能！
