"""测试token解码"""
from itsdangerous import URLSafeTimedSerializer as Serializer
from config import DevelopmentConfig

# 从截图看到的token
token = "eyJ1c2VyX2lkIjoyMDAxfQ.X8h-eA.wn-CSe12vAyAnhnhtApD3CtbkSQ"

print(f"Token: {token}")
print(f"SECRET_KEY: {DevelopmentConfig.SECRET_KEY}")
print()

try:
    s = Serializer(DevelopmentConfig.SECRET_KEY)
    data = s.loads(token, max_age=None)
    print(f"✓ Token解码成功！")
    print(f"  数据: {data}")
    print(f"  user_id: {data.get('user_id')}")
except Exception as e:
    print(f"✗ Token解码失败！")
    print(f"  错误: {type(e).__name__}: {e}")
    
print()
print("测试生成新token:")
try:
    s = Serializer(DevelopmentConfig.SECRET_KEY)
    new_token = s.dumps({'user_id': 2001})
    print(f"  新token: {new_token}")
    
    # 立即验证
    data = s.loads(new_token, max_age=None)
    print(f"  验证成功: {data}")
except Exception as e:
    print(f"  错误: {e}")
