from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'live_classroom_secret!'
# 允许跨域以便在开发环境中进行前端分离测试
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Live Classroom Module Server is running."

# 监听连接
@socketio.on('connect')
def handle_connect():
    print(f"Client connected")

# 加入课堂房间 (以班级 ID 为房间号)
@socketio.on('join_lesson')
def on_join(data):
    room = data.get('class_id')
    user_name = data.get('user_name')
    join_room(room)
    print(f"User {user_name} joined room: {room}")
    emit('status', {'msg': f'{user_name} has entered the room.'}, room=room)

# 协同画板：广播坐标数据
@socketio.on('drawing')
def handle_drawing(data):
    # data 包含 { x, y, color, class_id }
    room = data.get('class_id')
    # 广播给该房间内的所有人（包括发送者，以便展示同步效果）
    emit('drawing', data, room=room, include_self=False)

# 文字互动：广播消息
@socketio.on('chat_message')
def handle_message(data):
    room = data.get('class_id')
    emit('chat_message', {
        'user': data.get('user'),
        'msg': data.get('msg'),
        'time': time.strftime("%H:%M:%S", time.localtime())
    }, room=room)

# WebRTC 信令交换 (Signaling)
@socketio.on('webrtc_signal')
def handle_webrtc_signal(data):
    room = data.get('class_id')
    # 将信令转发给房间内的其他成员
    emit('webrtc_signal', data, room=room, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    print("Starting Live Classroom Module Server on port 5001...")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
