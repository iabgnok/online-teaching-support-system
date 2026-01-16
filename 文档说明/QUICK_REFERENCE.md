# 📋 UI设计 - 快速参考卡片

## 🎨 颜色代码速查表

### 主要颜色
```
主色        #5B7FFF  rgb(91, 127, 255)   var(--primary-color)
辅助色      #8B5CF6  rgb(139, 92, 246)   var(--accent-color)
成功        #10B981  rgb(16, 185, 129)   var(--success-color)
警告        #F59E0B  rgb(245, 158, 11)   var(--warning-color)
危险        #EF4444  rgb(239, 68, 68)    var(--danger-color)
```

### 背景/中性色
```
页面背景    #F8FAFC  var(--bg-primary)
卡片背景    #FFFFFF  var(--bg-card)
次要背景    #F1F5F9  var(--bg-secondary)
主文字      #1E293B  var(--text-primary)
次文字      #64748B  var(--text-secondary)
三文字      #94A3B8  var(--text-tertiary)
边框色      #E2E8F0  var(--border-color)
浅边框      #F1F5F9  var(--border-light)
```

---

## 📐 间距系统速查表

| 名称 | 值 | 用途 |
|------|-----|------|
| xs | 4px | var(--spacing-xs) | 微小间距 |
| sm | 8px | var(--spacing-sm) | 小间距 |
| md | 16px | var(--spacing-md) | 标准间距 |
| lg | 24px | var(--spacing-lg) | 大间距 |
| xl | 32px | var(--spacing-xl) | 超大间距 |
| 2xl | 48px | var(--spacing-2xl) | 巨大间距 |

---

## 🎨 圆角速查表

| 名称 | 值 | 用途 |
|------|-----|------|
| sm | 4px | var(--radius-sm) | 小元素 |
| md | 8px | var(--radius-md) | 默认/推荐 |
| lg | 12px | var(--radius-lg) | 大元素 |
| xl | 16px | var(--radius-xl) | 超大元素 |

---

## 🌟 阴影速查表

| 名称 | 效果 | 用途 |
|------|------|------|
| sm | 轻微 | var(--shadow-sm) | 边框/分隔 |
| md | 中等 | var(--shadow-md) | 卡片hover |
| lg | 明显 | var(--shadow-lg) | 浮层/弹窗 |
| xl | 强烈 | var(--shadow-xl) | 顶层浮层 |

---

## ⚡ 过渡动画速查表

```
快速    150ms  cubic-bezier(0.4, 0, 0.2, 1)  var(--transition-fast)
标准    250ms  cubic-bezier(0.4, 0, 0.2, 1)  var(--transition-base)
```

**常见用途**:
- Hover效果: `transition: all var(--transition-fast);`
- 页面过渡: `transition: all var(--transition-base);`

---

## 🧩 组件速用指南

### Card组件
```vue
<Card 
  title="标题"
  type="primary"  <!-- default/primary/success/warning/danger -->
  :hoverable="true"
>
  <p>卡片内容</p>
  <template #footer>
    <button>操作</button>
  </template>
</Card>
```

### StatCard组件
```vue
<StatCard 
  icon="📊"
  label="标签文字"
  :value="123"
  type="primary"  <!-- primary/success/warning/danger -->
  :trend="5"      <!-- 可选，显示趋势 -->
/>
```

### Button组件
```vue
<Button 
  variant="primary"    <!-- primary/secondary/success/warning/danger -->
  size="medium"        <!-- small/medium/large -->
  @click="handleClick"
  :icon="'icon'"       <!-- 可选 -->
  :loading="false"     <!-- 可选 -->
  :disabled="false"    <!-- 可选 -->
>
  按钮文字
</Button>
```

---

## 📱 响应式设计断点

| 设备 | 宽度 | 说明 |
|------|------|------|
| 桌面 | 1200px+ | 完整功能 |
| 平板 | 1024-1200px | 网格2列 |
| 手机 | <768px | 侧边栏隐藏 |

---

## 🎯 常用CSS模板

### 卡片样式
```css
.my-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.my-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-color);
}
```

### 按钮样式
```css
.my-button {
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.my-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.my-button:active {
  transform: scale(0.98);
}
```

### 文字样式
```css
.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.caption {
  font-size: 12px;
  color: var(--text-tertiary);
}
```

---

## 📊 颜色使用规范

### 主色 (#5B7FFF)
- ✓ 主要按钮
- ✓ 链接
- ✓ 强调元素
- ✓ 活跃状态

### 成功色 (#10B981)
- ✓ 完成状态
- ✓ 成功提示
- ✓ 确认按钮
- ✓ 正向反馈

### 警告色 (#F59E0B)
- ✓ 待办提醒
- ✓ 需注意
- ✓ 次要操作
- ✓ 进行中状态

### 危险色 (#EF4444)
- ✓ 删除确认
- ✓ 错误提示
- ✓ 禁止操作
- ✓ 负向反馈

---

## 🔤 字体规范

### 标题
- H1: 32px, 700, 行高1.2
- H2: 26px, 700, 行高1.2
- H3: 22px, 600, 行高1.2
- H4: 18px, 600, 行高1.3
- H5: 16px, 600, 行高1.3
- H6: 14px, 600, 行高1.4

### 正文
- 大文本: 16px, 400, 行高1.6
- 正常: 14px, 400, 行高1.6
- 小文本: 12px, 400, 行高1.5
- 极小: 11px, 400, 行高1.4

---

## 🎯 单位转换速查表

| 值 | px | rem | em |
|----|-----|----|----|
| xs | 4px | 0.25rem | - |
| sm | 8px | 0.5rem | - |
| md | 16px | 1rem | 1em |
| lg | 24px | 1.5rem | 1.5em |
| xl | 32px | 2rem | 2em |
| 2xl | 48px | 3rem | 3em |

---

## ✨ 动画效果代码片段

### 上浮效果
```css
.hover-up:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}
```

### 加载旋转
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading {
  animation: spin 0.8s linear infinite;
}
```

### 淡入淡出
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 300ms ease-in;
}
```

### 滑入
```css
@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

.slide-in {
  animation: slideIn 250ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 📝 CSS变量完整清单

### 颜色变量 (8个)
```
--primary-color      主色
--accent-color       辅助色
--success-color      成功色
--warning-color      警告色
--danger-color       危险色
--bg-primary         主背景
--bg-card            卡片背景
--text-primary       主文字
```

### 间距变量 (6个)
```
--spacing-xs         4px
--spacing-sm         8px
--spacing-md         16px
--spacing-lg         24px
--spacing-xl         32px
--spacing-2xl        48px
```

### 效果变量 (10+个)
```
--radius-sm          4px圆角
--radius-md          8px圆角
--shadow-sm          轻阴影
--shadow-md          中阴影
--transition-fast    150ms过渡
--transition-base    250ms过渡
```

---

## 🔗 文件位置速查

| 资源 | 位置 |
|------|------|
| CSS变量 | `src/styles/variables.css` |
| 全局样式 | `src/styles/globals.css` |
| Layout布局 | `src/components/Layout.vue` |
| Card卡片 | `src/components/Card.vue` |
| Button按钮 | `src/components/Button.vue` |
| 首页 | `src/views/Dashboard.vue` |
| 作业 | `src/views/Assignments.vue` |
| 成绩 | `src/views/Grades.vue` |

---

## 📞 快速帮助

**颜色问题** → 查看本表顶部的颜色代码  
**间距问题** → 查看间距系统速查表  
**组件问题** → 查看组件速用指南  
**动画问题** → 查看动画效果代码片段  
**更详细** → 查看 `文档说明/UI_REDESIGN_IMPLEMENTATION.md`  

---

## ⭐ 推荐记住的TOP 5

1. **主色**: `#5B7FFF` 或 `var(--primary-color)`
2. **间距**: `var(--spacing-lg)` (24px)
3. **圆角**: `var(--radius-md)` (8px)
4. **阴影**: `var(--shadow-md)`
5. **过渡**: `var(--transition-base)` (250ms)

---

**打印提示**: 本文档可直接打印使用，便于速查！  
**最后更新**: 2026年1月16日
