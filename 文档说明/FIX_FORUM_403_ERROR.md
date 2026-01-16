# 解决论坛管理 403 错误

## 问题原因
加载论坛帖子列表时返回 403 (FORBIDDEN) 错误，原因是当前管理员账户没有 `can_manage_forum` 权限。

## 解决方案
已执行 `init_admin_forum_permission.py` 脚本，为所有6个管理员账户初始化权限：

### ✅ 完成的操作
- 张三 (A001) - 超级管理员，所有权限 = True
- 李四 (A002) - 系统管理员，所有权限 = True
- 王五 (A003) - 系统管理员，所有权限 = True
- 赵六 (A004) - 系统管理员，所有权限 = True
- 孙七 (A005) - 系统管理员，所有权限 = True
- 系统管理员 (A006) - 系统管理员，所有权限 = True

### 🔑 权限包括
- ✅ 论坛管理: True
- ✅ 用户管理: True
- ✅ 课程管理: True
- ✅ 成绩管理: True
- ✅ 公告管理: True
- ✅ 内容审核: True
- ✅ 封禁用户: True

## 使用方法

### 1. 刷新浏览器
**方式1: 完全刷新**
- 按 `Ctrl + Shift + R` (Windows) 或 `Cmd + Shift + R` (Mac)
- 这会清空浏览器缓存并重新加载

**方式2: 退出登录再重新登录**
- 点击右上角 "退出" 按钮
- 重新登录管理员账户
- 权限会自动更新

### 2. 访问论坛管理
刷新后在管理员控制台应该能看到 "论坛管理" 卡片。

## 测试端点
如果仍有问题，可以直接测试 API:

```bash
# 测试论坛统计 API
curl http://localhost:5000/api/v1/forum-management/admin/statistics

# 测试获取帖子 API
curl http://localhost:5000/api/v1/forum-management/admin/posts
```

## 后续维护
- 新创建的管理员需要运行此脚本来获得论坛管理权限
- 或在管理员权限管理页面手动配置权限
