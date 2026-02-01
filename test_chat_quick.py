"""
快速测试聊天功能
"""
import webbrowser
import time
from models import db, Conversation, IMMessage, ConversationMember
from app import app

def check_system():
    """检查系统状态"""
    with app.app_context():
        convs = Conversation.query.count()
        msgs = IMMessage.query.count()
        members = ConversationMember.query.count()
        
        print("=" * 60)
        print("Chat System Status Check")
        print("=" * 60)
        print(f"\nDatabase:")
        print(f"  Conversations: {convs}")
        print(f"  Messages: {msgs}")
        print(f"  Members: {members}")
        
        if convs == 0:
            print("\n[WARNING] No conversations found!")
            print("Please run: python setup_chat_test_data.py")
            return False
        
        print("\n[OK] Test data is ready!")
        return True

def open_browser():
    """在浏览器中打开测试页面"""
    print("\n" + "=" * 60)
    print("Opening test page in browser...")
    print("=" * 60)
    
    url = "http://localhost:5173"
    
    print(f"\nURL: {url}")
    print("\nTest Accounts:")
    print("  Teacher: teacher001 / 123456")
    print("  Student: 3123004715 / 123456")
    print("  Student: 3123004716 / 123456")
    
    print("\nOpening in 3 seconds...")
    time.sleep(3)
    
    try:
        webbrowser.open(url)
        print("[OK] Browser opened!")
    except Exception as e:
        print(f"[ERROR] Failed to open browser: {e}")
        print(f"Please manually visit: {url}")
    
    print("\n" + "=" * 60)
    print("Testing Guide:")
    print("=" * 60)
    print("1. Login with student account: 3123004715 / 123456")
    print("2. Check navigation badge shows '8' unread messages")
    print("3. Click 'Message Center' to enter chat page")
    print("4. Click on conversations to view messages")
    print("5. Send a test message")
    print("6. Open another browser and login as teacher001")
    print("7. Test real-time messaging between users")
    print("\nFor detailed testing guide, see: CHAT_TESTING_GUIDE.md")
    print("=" * 60)

if __name__ == '__main__':
    if check_system():
        open_browser()
    else:
        print("\n[ERROR] System not ready. Please setup test data first.")
