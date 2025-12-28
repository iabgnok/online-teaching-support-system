"""
测试密码导入功能
验证新导入的用户可以直接用CSV中的密码登录
"""
from app import app, db
from models import Users

with app.app_context():
    print("=" * 60)
    print("测试密码导入功能")
    print("=" * 60)
    
    # 测试几个示例用户
    test_users = [
        ('teacher103', 'Passw0rd!'),  # 张曼玉
        ('student100', 'Passw0rd!'),  # 赵天宇
        ('admin100', 'Passw0rd!')     # 张维华
    ]
    
    for username, password in test_users:
        user = Users.query.filter_by(username=username).first()
        
        if user:
            # 检查密码是否正确
            is_valid = user.verify_password(password)
            status = "✅ 验证通过" if is_valid else "❌ 验证失败"
            
            print(f"\n用户: {username} ({user.real_name})")
            print(f"  密码验证: {status}")
            print(f"  密码哈希: {user.password_hash[:50]}...")
        else:
            print(f"\n用户: {username}")
            print(f"  ❌ 用户不存在")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
