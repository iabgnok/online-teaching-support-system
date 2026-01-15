from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from models import Users
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
    return jsonify({
        'id': current_user.user_id,
        'username': current_user.username,
        'real_name': current_user.real_name,
        'role': current_user.role
    })
