"""
测试邀请码注册功能
"""
import requests

BASE_URL = "http://localhost:8000"

def test_register():
    print("测试邀请码注册功能...")
    
    # 测试不同的邀请码
    invite_codes = ["health2026", "HEALTH2024", "UNIVERSITY", "STUDENT123", "HEALTH001", "INVALID"]
    
    for invite_code in invite_codes:
        user_data = {
            "name": f"testuser_{invite_code}",
            "password": "test123",
            "invite_code": invite_code
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        
        if response.status_code == 200:
            print(f"✅ 邀请码 {invite_code} 注册成功！")
            print(f"   用户 ID: {response.json()['id']}")
        else:
            error_detail = response.json().get('detail', '未知错误')
            print(f"❌ 邀请码 {invite_code} 注册失败：{error_detail}")

if __name__ == "__main__":
    test_register()
