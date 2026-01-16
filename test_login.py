#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import Users, db
from app import app

with app.app_context():
    user = Users.query.filter_by(username='3123004715').first()
    if user:
        print(f'用户存在: {user.username}')
        print(f'用户ID: {user.user_id}')
        print(f'用户角色: {user.role}')
        print(f'账户状态: {user.status}')
        
        # 测试密码
        test_password = '123456'
        result = user.verify_password(test_password)
        print(f'密码验证 ({test_password}): {result}')
    else:
        print('用户不存在')
