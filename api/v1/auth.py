from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from models import Users, Student, Teacher
from . import api_v1

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
    return jsonify({
        'message': 'Logged in successfully',
        'user': {
            'id': user.user_id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role
        }
    })

@api_v1.route('/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@api_v1.route('/me', methods=['GET'])
@login_required
def get_current_user():
    data = {
        'id': current_user.user_id,
        'username': current_user.username,
        'real_name': current_user.real_name,
        'role': current_user.role,
        'email': current_user.email,
        'phone': current_user.phone
    }
    
    if current_user.role == 'student' and current_user.student_profile:
        s = current_user.student_profile
        data.update({
            'student_no': s.student_no,
            'major': s.major,
            'dept_name': s.department.dept_name if s.department else ''
        })
    elif current_user.role == 'teacher' and current_user.teacher_profile:
        t = current_user.teacher_profile
        data.update({
            'teacher_no': t.teacher_no,
            'title': t.title,
            'dept_name': t.department.dept_name if t.department else ''
        })
        
    return jsonify(data)

@api_v1.route('/users/search', methods=['GET'])
@login_required
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
@login_required
def update_profile():
    """更新当前用户的基本信息"""
    data = request.get_json()
    
    if 'real_name' in data:
        current_user.real_name = data['real_name']
    if 'phone' in data:
        current_user.phone = data['phone']
    if 'email' in data:
        current_user.email = data['email']
    
    try:
        from app import db
        db.session.commit()
        return jsonify({'message': '信息更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_v1.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改当前用户密码"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 验证旧密码
    if not current_user.verify_password(old_password):
        return jsonify({'error': '原密码错误'}), 400
    
    # 设置新密码
    current_user.set_password(new_password)
    
    try:
        from app import db
        db.session.commit()
        return jsonify({'message': '密码修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
