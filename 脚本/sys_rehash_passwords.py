from app import app
from models import db, Users

def rehash_passwords():
    with app.app_context():
        print("开始检查并重新哈希用户密码...")
        users = Users.query.all()
        count = 0
        skipped = 0
        
        for user in users:
            current_pwd = user.password_hash
            # 打印前几个用户的密码前缀用于调试（只显示前20字符）
            if skipped < 5 and Users.is_hashed_password(current_pwd):
                 print(f"DEBUG: 用户 {user.username} 当前存储的密码视为哈希: {current_pwd[:30]}...")

            # 检查当前密码是否已经是哈希值
            if Users.is_hashed_password(current_pwd):
                skipped += 1
                continue
                
            # 如果不是哈希值，则认为是明文，进行哈希
            try:
                # 使用 set_password 方法，它不仅设置属性，还会处理哈希逻辑
                # 但这里我们需要强制它通过 set_password 的逻辑重新赋值
                # 因为 set_password 内部会再次检查 is_hashed_password
                user.set_password(current_pwd)
                count += 1
                print(f"用户 {user.username} (ID: {user.user_id}) 密码已重新哈希")
            except Exception as e:
                print(f"处理用户 {user.username} 时出错: {str(e)}")
        
        if count > 0:
            try:
                db.session.commit()
                print(f"成功更新了 {count} 个用户的密码。")
            except Exception as e:
                db.session.rollback()
                print(f"提交更改时出错: {str(e)}")
        else:
            print("没有发现需要重新哈希的密码。")
            
        print(f"跳过了 {skipped} 个已经是哈希值的密码。")

if __name__ == "__main__":
    rehash_passwords()
