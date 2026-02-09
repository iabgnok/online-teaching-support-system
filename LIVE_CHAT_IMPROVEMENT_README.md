# 直播聊天模块改进

## 📋 概述

本次改进主要针对教学支持系统的直播聊天模块，实现了以下目标：

1. **组件化聊天UI** - 课堂聊天模块使用统一的聊天组件
2. **独立切换按钮** - 创建专门的聊天切换按钮组件
3. **提升用户体验** - 优化界面设计和交互体验

## 🎯 主要改进

### 1. 新增组件

#### `ChatSwitchButton.vue`
- **位置**: `src/components/live-class/ChatSwitchButton.vue`
- **功能**: 专门的聊天标签切换按钮
- **特性**:
  - 支持未读消息数量显示
  - 活跃状态指示器
  - 响应式设计
  - 自定义图标插槽

#### `LiveClassChatPanel.vue`
- **位置**: `src/components/live-class/LiveClassChatPanel.vue`
- **功能**: 整合的直播聊天面板
- **特性**:
  - 集成ChatWindow组件
  - 多标签切换支持
  - 在线状态显示
  - 折叠/展开控制

### 2. 增强组件

#### `ChatWindow.vue` 增强
- 添加直播模式支持 (`isLiveMode` prop)
- 支持隐藏头部 (`hideHeader` prop)
- 增强事件处理 (回复、编辑、删除等)
- 直播场景样式优化

#### `LiveRoom.vue` 更新
- 集成新的 `LiveClassChatPanel` 组件
- 添加完整的聊天相关props
- 增强事件处理支持

### 3. 组件导出

更新 `src/components/live-class/index.js` 导出新组件：

```javascript
export { default as LiveClassChatPanel } from './LiveClassChatPanel.vue'
export { default as ChatSwitchButton } from './ChatSwitchButton.vue'
```

## 🚀 使用方法

### 基本用法

```vue
<template>
  <LiveClassChatPanel
    :discussion-conversation-id="discussionId"
    :class-group-conversation-id="classGroupId"
    :role="userRole"
    :online-count="onlineCount"
    :discussion-unread="discussionUnread"
    :class-group-unread="classGroupUnread"
    @switch-tab="handleTabSwitch"
    @send-message="handleSendMessage"
    @toggle-collapse="handleToggleCollapse"
  />
</template>

<script>
import { LiveClassChatPanel } from '@/components/live-class'

export default {
  components: {
    LiveClassChatPanel
  },
  // ... 其他代码
}
</script>
```

### 单独使用切换按钮

```vue
<template>
  <ChatSwitchButton
    tab-type="discussion"
    label="课堂讨论"
    :unread-count="unreadCount"
    :is-active="activeTab === 'discussion'"
    @switch="activeTab = $event"
  />
</template>

<script>
import { ChatSwitchButton } from '@/components/live-class'

export default {
  components: {
    ChatSwitchButton
  },
  // ... 其他代码
}
</script>
```

## 📋 Props 说明

### LiveClassChatPanel Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `discussionConversationId` | Number/String | null | 课堂讨论对话ID |
| `classGroupConversationId` | Number/String | null | 班级群对话ID |
| `role` | String | 'student' | 用户角色 |
| `isOnline` | Boolean | true | 是否在线 |
| `onlineCount` | Number | 0 | 在线人数 |
| `isCollapsed` | Boolean | false | 是否折叠 |
| `discussionLabel` | String | '课堂讨论' | 讨论标签文本 |
| `classGroupLabel` | String | '班级群聊' | 班级群标签文本 |
| `discussionUnread` | Number | 0 | 讨论未读数 |
| `classGroupUnread` | Number | 0 | 班级群未读数 |

### ChatSwitchButton Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `tabType` | String | - | 标签类型 ('discussion', 'classGroup', 'private') |
| `label` | String | - | 按钮标签文本 |
| `unreadCount` | Number | 0 | 未读消息数量 |
| `isActive` | Boolean | false | 是否为活跃状态 |
| `disabled` | Boolean | false | 是否禁用 |

## 🎉 Events 说明

### LiveClassChatPanel Events

- `switch-tab`: 切换标签时触发
- `send-message`: 发送消息时触发
- `load-more`: 加载更多消息时触发
- `reply`: 回复消息时触发
- `edit`: 编辑消息时触发
- `delete`: 删除消息时触发
- `open-comments`: 打开评论时触发
- `react`: 消息反应时触发
- `pin`: 置顶消息时触发
- `toggle-collapse`: 切换折叠状态时触发

### ChatSwitchButton Events

- `switch`: 点击切换按钮时触发

## 🎨 样式特性

### 响应式设计
- 支持移动端和桌面端
- 自适应屏幕尺寸

### 动画效果
- 平滑的切换动画
- 未读消息脉冲效果
- 折叠/展开过渡

### 主题适配
- 支持深色/浅色主题
- 统一的颜色系统
- 一致的圆角和阴影

## 📁 文件结构

```
src/components/live-class/
├── ChatSwitchButton.vue      # 聊天切换按钮组件
├── LiveClassChatPanel.vue    # 直播聊天面板组件
├── LiveRoom.vue             # 直播房间主组件 (更新)
├── LiveClassChat.vue        # 原聊天组件 (保留)
├── index.js                 # 组件导出文件 (更新)
└── ...其他组件

src/components/chat/
├── ChatWindow.vue           # 聊天窗口组件 (增强)
├── MessageList.vue          # 消息列表组件
├── MessageInput.vue         # 消息输入组件
└── ...其他组件
```

## 🧪 测试和演示

### 在线演示
打开 `frontend/live-chat-demo.html` 查看组件演示

### 功能测试
1. 标签切换功能
2. 未读消息显示
3. 折叠/展开功能
4. 消息发送和接收
5. 响应式布局

## 🔧 技术栈

- **Vue 3**: Composition API
- **Element Plus**: UI组件库
- **SCSS**: 样式预处理器
- **Vite**: 构建工具

## 📈 性能优化

- 组件懒加载
- 虚拟滚动 (消息列表)
- 事件防抖
- 内存泄漏防护

## 🎯 后续计划

1. **实时通信集成** - 集成WebSocket/Socket.io
2. **消息搜索功能** - 添加消息搜索和过滤
3. **文件分享** - 支持文件和图片分享
4. **语音消息** - 添加语音消息功能
5. **消息翻译** - 多语言消息翻译

---

## 📞 技术支持

如有问题或建议，请联系开发团队。