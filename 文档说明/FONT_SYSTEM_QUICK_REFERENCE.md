# 字体系统 UI 设计改进 - 快速使用指南

## 🎨 核心设计体系

### 颜色系统

#### 文字颜色
- `--text-primary: #1E293B` - 主文字（对比度18:1）
- `--text-secondary: #475569` - 次要文字（已优化）
- `--text-tertiary: #94A3B8` - 辅助文字
- `--text-disabled: #CBD5E1` - 禁用状态

#### 主色按钮
- 正常: `--primary-color: #5B7FFF`
- 悬浮: `--primary-dark: #4F46E5`（深一级）
- 激活: `--primary-darker: #4338CA`（最深）

#### 角色标签颜色
```css
.role-badge.student { color: var(--role-student); }  /* 学生 - 蓝 */
.role-badge.teacher { color: var(--role-teacher); }  /* 教师 - 绿 */
.role-badge.admin   { color: var(--role-admin); }    /* 管理员 - 橙 */
```

---

## 📝 字体大小体系

| 变量 | 大小 | 用途 |
|------|------|------|
| `--font-size-xs` | 12px | 辅助文字、标签 |
| `--font-size-sm` | 14px | 小文字、导航项 |
| `--font-size-base` | 16px | 正文、按钮 |
| `--font-size-lg` | 18px | 较大文字 |
| `--font-size-xl` | 20px | 大标题 |
| `--font-size-2xl` | 24px | 更大标题 |
| `--font-size-3xl` | 28px | 特大标题 |
| `--font-size-4xl` | 32px | 超大标题 |

### 使用示例
```vue
<!-- 标题 -->
<h1>{{ title }}</h1>  <!-- 自动应用 var(--font-size-4xl) -->
<p class="text-lg">大段落</p>
<span class="text-sm">小标签</span>
```

---

## ⚖️ 字重体系

| 变量 | 值 | 用途 |
|------|-----|------|
| `--font-weight-normal` | 400 | 常规文字 |
| `--font-weight-medium` | 500 | 按钮、标签 |
| `--font-weight-semibold` | 600 | 子标题 |
| `--font-weight-bold` | 700 | 主标题 |

### 使用示例
```css
.btn { font-weight: var(--font-weight-medium); }
h3 { font-weight: var(--font-weight-semibold); }
h1 { font-weight: var(--font-weight-bold); }
```

---

## 📏 行高体系

| 变量 | 值 | 用途 |
|------|-----|------|
| `--line-height-tight` | 1.4 | 紧凑标题 |
| `--line-height-normal` | 1.6 | 标准正文 |
| `--line-height-relaxed` | 1.8 | 宽松长文本 |

### 使用示例
```css
h1 { line-height: 1.2; }           /* 标题通常更紧凑 */
p { line-height: var(--line-height-normal); }
```

---

## 🎯 按钮样式

### 主按钮 (Primary)
```vue
<button class="btn btn-primary">保存</button>
<button class="btn btn-primary btn-large">大按钮</button>
<button class="btn btn-primary btn-small">小按钮</button>
```

### 次要按钮 (Secondary)
```vue
<button class="btn btn-secondary">取消</button>
```

### 轮廓按钮 (Outline)
```vue
<button class="btn btn-outline">编辑</button>
```

### 危险/成功按钮
```vue
<button class="btn btn-danger">删除</button>
<button class="btn btn-success">确定</button>
```

---

## 🏷️ 标签/徽章

```vue
<span class="badge badge-primary">7</span>
<span class="badge badge-success">完成</span>
<span class="badge badge-warning">处理中</span>
<span class="badge badge-danger">错误</span>
```

### 角色徽章
```vue
<span class="role-badge student">学生</span>
<span class="role-badge teacher">教师</span>
<span class="role-badge admin">管理员</span>
```

---

## 📊 卡片组件

```vue
<div class="card">
  <div class="card-header">
    <h2 class="card-title">标题</h2>
    <p class="card-subtitle">副标题</p>
  </div>
  <div class="card-content">
    <!-- 内容 -->
  </div>
</div>
```

---

## 📋 表单组件

```vue
<div class="form-group">
  <label class="form-label required">姓名</label>
  <input type="text" class="form-input" placeholder="请输入">
  <span class="form-error" v-if="error">{{ error }}</span>
  <span class="form-help">辅助文本</span>
</div>

<div class="form-group">
  <label class="form-label">描述</label>
  <textarea class="form-textarea"></textarea>
</div>
```

---

## ⚠️ 警告框/提示框

```vue
<div class="alert alert-primary">
  <div class="alert-title">提示</div>
  <p>这是一条提示消息</p>
</div>

<div class="alert alert-success">
  <div class="alert-title">成功</div>
  <p>操作成功</p>
</div>

<div class="alert alert-warning">警告信息</div>

<div class="alert alert-danger">错误信息</div>
```

---

## 🔧 布局工具类

### 网格布局
```vue
<div class="grid grid-3">
  <div>项目1</div>
  <div>项目2</div>
  <div>项目3</div>
</div>

<!-- 响应式自适应 -->
<div class="grid grid-auto-fit">
  <div class="card">卡片</div>
  <div class="card">卡片</div>
</div>
```

### 弹性布局
```vue
<div class="flex flex-between">
  <span>左边</span>
  <span>右边</span>
</div>

<div class="flex flex-center gap-md">
  <icon></icon>
  <span>居中对齐</span>
</div>
```

---

## 🎯 间距工具类

### 外边距
```html
<div class="m-lg">四边各 24px 外边距</div>
<div class="mx-auto">水平居中</div>
<div class="m-sm">四边各 8px</div>
```

### 内边距
```html
<div class="p-lg">四边各 24px 内边距</div>
<div class="p-md">四边各 16px</div>
```

### 间隔
```html
<div class="flex gap-lg">
  <div>项目1</div>
  <div>项目2</div>
</div>
```

---

## 🎨 圆角工具类

```html
<div class="rounded-md">8px 圆角</div>
<div class="rounded-lg">12px 圆角</div>
<div class="rounded-full">50% 圆形</div>
```

---

## 💫 阴影工具类

```html
<div class="shadow-sm">小阴影</div>
<div class="shadow-md">中阴影</div>
<div class="shadow-lg">大阴影</div>
```

---

## 📱 响应式设计

### 在不同断点上自动调整
```css
/* 桌面端: 3 列网格 */
.grid-3 { grid-template-columns: repeat(3, 1fr); }

/* 平板端 (≤ 1024px): 2 列 */
@media (max-width: 1024px) {
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
}

/* 手机端 (≤ 768px): 1 列 */
@media (max-width: 768px) {
  .grid-3 { grid-template-columns: 1fr; }
}
```

---

## 🌙 深色主题

所有颜色变量在深色主题下自动调整:
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0F172A;     /* 深色背景 */
    --text-primary: #F1F5F9;   /* 浅色文字 */
    /* ... 其他变量 */
  }
}
```

**无需修改代码，自动适应系统深色模式！**

---

## 🔍 文本截断

```html
<!-- 单行截断 -->
<div class="truncate">很长很长很长的文本会被截断...</div>

<!-- 多行截断 -->
<div class="line-clamp-2">
  这是一段很长的文本，最多显示2行，
  超出部分会被省略号截断...
</div>

<div class="line-clamp-3">最多显示3行</div>
```

---

## 💡 最佳实践

### 1. 使用语义化的 HTML
```vue
<!-- ✅ 好 -->
<h1>主标题</h1>
<h2>子标题</h2>
<p>段落文字</p>

<!-- ❌ 避免 -->
<div class="text-4xl">标题</div>
<div class="text-2xl">子标题</div>
```

### 2. 优先使用 CSS 变量
```css
/* ✅ 好 */
.component {
  color: var(--text-primary);
  font-size: var(--font-size-base);
}

/* ❌ 避免 */
.component {
  color: #1E293B;
  font-size: 16px;
}
```

### 3. 组合使用工具类
```vue
<!-- ✅ 可接受 -->
<div class="flex gap-md p-lg rounded-md shadow-md">
  内容
</div>

<!-- ⚠️ 避免过度 -->
<div class="m-xs p-xs text-xs font-normal">
  过多工具类
</div>
```

### 4. 保持色彩对比度
```vue
<!-- ✅ 好 - 高对比度 -->
<span class="text-primary">正文</span>
<span class="text-secondary">次要文字</span>

<!-- ❌ 避免 - 低对比度 -->
<span style="color: #94A3B8; background: #F1F5F9;">
  难以阅读
</span>
```

---

## 🧪 测试检查清单

- [ ] 所有文字颜色对比度满足 WCAG AA
- [ ] 深色主题可正常切换
- [ ] 响应式设计在各断点正常
- [ ] 按钮在 hover/active 状态有反馈
- [ ] 表单验证状态清晰
- [ ] 加载状态显示正常
- [ ] 空状态提示清晰

---

## 📞 常见问题

### Q: 如何自定义颜色？
A: 修改 `frontend/src/styles/variables.css` 中的 CSS 变量

### Q: 能否只在特定页面使用不同样式？
A: 可以，在组件中使用 `<style scoped>` 覆盖全局样式

### Q: 如何添加新的字体大小？
A: 在 `variables.css` 中添加新变量，然后在 `globals.css` 中创建对应的工具类

### Q: 深色主题不工作怎么办？
A: 检查系统设置或浏览器偏好，使用 DevTools 验证媒体查询

---

## 📚 参考文档

- [主改进完成报告](./FONT_SYSTEM_IMPROVEMENT_COMPLETION.md)
- [UI 设计改进路线图](./UI_DESIGN_IMPROVEMENT_ROADMAP.md)
- [视觉指南](./UI_VISUAL_GUIDE.md)

---

**最后更新**: 2026年1月16日
**维护者**: UI Team
