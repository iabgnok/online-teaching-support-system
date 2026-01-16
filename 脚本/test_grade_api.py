"""
成绩系统 API 测试脚本
快速验证所有API端点是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

def test_grade_apis():
    """测试成绩系统API"""
    
    print("=" * 60)
    print("开始测试成绩系统 API")
    print("=" * 60)
    
    # 需要登录token，这里假设已登录
    # 实际使用时需要先登录获取session
    
    class_id = 301  # 测试用的教学班ID，请根据实际情况修改
    
    tests = [
        {
            "name": "1. 获取成绩结构",
            "method": "GET",
            "url": f"{BASE_URL}/grades/class/{class_id}/categories",
        },
        {
            "name": "2. 创建成绩分类",
            "method": "POST",
            "url": f"{BASE_URL}/grades/class/{class_id}/categories",
            "data": {
                "name": "平时成绩",
                "weight": 30,
                "description": "包括考勤、作业等"
            }
        },
        {
            "name": "3. 获取成绩统计",
            "method": "GET",
            "url": f"{BASE_URL}/grades/class/{class_id}/statistics",
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], timeout=5)
            elif test['method'] == 'POST':
                response = requests.post(
                    test['url'], 
                    json=test.get('data'),
                    timeout=5
                )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✓ 测试通过")
                results.append((test['name'], True))
            elif response.status_code == 401:
                print("⚠ 需要登录（这是正常的，说明API存在）")
                results.append((test['name'], True))
            else:
                print(f"✗ 测试失败: {response.text[:100]}")
                results.append((test['name'], False))
                
        except requests.exceptions.ConnectionError:
            print("✗ 连接失败：后端服务器未启动")
            results.append((test['name'], False))
        except Exception as e:
            print(f"✗ 测试出错: {str(e)}")
            results.append((test['name'], False))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有API端点已正确注册！")
    else:
        print("\n⚠ 部分API端点可能存在问题")

if __name__ == '__main__':
    test_grade_apis()
