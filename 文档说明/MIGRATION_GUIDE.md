# 🔄 页面迁移指南 - 如何适配新UI设计

## 概述

本指南说明如何将现有的页面组件迁移到新的UI设计系统。通过遵循这些步骤，可以快速将任何页面转换为新的视觉风格。

---

## 📋 迁移清单

### 必要步骤
- [ ] 使用新Layout组件
- [ ] 导入新的全局样式
- [ ] 替换颜色硬编码为CSS变量
- [ ] 使用新的组件库
- [ ] 更新元素间距
- [ ] 测试响应式显示

---

## 🚀 快速开始 (5分钟)

### 第1步: 基础设置

确保你的页面使用了新的Layout组件（自动完成）：

```javascript
// src/App.vue 已自动使用
import Layout from './components/Layout.vue'
// Layout会根据路由自动显示/隐藏
```

### 第2步: 导入组件

```javascript
// 在你的 .vue 页面中
import Card from '@/components/Card.vue'
import Button from '@/components/Button.vue'
import StatCard from '@/components/StatCard.vue'
```

### 第3步: 使用CSS变量

```css
/* ❌ 旧方式 */
.my-container {
  background-color: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  color: #333;
}

/* ✅ 新方式 */
.my-container {
  background-color: var(--bg-card);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  color: var(--text-primary);
}
```

### 第4步: 运行测试

```bash
npm run dev
# 打开 http://localhost:5177
# 检查布局、颜色、间距
```

---

## 🎨 常见迁移场景

### 场景1: 简单的列表页面

#### 原始代码
```vue
<template>
  <div class="page">
    <h1>{{ title }}</h1>
    <div class="items-list">
      <div v-for="item in items" :key="item.id" class="item">
        {{ item.name }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 20px;
  background: #f5f7fa;
}
.items-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}
.item {
  background: white;
  padding: 15px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
```

#### 迁移后的代码
```vue
<template>
  <div class="page">
    <h1>{{ title }}</h1>
    <div class="items-list">
      <Card 
        v-for="item in items" 
        :key="item.id"
        :title="item.name"
      >
        <p>{{ item.description }}</p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import Card from '@/components/Card.vue'

defineProps({
  title: String,
  items: Array
})
</script>

<style scoped>
.page {
  padding: var(--spacing-lg);
  background-color: var(--bg-primary);
}

.items-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}
</style>
```

**改进**:
- 使用Card组件替代div
- 使用CSS变量
- 少了3行CSS代码
- 自动支持hover效果

---

### 场景2: 数据表格页面

#### 原始代码
```vue
<template>
  <el-table :data="tableData" stripe>
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="status" label="状态">
      <template #default="{ row }">
        <el-tag :type="row.status === '完成' ? 'success' : 'info'">
          {{ row.status }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作">
      <template #default="{ row }">
        <el-button link type="primary" @click="edit(row)">编辑</el-button>
        <el-button link type="danger" @click="delete(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
```

#### 迁移后的代码
```vue
<template>
  <Card title="数据列表">
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in tableData" :key="item.id">
            <td>{{ item.name }}</td>
            <td>
              <span class="status-badge" :class="item.status">
                {{ item.status }}
              </span>
            </td>
            <td>
              <Button size="small" variant="secondary" @click="edit(item)">
                编辑
              </Button>
              <Button size="small" variant="danger" @click="deleteItem(item)">
                删除
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/Card.vue'
import Button from '@/components/Button.vue'
</script>

<style scoped>
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 2px solid var(--border-color);
}

.data-table td {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-light);
}

.data-table tbody tr:hover {
  background-color: var(--bg-secondary);
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
}

.status-badge.success {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--success-color);
}

.status-badge.pending {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--warning-color);
}
</style>
```

**改进**:
- 使用Card包装
- 使用新的Button组件
- 自定义样式使用CSS变量
- 支持hover高亮
- 代码更清晰

---

### 场景3: 表单页面

#### 原始代码
```vue
<template>
  <el-form :model="form" label-width="120px">
    <el-form-item label="名称">
      <el-input v-model="form.name" />
    </el-form-item>
    <el-form-item label="描述">
      <el-input v-model="form.description" type="textarea" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="submit">提交</el-button>
      <el-button @click="reset">重置</el-button>
    </el-form-item>
  </el-form>
</template>
```

#### 迁移后的代码
```vue
<template>
  <Card title="编辑信息">
    <form @submit.prevent="submit" class="form">
      <div class="form-group">
        <label for="name">名称 <span class="required">*</span></label>
        <input 
          id="name" 
          v-model="form.name" 
          type="text"
          class="form-input"
          required
        />
      </div>

      <div class="form-group">
        <label for="description">描述</label>
        <textarea 
          id="description" 
          v-model="form.description"
          class="form-input"
          rows="4"
        ></textarea>
      </div>

      <div class="form-actions">
        <Button variant="primary" @click="submit">提交</Button>
        <Button variant="secondary" @click="reset">重置</Button>
      </div>
    </form>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import Card from '@/components/Card.vue'
import Button from '@/components/Button.vue'

const form = ref({
  name: '',
  description: ''
})

const submit = () => {
  // 提交逻辑
}

const reset = () => {
  form.value = { name: '', description: '' }
}
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.required {
  color: var(--danger-color);
}

.form-input {
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(91, 127, 255, 0.1);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}
</style>
```

**改进**:
- 使用Card包装表单
- 使用新的Button组件
- 简洁的表单样式
- 焦点状态美化
- 更好的无障碍性

---

## 🎯 颜色迁移对照表

| 原始颜色 | 用途 | 新CSS变量 | 新值 |
|---------|------|---------|------|
| #409EFF | 主色 | --primary-color | #5B7FFF |
| #67C23A | 成功 | --success-color | #10B981 |
| #E6A23C | 警告 | --warning-color | #F59E0B |
| #F56C6C | 错误 | --danger-color | #EF4444 |
| #ffffff | 背景 | --bg-card | #FFFFFF |
| #f5f7fa | 页面背景 | --bg-primary | #F8FAFC |
| #303133 | 文字 | --text-primary | #1E293B |

---

## 📏 间距迁移对照表

| 原始值 | 新CSS变量 | 说明 |
|-------|---------|------|
| 5px | var(--spacing-xs) | 微小 |
| 10px | var(--spacing-sm) | 小 |
| 15px | var(--spacing-md) | 标准 |
| 20px | var(--spacing-md) + extra | 需要自定义 |
| 24px | var(--spacing-lg) | 大 |
| 30px | var(--spacing-lg) + extra | 需要自定义 |

---

## ✅ 迁移验收清单

### 外观检查
- [ ] 颜色符合新配色
- [ ] 间距符合8px系统
- [ ] 圆角统一为8px或以上
- [ ] 阴影柔和自然
- [ ] 字体大小合理

### 交互检查
- [ ] Hover效果流畅
- [ ] 按钮可点击
- [ ] 过渡动画正常
- [ ] 加载状态清晰
- [ ] 空状态处理好

### 响应式检查
- [ ] 桌面端 (1920x1080) ✓
- [ ] 平板端 (1024x768) ✓
- [ ] 手机端 (375x812) ✓
- [ ] 侧边栏响应式折叠 ✓
- [ ] 内容自适应 ✓

### 代码质量
- [ ] 使用CSS变量
- [ ] 遵循命名规范
- [ ] 注释清晰
- [ ] 无重复代码
- [ ] 性能良好

---

## 🔗 快速参考

### 常用CSS变量
```css
/* 颜色 */
var(--primary-color)      /* #5B7FFF */
var(--bg-card)            /* #FFFFFF */
var(--text-primary)       /* #1E293B */

/* 间距 */
var(--spacing-md)         /* 16px */
var(--spacing-lg)         /* 24px */

/* 效果 */
var(--radius-md)          /* 8px */
var(--shadow-md)          /* 0 4px 6px... */
var(--transition-base)    /* 250ms ease */
```

### 常用组件
```vue
<!-- Card -->
<Card title="标题"><p>内容</p></Card>

<!-- StatCard -->
<StatCard icon="📊" label="标签" :value="123" />

<!-- Button -->
<Button variant="primary" size="medium">按钮</Button>
```

---

## 📞 常见问题

**Q: 可以混用新旧组件吗？**  
A: 可以，但不推荐。应该逐步迁移。

**Q: 如何自定义主题色？**  
A: 修改 `src/styles/variables.css` 中的CSS变量。

**Q: 响应式设计怎么处理？**  
A: 查看 Dashboard.vue、Assignments.vue 等示例页面。

**Q: 如何添加自己的样式？**  
A: 在 `<style scoped>` 中使用CSS变量，遵循规范。

---

## 🚀 下一步

1. **选择一个页面** - 从简单的开始
2. **按照指南迁移** - 遵循本指南步骤
3. **测试验收** - 检查迁移清单
4. **反馈优化** - 记录遇到的问题

---

**祝迁移顺利！** ✨

如有问题，参考这些文件：
- UI_REDESIGN_IMPLEMENTATION.md - 详细文档
- UI_VISUAL_GUIDE.md - 视觉展示
- src/views/Dashboard.vue - 参考实现
