"""
创建测试用户
"""
import requests

BASE_URL = "http://localhost:8000"

def create_test_user():
    print("创建测试用户...")
    
    # 使用有效的邀请码注册
    invite_codes = ["HEALTH2024", "UNIVERSITY", "STUDENT123", "HEALTH001"]
    
    for invite_code in invite_codes:
        user_data = {
            "name": "testuser",
            "password": "test123",
            "invite_code": invite_code
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        
        if response.status_code == 200:
            print(f"注册成功！邀请码：{invite_code}")
            print(f"响应：{response.json()}")
            return True
        else:
            print(f"邀请码 {invite_code} 失败：{response.json()}")
    
    print("所有邀请码都失败，请检查后端配置")
    return False

if __name__ == "__main__":
    create_test_user()
