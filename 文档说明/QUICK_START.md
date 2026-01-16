# 权限管理和论坛管理系统 - 快速开始指南

## 5分钟快速开始

### 1. 检查文件是否存在

```bash
# 检查后端文件
ls -la permission_manager.py
ls -la api/v1/forum_management.py

# 检查前端文件
ls -la frontend/src/views/admin/PermissionManagement.vue
ls -la frontend/src/views/admin/ForumManagement.vue
```

### 2. 启动应用

```bash
# 启动后端
python app.py

# 在另一个终端启动前端
cd frontend
npm run dev
```

### 3. 数据库初始化

```bash
# 在 Python 交互式会话中
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     print("Tables created!")
```

### 4. 升级现有管理员权限

```python
# 创建脚本并运行
from app import app, db
from models import Admin
from permission_manager import init_admin_permissions

with app.app_context():
    admins = Admin.query.all()
    for admin in admins:
        # 默认设为系统管理员（权限等级2）
        init_admin_permissions(admin, 'system_admin')
    db.session.commit()
    print(f"Upgraded {len(admins)} admins!")
```

### 5. 测试权限管理 API

```bash
# 获取管理员列表
curl -X GET http://localhost:5000/api/v1/admin/admins \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_ID"

# 查看权限等级定义
curl -X GET http://localhost:5000/api/v1/admin/permission-levels \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_ID"
```

### 6. 测试论坛管理 API

```bash
# 获取所有帖子（需要论坛管理权限）
curl -X GET "http://localhost:5000/api/v1/forum-management/admin/posts?page=1" \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_ID"

# 获取统计信息
curl -X GET http://localhost:5000/api/v1/forum-management/admin/statistics \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_ID"
```

### 7. 访问前端页面

- 权限管理: `http://localhost:3000/admin/permissions`
- 论坛管理: `http://localhost:3000/admin/forum-management`

---

## 常用命令

### 查看所有管理员权限

```python
from app import app
from models import Admin

with app.app_context():
    admins = Admin.query.all()
    for admin in admins:
        print(f"管理员: {admin.user.real_name}")
        print(f"  等级: {admin.permission_level}")
        print(f"  论坛管理: {admin.can_manage_forum}")
        print(f"  用户管理: {admin.can_manage_users}")
        print()
```

### 给某个管理员授予权限

```python
from app import app, db
from models import Admin

with app.app_context():
    admin = Admin.query.filter_by(admin_no='ADMIN001').first()
    if admin:
        admin.can_manage_forum = True
        admin.can_review_content = True
        db.session.commit()
        print("Permission granted!")
```

### 查看最近的审核日志

```python
from app import app
from models import ForumModeration

with app.app_context():
    logs = ForumModeration.query.order_by(
        ForumModeration.created_at.desc()
    ).limit(10).all()
    
    for log in logs:
        print(f"操作: {log.action}")
        print(f"原因: {log.reason}")
        print(f"时间: {log.created_at}")
        print()
```

### 查看所有隐藏的帖子

```python
from app import app
from models import ForumPost, ForumPostStatus

with app.app_context():
    hidden_posts = ForumPost.query.join(
        ForumPostStatus
    ).filter(
        ForumPostStatus.is_hidden == True
    ).all()
    
    print(f"隐藏的帖子数: {len(hidden_posts)}")
    for post in hidden_posts:
        print(f"  - {post.title} (原因: {post.status_tracking[0].hide_reason})")
```

---

## 权限快速参考

### 权限等级

```
1 = 超级管理员 (最高权限)
2 = 系统管理员
3 = 部门管理员
4 = 内容审核员 (最低权限)
```

### 功能权限

| 权限 | 说明 |
|------|------|
| `can_manage_users` | 管理用户 |
| `can_manage_forum` | 管理论坛 |
| `can_manage_courses` | 管理课程 |
| `can_manage_grades` | 管理成绩 |
| `can_manage_announcements` | 管理公告 |
| `can_review_content` | 审核内容 |
| `can_ban_users` | 禁用用户 |

### 快速设置管理员

```python
from app import app, db
from models import Admin
from permission_manager import init_admin_permissions

with app.app_context():
    admin = Admin.query.get(1)
    
    # 设为超级管理员
    init_admin_permissions(admin, 'super_admin')
    db.session.commit()
```

---

## 前端快速参考

### 权限管理页面功能

1. **查看权限等级表** - 理解不同管理员等级
2. **查看管理员列表** - 所有系统管理员
3. **筛选管理员** - 按权限等级筛选
4. **编辑权限** - 点击"编辑"按钮修改权限

### 论坛管理页面功能

1. **查看统计卡片** - 总帖子数、隐藏数等
2. **查看帖子列表** - 所有论坛帖子
3. **快速操作** - 置顶、隐藏、锁定、删除
4. **查看审核日志** - 点击"查看审核日志"按钮
5. **撤销操作** - 点击"↩️"撤销错误的审核

---

## 常见问题解答

### Q: 如何快速给管理员赋予所有权限？

```python
from permission_manager import init_admin_permissions
init_admin_permissions(admin, 'super_admin')
```

### Q: 如何检查管理员是否有某个权限？

```python
if admin.has_feature_permission('forum_manage'):
    print("Has forum management permission")
```

### Q: 如何查看某个帖子的所有审核操作？

```python
logs = ForumModeration.query.filter_by(post_id=post_id).all()
```

### Q: 如何撤销某个审核操作？

```
POST /api/v1/forum-management/admin/moderation-logs/{log_id}/reverse
```

---

## 故障排查

### 权限装饰器返回 403

**检查点**:
1. 用户是否已登录？
2. 用户是否是管理员？
3. 管理员是否有对应的功能权限？

### 论坛管理页面空白

**检查点**:
1. 前端代码是否加载？
2. API 是否可访问？
3. 浏览器控制台是否有错误？

### 数据库表不存在

**解决**:
```python
from app import app, db
with app.app_context():
    db.create_all()
```

---

## 代码示例

### 使用权限装饰器保护端点

```python
from permission_manager import admin_permission_required, forum_admin_required

@app.route('/api/admin/settings', methods=['POST'])
@admin_permission_required(1)  # 需要权限等级 1
def admin_settings():
    # 仅超级管理员可访问
    return jsonify({'status': 'ok'})

@app.route('/api/forum/delete-post/<post_id>', methods=['DELETE'])
@forum_admin_required  # 需要论坛管理权限
def delete_forum_post(post_id):
    # 仅论坛管理员可访问
    return jsonify({'status': 'deleted'})
```

### 在 JavaScript 中检查权限

```javascript
// 获取当前用户权限
async function checkMyPermissions() {
  const response = await fetch('/api/v1/admin/my-permissions', {
    credentials: 'include'
  })
  
  if (response.ok) {
    const perms = await response.json()
    
    if (perms.permissions.can_manage_forum) {
      // 显示论坛管理按钮
      showForumManagementButton()
    }
  }
}
```

### 执行论坛操作

```javascript
// 置顶帖子
async function pinPost(postId) {
  const response = await fetch(
    `/api/v1/forum-management/admin/posts/${postId}/pin`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ reason: '重要讨论' })
    }
  )
  
  if (response.ok) {
    alert('帖子已置顶')
    location.reload()
  }
}

// 隐藏帖子
async function hidePost(postId) {
  const response = await fetch(
    `/api/v1/forum-management/admin/posts/${postId}/hide`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ reason: '内容不当' })
    }
  )
  
  if (response.ok) {
    alert('帖子已隐藏')
    location.reload()
  }
}
```

---

## 性能优化提示

1. **使用分页** - 帖子列表默认每页20条
2. **缓存权限** - 权限变更后可设置缓存过期
3. **索引数据库** - 常用查询字段建立索引
4. **异步加载** - 前端使用异步加载大数据

---

## 安全提示

1. **权限检查** - 所有敏感操作都需要权限检查
2. **审计日志** - 所有操作都记录在审核日志中
3. **操作撤销** - 支持撤销错误的操作
4. **内容备份** - 删除操作保存内容备份

---

## 获取帮助

- 查看详细文档: `PERMISSION_FORUM_MANAGEMENT.md`
- 查看集成指南: `IMPLEMENTATION_GUIDE.md`
- 查看 API 文档: 各模块的注释和说明
- 检查示例代码: 本文件中的代码示例

---

*最后更新: 2026年1月16日*
