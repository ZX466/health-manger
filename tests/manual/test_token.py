"""
调试 Token 问题
"""
import requests
from jose import jwt

BASE_URL = "http://localhost:8001"
import os
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = "HS256"

# 登录获取 token
login_data = {
    "username": "testuser",
    "password": "test123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
print(f"登录响应：{response.status_code}")
print(f"Token: {response.json()['access_token']}")

# 解码 token 查看内容
token = response.json()['access_token']
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"Token 解码成功：{payload}")
except Exception as e:
    print(f"Token 解码失败：{e}")

# 尝试使用 token 请求
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
print("\n请求 /api/auth/me:")
print(f"状态码：{response.status_code}")
print(f"响应：{response.text}")
