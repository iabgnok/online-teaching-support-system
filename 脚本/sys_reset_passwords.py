from app import app
from models import db, Users

def reset_all_passwords(default_password='123456'):
    """重置所有用户的密码为默认值"""
    with app.app_context():
        print(f"准备将所有用户的密码重置为: {default_password}")
        users = Users.query.all()
        count = 0
        
        for user in users:
            try:
                # 使用 password setter 自动进行哈希加密
                user.password = default_password
                count += 1
                if count % 10 == 0:
                    print(f"已处理 {count} 个用户...")
            except Exception as e:
                print(f"重置用户 {user.username} 密码时出错: {str(e)}")
        
        if count > 0:
            try:
                db.session.commit()
                print(f"\n成功！已将 {count} 个用户的密码重置为 '{default_password}' (已加密存储)。")
            except Exception as e:
                db.session.rollback()
                print(f"提交更改时出错: {str(e)}")
        else:
            print("没有找到用户。")

if __name__ == "__main__":
    reset_all_passwords()
