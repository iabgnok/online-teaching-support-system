from flask import jsonify, request, g
from flask_login import login_user, logout_user, current_user
from models import Users, Student, Teacher
from . import api_v1
from functools import wraps
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

def api_login_required(f):
    """检查用户是否登录，如果未登录则返回 401"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 允许OPTIONS请求通过（CORS预检）
        if request.method == 'OPTIONS':
            return jsonify({'msg': 'preflight ok'}), 200

        # 首先尝试从Authorization头获取token
        token = request.headers.get('Authorization')
        print(f"Debug auth: Authorization header = {token}")
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
            try:
                s = Serializer(current_app.config['SECRET_KEY'])
                data = s.loads(token, max_age=None)  # 不检查过期时间
                user_id = data.get('user_id')
                print(f"Debug auth: token user_id = {user_id}")
                user = Users.query.get(user_id)
                if user and user.status == 1:
                    # 将用户存储在g对象中
                    g.user = user
                    print(f"Debug auth: authenticated user = {user.user_id}, role = {user.role}")
                    return f(*args, **kwargs)
            except Exception as e:
                print(f"Token validation error: {e}")
                pass
        
        # 如果token无效或不存在，返回401
        print("Debug auth: authentication failed")
        return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def generate_token(user):
    """生成用户token"""
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.user_id})

@api_v1.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = Users.query.filter_by(username=username).first()
    
    if user is None or not user.verify_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    if user.status == 0:
        return jsonify({'error': 'Account disabled'}), 403

    login_user(user)
    token = generate_token(user)
    return jsonify({
        'message': 'Logged in successfully',
        'token': token,
        'user': {
            'id': user.user_id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role
        }
    })

@api_v1.route('/logout', methods=['POST'])
@api_login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@api_v1.route('/me', methods=['GET'])
@api_login_required
def get_current_user():
    user = g.user
    data = {
        'id': user.user_id,
        'username': user.username,
        'real_name': user.real_name,
        'role': user.role,
        'email': user.email,
        'phone': user.phone
    }
    
    if user.role == 'student' and user.student_profile:
        s = user.student_profile
        data.update({
            'student_no': s.student_no,
            'major': s.major,
            'dept_name': s.department.dept_name if s.department else ''
        })
    elif user.role == 'teacher' and user.teacher_profile:
        t = user.teacher_profile
        data.update({
            'teacher_no': t.teacher_no,
            'title': t.title,
            'dept_name': t.department.dept_name if t.department else ''
        })
        
    return jsonify(data)

@api_v1.route('/users/search', methods=['GET'])
@api_login_required
def search_users():
    """搜索用户（用于站内信等功能）"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # 搜索用户名或真实姓名
    users = Users.query.filter(
        (Users.username.like(f'%{query}%')) | 
        (Users.real_name.like(f'%{query}%'))
    ).filter(Users.status == 1).limit(20).all()
    
    results = []
    for u in users:
        user_info = {
            'id': u.user_id,
            'username': u.username,
            'real_name': u.real_name,
            'role': u.role
        }
        
        # 添加角色特定信息
        if u.role == 'student' and u.student_profile:
            user_info['student_no'] = u.student_profile.student_no
        elif u.role == 'teacher' and u.teacher_profile:
            user_info['teacher_no'] = u.teacher_profile.teacher_no
            
        results.append(user_info)
    
    return jsonify(results)

@api_v1.route('/profile', methods=['PUT'])
@api_login_required
def update_profile():
    """更新当前用户的基本信息"""
    data = request.get_json()
    
    if 'real_name' in data:
        g.user.real_name = data['real_name']
    if 'phone' in data:
        g.user.phone = data['phone']
    if 'email' in data:
        g.user.email = data['email']
    
    try:
        from models import db
        db.session.commit()
        return jsonify({'message': '信息更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_v1.route('/change-password', methods=['POST'])
@api_login_required
def change_password():
    """修改当前用户密码"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 验证旧密码
    if not g.user.verify_password(old_password):
        return jsonify({'error': '原密码错误'}), 400
    
    # 设置新密码
    g.user.set_password(new_password)
    
    try:
        from models import db
        db.session.commit()
        return jsonify({'message': '密码修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
