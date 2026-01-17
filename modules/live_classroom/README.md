# 线上授课模块 (Live Classroom) - 开发隔离区

本目录是为“线上授课”功能设立的独立开发环境，旨在确保该复杂模块在集成到主系统前能够独立完成 SocketIO 通信与 WebRTC 信令的测试。

## 目录结构
- `/server/live_app.py`: 独立的 Flask-SocketIO 服务器（运行于 5001 端口）。
- `/client/index.html`: 独立的轻量级前端测试页面，包含协同画板原型。

## 如何运行测试
1. **启动后端服务**:
   在终端运行：
   ```bash
   venv/Scripts/python.exe modules/live_classroom/server/live_app.py
   ```
2. **启动前端测试**:
   直接在浏览器中打开 `modules/live_classroom/client/index.html`。
   建议同时打开两个浏览器窗口，一个选择“教师”身份，另一个选择“学生”身份，并在同一个班级代码（如 CLASS_101）下连接。

## 核心测试点
1. **Socket 房间隔离**: 不同班级代码的绘画数据是否互不干扰。
2. **画板协同性能**: 教师涂鸦时，学生端的延迟情况。
3. **百分比坐标适配**: 教师端和学生端如果窗口大小不一致，笔迹是否依然对齐。
4. **WebRTC 信令转发**: (待完成后) 交换 SDP 和 ICE Candidate 的逻辑。

## 完成后集成步骤
1. 将 `live_app.py` 中的事件处理逻辑迁移至主系统的 `app.py` 或独立的 SocketIO 蓝图中。
2. 将 `index.html` 中的 Canvas 逻辑与 Socket 监听器重构为 Vue 组件，集成至 `frontend/src`。
3. 把 5001 端口的通信收拢回主系统的 SocketIO 服务（通常为 5000）。
