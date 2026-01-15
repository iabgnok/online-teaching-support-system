# 在线教学支持系统 - 功能更新与迭代计划

本文档旨在规划系统的后续功能开发与迭代方向，基于对标市面主流教学管理系统（LMS）的架构标准，提出从后端到前端的全面升级方案。

## 📅一、 实施路线图 (Roadmap)

建议分三个阶段进行系统升级，由易到难，逐步完善。其中，**前端架构重构**将作为贯穿始终的技术底座升级。

*   **第一阶段 (Phase 1): 课堂管理增强 & 接口化准备**
    *   **业务功能**：公告与通知系统、考勤管理。
    *   **架构升级**：开始逐步将 Flask 视图改造为 RESTful API，为前后端分离做准备。
*   **第二阶段 (Phase 2): 师生互动提升 & 前端重构**
    *   **业务功能**：课程讨论区、私信/站内信系统。
    *   **架构升级**：引入 Vue 3 前端框架，重写核心交互页面（如讨论区），实现混合架构。
*   **第三阶段 (Phase 3): 核心教学深化 & 全面分离**
    *   **业务功能**：可视化日历/课程表、在线测验与自动评分。
    *   **架构升级**：完成所有页面 Vue 化，后端完全 API 化，实现标准的前后端分离 SPA 架构。

## 💻 二、 前端架构重构规划 (Frontend Architecture Refactoring)

**现状**: 当前使用 Flask Jinja2 模板引擎进行服务端渲染 (SSR)，页面跳转刷新，交互由原生 JS/jQuery 驱动。
**目标**: 对标主流商业系统，采用 **前后端分离 (Frontend-Backend Separation)** 架构。

### 1. 技术选型
*   **前端框架**: **Vue 3** (Composition API) + **Vite**
    *   *理由*: 响应式数据绑定，丰富的组件生态，极佳的开发体验。
*   **UI 组件库**: **Element Plus** 或 **Ant Design Vue**
    *   *理由*: 专业的企业级后台管理组件（表格、表单、侧边栏），开箱即用，视觉风格现代化。
*   **通信协议**: All **RESTful API** (JSON)
    *   *理由*: 清晰的接口定义，支持多端（Web, App）扩展。

### 2. 重构收益
*   **用户体验**: 像原生 App 一样流畅，无页面白屏刷新，支持复杂的即时交互（如拖拽排课、实时消息）。
*   **开发效率**: 后端专注数据处理，前端专注界面交互，可并行开发。
*   **维护性**: 清晰的代码结构，组件复用率高。

---

## 🛠️ 三、 详细功能规划

### 1. 公告与通知系统 (Announcement & Notification)
**优先级**: 🔥 **P0 (最高)**
**目标**: 实现信息的持久化传达，确保重要消息不被遗漏。

*   **功能描述**:
    *   **系统公告**: 管理员发布，所有用户登录后在首页/仪表盘可见（如：系统维护通知）。
    *   **课程通知**: 教师针对特定教学班发布，仅该班级学生可见（如：作业截止提醒、停课通知）。
    *   **未读提醒**: 简单的红点标记或未读计数。

*   **数据库变更 (Schema)**:
    ```python
    class Announcement(db.Model):
        id = db.Column(db.BigInteger, primary_key=True)
        title = db.Column(db.String(200))
        content = db.Column(db.Text)
        author_id = db.Column(db.BigInteger, db.ForeignKey('Users.user_id'))
        #Scope: 'global' (全站) 或 'class' (班级)
        scope_type = db.Column(db.String(20)) 
        # 如果是班级通知，关联班级ID
        target_class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'), nullable=True)
        created_at = db.Column(db.DateTime, default=func.now())
    ```

*   **开发任务**:
    *   后端: 新增 CRUD 路由，仪表盘数据注入逻辑。
    *   前端: 仪表盘增加“最新公告”板块。

### 2. 考勤管理模块 (Attendance)
**优先级**: 🔥 **P0 (最高)**
**目标**: 数字化管理线下/线上出勤，纳入平时成绩计算。

*   **功能描述**:
    *   **教师点名**: 教师选择教学班，生成当日学生名单，手动勾选状态（出勤/缺席/迟到/请假）。
    *   **考勤统计**: 自动计算每个学生的出勤率。
    *   **成绩挂钩**: 在成绩计算公式中增加考勤权重（如 +10%）。

*   **数据库变更 (Schema)**:
    ```python
    class Attendance(db.Model):
        id = db.Column(db.BigInteger, primary_key=True)
        class_id = db.Column(db.BigInteger, db.ForeignKey('TeachingClass.class_id'))
        date = db.Column(db.Date)
        # 记录每位学生的出勤状态，建议使用关联表或JSON存储
        # 简单方案：AttendanceRecord 表关联 Attendance 和 Student
    
    class AttendanceRecord(db.Model):
        id = db.Column(db.BigInteger, primary_key=True)
        attendance_id = db.Column(db.BigInteger, db.ForeignKey('Attendance.id'))
        student_id = db.Column(db.BigInteger, db.ForeignKey('Student.student_id'))
        status = db.Column(db.String(20)) # 'present', 'absent', 'late', 'leave'
    ```

*   **开发任务**:
    *   后端: 批量创建考勤记录的逻辑，统计接口。
    *   前端: 考勤录入表格页面，学生端查看考勤记录页面。

### 3. 课程讨论区 (Discussion Forum)
**优先级**: 🌟 **P1 (中)**
**目标**: 提供异步沟通渠道，沉淀课程知识库。

*   **功能描述**:
    *   每门课程/教学班拥有独立讨论区。
    *   支持发帖、回帖、Markdown编辑器。
    *   教师可置顶帖子、标记“标准答案”。

*   **数据库变更 (Schema)**:
    *   新增 `ForumPost` (主题帖) 和 `ForumComment` (回复) 表。

*   **开发任务**:
    *   后端: 帖子与评论的增删改查。
    *   前端: 仿论坛列表页与详情页，集成简单的富文本编辑器。

### 4. 课程表与日历视图 (Calendar & Schedule)
**优先级**: 🌟 **P1 (中)**
**目标**: 提升用户体验，直观展示时间安排。

*   **功能描述**:
    *   **仪表盘日历**: 首页显示日历控件。
    *   **事件集成**: 自动显示上课时间（需解析 "周一 1-2节" 格式）、作业 Deadline、考试时间。
    *   **视图切换**: 月视图/周视图切换。

*   **技术实现**:
    *   前端: 引入 `FullCalendar` 或类似 JS 库。
    *   后端: 提供 `/api/events` 接口，返回 JSON 格式的事件数据。

### 5. 在线测验 (Online Quiz)
**优先级**: 🧊 **P2 (待定)**
**目标**: 补充客观题自动批改能力 (当前系统主要处理主观作业)。

*   **功能描述**:
    *   **题库管理**: 录入单选、多选、判断题。
    *   **测验发布**: 从题库选题，设置时间限制。
    *   **在线答题**: 学生在网页端点击选项作答。
    *   **自动评分**: 提交即出分，自动写入成绩表。

*   **复杂度预警**:
    *   涉及复杂的题库设计和防作弊逻辑，开发周期较长。

### 6. 站内信 (Direct Messaging)
**优先级**: 🧊 **P2 (待定)**
**目标**: 解决一对一隐私沟通需求。

*   **功能描述**:
    *   简单的收件箱/发件箱。
    *   用户搜索与私信发送。

---

## 🏗️ 四、 底层架构与数据库深度升级 (Deep Architecture & Database Upgrades)

为了支撑更复杂的业务场景，并对标企业级 LMS 系统，以下升级涉及核心数据模型的重构，建议在系统流量增长或功能扩充到一定阶段后实施。

### 1. 动态权限系统 (RBAC - Role-Based Access Control)
**现状**: 硬编码的 `role` 字段 (admin/teacher/student)，权限控制逻辑分散在代码装饰器中。
**痛点**: 无法添加自定义角色（如“教务员”、“助教”、“督导”），无法灵活调整权限（如临时允许助教修改成绩）。
**升级方案**:
*   **模型重构**:
    *   `Permission`: 定义原子权限 (如 `course:view`, `grade:edit`, `user:delete`)。
    *   `Role`: 角色表 (如 Administrator, Teacher, TA)。
    *   `RolePermission`: 角色与权限的多对多关联。
    *   `UserRole`: 用户与角色的多对多关联（一名用户可是某课的老师，也是另一课的学生）。
*   **收益**: 实现细粒度的权限控制，支持后台动态配置角色权限。

### 2. 教学资源库与版本控制 (Resource Repository & Versioning)
**现状**: `Material` (资料) 与 `TeachingClass` (班级) 强绑定。
**痛点**: 老师每学期开新课都需要重复上传相同的课件；无法管理课件的历史版本。
**升级方案**:
*   **模型重构**:
    *   引入 `ResourceRepository` (公共/个人资源库)：存储文件的元数据、存储路径。
    *   引入 `ResourceVersion` (版本控制)：记录文件的 v1, v2 变更。
    *   `ClassMaterial` (班级引用)：关联 `TeachingClass` 和 `Resource`，而非直接存储文件。
*   **收益**: 实现“一次上传，多处引用”，跨学期轻松复用课程资源，节省存储空间，方便历史回溯。

### 3. 操作审计与学习分析 (Audit Log & Learning Analytics)
**现状**: 只有结果数据（分数），缺乏过程数据。
**痛点**: 无法追踪“谁删除了数据”，无法分析学生的学习投入度（如是否下载了课件）。
**升级方案**:
*   **模型重构**:
    *   `AuditLog`: 记录关键操作 (Who, When, What, OldValue, NewValue)，用于安全审计。
    *   `LearningActivity`: 记录高频学习行为 (Student, Action='view_video', TargetID, Duration, Timestamp)。
*   **技术挑战**: 数据量巨大，可能需要考虑分表存储或引入 NoSQL。

---

## 📝 五、 下一步行动建议

1.  **确认需求**: 请确认优先开发 **Phase 1 (公告 + 考勤)** 是否符合当前教学需求。
2.  **备份数据**: 在进行任何数据库 Schema 变更前，务必完整备份 `models.py` 和现有数据库。
3.  **环境准备**: 确保开发环境配置（`requirements.txt`）准备就绪。

