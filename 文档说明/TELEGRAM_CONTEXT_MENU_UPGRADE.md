# Telegram 风格右键菜单完全分离升级

## 📋 升级概述

将右键菜单从单一容器设计升级为完全分离的 Telegram 风格，表情栏和功能菜单各自拥有独立的背景、圆角和阴影，并增加智能定位功能。

## 🎯 核心改进

### 1. 结构解耦
- **外层容器透明化**：`context-menu-container` 仅负责定位，background 为 transparent
- **内部元素独立**：`.tg-reaction-bar` 和 `.tg-menu-list` 各自拥有独立的背景和样式
- **10px 间距**：通过 `gap: 10px` 实现视觉分离

### 2. 视觉升级
- **磨砂玻璃效果**：`backdrop-filter: blur(12px) saturate(180%)`
- **深色主题**：`rgba(28, 36, 47, 0.96)` 半透明暗色背景
- **多层阴影**：外阴影 + 内高光，增强立体感
- **独立圆角**：
  - 表情栏：`border-radius: 24px`（更圆润）
  - 菜单列表：`border-radius: 14px`

### 3. 智能定位
- **自动方向检测**：点击屏幕下半部时，菜单自动翻转（`column-reverse`）
- **边界保护**：确保菜单不会超出视口范围
- **动态高度计算**：根据菜单项数量精确计算总高度

## 🔧 技术实现

### HTML 结构
```vue
<div class="context-menu-container" :style="{ flexDirection: contextMenu.direction }">
  <!-- 表情栏：独立背景 -->
  <div class="tg-reaction-bar">
    <span class="tg-emoji-item">👍</span>
    ...
  </div>

  <!-- 菜单列表：独立背景 -->
  <div class="tg-menu-list">
    <div class="tg-menu-item">回复</div>
    ...
  </div>
</div>
```

### JavaScript 核心逻辑
```javascript
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  message: null,
  direction: 'column' // 动态方向控制
})

const showContextMenu = (event, message) => {
  // 智能方向判断
  const isBottomHalf = y > window.innerHeight / 2
  const direction = isBottomHalf ? 'column-reverse' : 'column'
  
  // 根据方向调整y坐标
  if (isBottomHalf) {
    y = Math.max(10, y - totalHeight) // 向上展开
  }
  
  contextMenu.value = { visible: true, x, y, message, direction }
}
```

### CSS 关键样式
```css
/* 外层容器：透明 + 定位 */
.context-menu-container {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column; /* 动态绑定 */
  gap: 10px; /* 分离间距 */
  width: fit-content;
}

/* 表情栏：独立样式 */
.tg-reaction-bar {
  background: rgba(28, 36, 47, 0.96);
  backdrop-filter: blur(12px) saturate(180%);
  border-radius: 24px;
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.3),
    0 2px 8px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* 菜单列表：独立样式 */
.tg-menu-list {
  background: rgba(28, 36, 47, 0.96);
  backdrop-filter: blur(12px) saturate(180%);
  border-radius: 14px;
  box-shadow: 
    0 10px 28px rgba(0, 0, 0, 0.35),
    0 4px 12px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
```

## ✨ 交互细节

### 表情 Hover 效果
- **Scale + TranslateY**：`scale(1.45) translateY(-3px)` 悬浮上升
- **背景淡入**：`rgba(255, 255, 255, 0.15)` 半透明白色
- **Cubic-bezier 缓动**：`cubic-bezier(0.175, 0.885, 0.32, 1.275)` 弹性效果

### 菜单项 Hover 效果
- **Active 缩放**：`scale(0.98)` 点击反馈
- **平滑过渡**：`transition: all 0.18s`
- **危险操作高亮**：`.tg-danger` 红色警告样式

### 弹出动画
- **tg-popup**：从 88% 缩放 + 12px 上移，0.18s 弹出
- **telegramFadeIn/Out**：进入/退出动画，符合 Telegram 原生体验

## 🎨 视觉对比

| 特性 | 旧版设计 | 新版设计 |
|------|---------|---------|
| 容器背景 | 统一深色渐变 | 透明容器 |
| 表情栏 | 嵌套在菜单内 | 独立圆角背景 |
| 间距 | 8px 内部间距 | 10px 外部间隙 |
| 阴影 | 单层阴影 | 多层阴影 + 内高光 |
| 磨砂玻璃 | `blur(10px)` | `blur(12px) saturate(180%)` |
| 智能定位 | 固定向下 | 上下自适应 |

## 📊 尺寸规格

```
外层容器：fit-content（自适应）
├─ 表情栏高度：48px
│  ├─ 表情图标：36×36px (24px 字体)
│  ├─ Padding：8px 14px
│  └─ 圆角：24px
├─ 间隙：10px
└─ 菜单列表
   ├─ 宽度：200px
   ├─ 菜单项高度：40px
   ├─ Padding：6px 0
   └─ 圆角：14px
```

## 🚀 使用场景

### 普通聊天消息
```vue
<div @contextmenu.prevent="showContextMenu($event, message)">
  {{ message.content }}
</div>
```

### 特殊消息类型
- 课堂入口消息：完整菜单支持
- 图片消息：支持预览 + 表情回复
- 系统消息：只显示复制功能

## 🐛 已解决问题

1. ✅ 表情栏和菜单视觉未分离 → 外层容器透明化
2. ✅ 底部点击菜单超出屏幕 → 智能翻转方向
3. ✅ 阴影效果单一 → 多层阴影 + 边框
4. ✅ 磨砂玻璃不够明显 → 增加饱和度 `saturate(180%)`
5. ✅ 表情 hover 不够突出 → 加大缩放 1.45x + 上移

## 📱 兼容性

- ✅ Chrome/Edge 88+（完整支持 backdrop-filter）
- ✅ Firefox 103+（完整支持）
- ✅ Safari 14+（需 -webkit- 前缀）
- ⚠️ IE 11（降级为纯色背景）

## 🔜 未来优化

1. **表情选择器扩展**：点击"更多"按钮显示完整表情面板
2. **键盘导航**：支持 Tab/Arrow 键操作菜单
3. **主题切换**：支持浅色/深色主题动态切换
4. **长按快捷操作**：长按消息直接显示快捷操作
5. **表情搜索**：在扩展面板中支持表情搜索

## 📝 更新日志

**2026-02-02**
- ✅ 外层容器透明化，内部元素独立背景
- ✅ 增加智能定位，屏幕下半部菜单翻转
- ✅ 升级磨砂玻璃效果，增加饱和度
- ✅ 多层阴影 + 内高光，增强立体感
- ✅ 表情 hover 优化，scale 1.45x + translateY(-3px)
- ✅ 菜单项 active 状态缩放反馈

---

**技术架构**：Vue 3 + Element Plus  
**设计灵感**：Telegram Desktop  
**开发者**：Online Teaching Support System Team
