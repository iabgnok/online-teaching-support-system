"""
将现有的群聊对话转换为班级群
"""

from models import db, Conversation, TeachingClass
from app import app

def fix_conversations():
    with app.app_context():
        # 查找所有type为group的对话
        conversations = Conversation.query.filter_by(conversation_type='group').all()
        
        print(f"找到 {len(conversations)} 个群聊对话")
        
        for conv in conversations:
            print(f"\n处理对话: {conv.title} (ID: {conv.id})")
            
            # 尝试从标题匹配班级
            classes = TeachingClass.query.all()
            matched_class = None
            
            for cls in classes:
                if cls.class_name in conv.title or conv.title in cls.class_name:
                    matched_class = cls
                    break
            
            if matched_class:
                print(f"  匹配到班级: {matched_class.class_name} (ID: {matched_class.class_id})")
                
                # 更新对话类型和班级ID
                conv.conversation_type = 'class_group'
                conv.class_id = matched_class.class_id
                
                # 更新标题，添加班级群标识
                if '班级群' not in conv.title:
                    conv.title = f"🏫 {matched_class.class_name}"
                
                print(f"  ✅ 已转换为班级群")
            else:
                print(f"  ⚠️ 未找到匹配的班级")
        
        db.session.commit()
        print("\n✅ 所有对话已更新")

if __name__ == '__main__':
    fix_conversations()
