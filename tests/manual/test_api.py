import requests

BASE_URL = "http://localhost:8000"

def test_register():
    print("测试用户注册...")
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "name": "testuser",
        "password": "test123",
        "invite_code": "HEALTH2024"
    }
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_login():
    print("\n测试用户登录...")
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "testuser",
        "password": "test123"
    }
    try:
        response = requests.post(url, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return response.status_code == 200, response.json().get("access_token")
    except Exception as e:
        print(f"错误: {e}")
        return False, None

def test_health_check():
    print("\n测试健康检查...")
    url = f"{BASE_URL}/"
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("大学生健康系统 API 测试")
    print("=" * 50)

    test_health_check()
    test_register()
    success, token = test_login()

    if success:
        print(f"\n✅ 测试成功！Token: {token[:20]}...")
    else:
        print("\n❌ 测试失败")
