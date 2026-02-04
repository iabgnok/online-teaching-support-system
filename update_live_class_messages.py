"""
更新所有课堂入口消息，添加课堂状态
"""
from app import app
from models import db, IMMessage, LiveClass
import json

def update_live_class_entry_messages():
    """更新所有课堂入口消息，添加status字段"""
    with app.app_context():
        # 获取所有课堂入口消息
        entry_messages = IMMessage.query.filter_by(message_type='live_class_entry').all()
        
        updated_count = 0
        for msg in entry_messages:
            try:
                content = json.loads(msg.content)
                lesson_id = content.get('lesson_id')
                
                if not lesson_id:
                    continue
                
                # 查找对应的课堂
                live_class = LiveClass.query.filter_by(lesson_id=lesson_id).first()
                
                if live_class:
                    # 根据课堂的实际状态更新消息
                    content['status'] = live_class.status
                    msg.content = json.dumps(content, ensure_ascii=False)
                    updated_count += 1
                    print(f"更新消息 {msg.id}: lesson_id={lesson_id}, status={live_class.status}")
                else:
                    # 如果找不到课堂，标记为已结束
                    if 'status' not in content:
                        content['status'] = 'ended'
                        msg.content = json.dumps(content, ensure_ascii=False)
                        updated_count += 1
                        print(f"更新消息 {msg.id}: lesson_id={lesson_id}, status=ended (课堂不存在)")
                        
            except Exception as e:
                print(f"处理消息 {msg.id} 时出错: {e}")
                continue
        
        db.session.commit()
        print(f"\n总共更新了 {updated_count} 条消息")
        return updated_count

if __name__ == '__main__':
    print("开始更新课堂入口消息...")
    count = update_live_class_entry_messages()
    print(f"完成！更新了 {count} 条消息")
