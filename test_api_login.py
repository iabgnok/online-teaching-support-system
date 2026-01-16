#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app
import json

# 测试登录API
with app.test_client() as client:
    response = client.post(
        '/api/v1/login',
        data=json.dumps({
            'username': '3123004715',
            'password': '123456'
        }),
        content_type='application/json'
    )
    
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.get_json()}')
    print(f'Session: {dict(client.cookie_jar)}')
