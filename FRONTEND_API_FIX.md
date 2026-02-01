# 前端API修复说明

## 🔧 已修复的问题

### 问题描述
前端访问聊天API时出现 **401 UNAUTHORIZED** 错误，原因是新创建的组件直接使用了`axios`而不是配置好的`api`实例，导致认证token没有正确发送。

### 修复内容

#### 1. 更新所有新组件的导入
将所有组件中的：
```javascript
import axios from 'axios'
```
替换为：
```javascript
import api from '../api'
```

#### 2. 更新API调用路径
将所有组件中的完整路径：
```javascript
axios.get('/api/v1/chat/...')
```
替换为：
```javascript
api.get('/chat/...')
```

因为`api`实例已经配置了`baseURL: '/api/v1'`

#### 3. 已修复的组件列表
- ✅ **MessageReactions.vue** - 消息反应组件
- ✅ **PinnedMessageBar.vue** - 置顶消息栏
- ✅ **MentionSelector.vue** - @提及选择器
- ✅ **ForwardDialog.vue** - 转发对话框
- ✅ **LinkPreview.vue** - 链接预览组件

#### 4. 改进App.vue
- 优化未读消息获取逻辑
- 添加401错误的静默处理
- 避免在未登录时打印错误日志

#### 5. 改进api.js
- 优化401错误处理
- 避免在已经在登录页时重复重定向
- 清理更多localStorage项

---

## ✅ 验证步骤

### 1. 检查浏览器控制台
打开浏览器开发者工具（F12），查看：
- Network标签：检查请求是否带有`Authorization: Bearer <token>`
- Console标签：不应该有401错误

### 2. 检查localStorage
在Console中运行：
```javascript
console.log('Token:', localStorage.getItem('user_token'))
console.log('User ID:', localStorage.getItem('user_id'))
console.log('Role:', localStorage.getItem('user_role'))
```

应该能看到这些值（登录后）。

### 3. 测试登录流程
1. 访问 http://localhost:5173/login
2. 使用测试账号登录（如：admin/admin123）
3. 登录成功后应该：
   - 自动跳转到对应页面
   - 顶部导航栏显示"消息中心"等链接
   - 不应该有401错误

### 4. 测试聊天功能
1. 点击"消息中心"
2. 应该能看到对话列表
3. 点击某个对话进入聊天页面
4. 尝试：
   - 发送消息
   - 添加表情反应（点击消息）
   - 输入@触发提及选择器
   - 转发消息（右键菜单）

---

## 🚨 常见问题排查

### Q1: 仍然出现401错误
**检查**：
1. 确保已经登录
2. 打开Console，运行：`localStorage.getItem('user_token')`
3. 如果是null，说明token丢失，需要重新登录

**解决**：
```javascript
// 清除所有缓存，重新登录
localStorage.clear()
location.reload()
```

### Q2: 登录后立即跳回登录页
**原因**：Token可能格式错误或后端验证失败

**检查**：
1. 打开Network标签
2. 找到登录请求
3. 查看Response，确认返回了token
4. 检查后端日志，看token验证是否有问题

### Q3: 消息中心页面空白
**可能原因**：
- 数据库中没有对话记录
- API返回数据格式不匹配

**检查**：
1. 打开Network标签
2. 查看`/api/v1/chat/conversations`请求
3. 检查Response是否返回了数据
4. 如果返回空数组[]，说明没有对话，这是正常的

---

## 📝 API认证机制说明

### 工作流程
1. **登录**: POST /api/v1/auth/login
   - 返回：`{ token: '...', user: {...} }`
   - 前端保存到localStorage

2. **后续请求**: 
   - 请求拦截器自动添加：`Authorization: Bearer <token>`
   - 后端验证token
   - 返回数据或401错误

3. **401处理**:
   - 清除localStorage
   - 重定向到登录页

### api.js配置
```javascript
// 请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('user_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 清除认证信息并跳转
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

---

## 🎯 下一步

所有组件已修复，现在应该：

1. **刷新浏览器页面**（Ctrl+Shift+R 或 Cmd+Shift+R）
2. **清除浏览器缓存**（如果仍有问题）
3. **重新登录**
4. **测试所有新功能**

如果仍有问题，请提供：
- 浏览器Console的完整错误信息
- Network标签中失败请求的详情
- 后端日志（如果有）
