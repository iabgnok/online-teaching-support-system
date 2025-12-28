# fix_passwords.py
from app import app, db
from models import Users # 导入 Users 模型
from werkzeug.security import generate_password_hash # 导入加密函数

# 假设您所有用户的明文密码都是 'password123'
DEFAULT_PLAINTEXT_PASSWORD = 'password123'

with app.app_context():
    print("--- 开始更新用户密码 ---")
    
    # 1. 查询所有用户
    users = Users.query.all()
    
    if not users:
        print("数据库中没有找到用户。")
    else:
        for user in users:
            # 检查当前存储的密码是否是明文 'password123'
            # 这是一个安全检查，避免重复哈希已经哈希过的密码
            
            # ⚠️ 注意：由于您模型的@password.setter使用了generate_password_hash，
            # 我们可以直接设置password属性，模型会自动处理哈希。
            # 这里我们假设所有人的明文密码都是 DEFAULT_PLAINTEXT_PASSWORD

            print(f"正在更新用户: {user.username} (ID: {user.user_id})...")
            
            # 直接调用 setter，自动生成并存储哈希值
            # 这一步会调用 Users 模型的 @password.setter
            user.password = DEFAULT_PLAINTEXT_PASSWORD 
            
            print(f" -> 新的哈希值已生成并存储。")
            
        # 2. 提交更改到数据库
        try:
            db.session.commit()
            print("--- 所有用户密码哈希化完成，更改已提交！ ---")
            print("您现在可以使用 'password123' 成功登录了。")
        except Exception as e:
            db.session.rollback()
            print(f"提交数据库时出错: {e}")