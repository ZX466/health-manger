"""
测试完善后的 API 功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("开始测试健康系统 API")
    print("=" * 60)
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"状态码：{response.status_code}")
    print(f"响应：{response.json()}")
    
    # 2. 测试获取食物列表
    print("\n2. 测试获取食物列表...")
    response = requests.get(f"{BASE_URL}/api/food/foods")
    print(f"状态码：{response.status_code}")
    if response.status_code == 200:
        foods = response.json()
        print(f"获取到 {len(foods)} 种食物")
        for food in foods[:5]:
            print(f"  - {food['name']}: {food['calories_per_100g']} kcal/100g")
    
    # 3. 测试获取运动列表
    print("\n3. 测试获取运动列表...")
    response = requests.get(f"{BASE_URL}/api/sport/sports")
    print(f"状态码：{response.status_code}")
    if response.status_code == 200:
        sports = response.json()
        print(f"获取到 {len(sports)} 种运动")
        for sport in sports[:5]:
            print(f"  - {sport['name']}: {sport['calories_per_hour']} kcal/h")
    
    # 4. 测试注册（使用已存在的测试用户）
    print("\n4. 测试用户登录...")
    login_data = {
        "username": "testuser",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("登录成功！")
        print(f"Token: {token[:50]}...")
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # 5. 测试获取当前用户信息
        print("\n5. 测试获取当前用户信息...")
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print(f"响应：{response.json()}")
        
        # 6. 测试创建健康记录
        print("\n6. 测试创建健康记录...")
        health_record = {
            "height": 175,
            "weight": 70,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 75,
            "temperature": 36.5,
            "sleep_hours": 7.5,
            "exercise_frequency": "每周 3 次",
            "diet_habit": "均衡饮食"
        }
        response = requests.post(f"{BASE_URL}/api/health/records", json=health_record, headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print("健康记录创建成功！")
            print(f"BMI: {response.json().get('bmi')}")
        
        # 7. 测试获取健康预警
        print("\n7. 测试健康预警检查...")
        response = requests.post(f"{BASE_URL}/api/warning/check", headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print(f"响应：{response.json()}")
        
        # 8. 测试获取预警列表
        print("\n8. 测试获取预警列表...")
        response = requests.get(f"{BASE_URL}/api/warning/list", headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            warnings = response.json()
            print(f"获取到 {len(warnings)} 条预警")
        
        # 9. 测试创建饮食记录
        print("\n9. 测试创建饮食记录...")
        food_record = {
            "food_id": 1,
            "quantity_grams": 200,
            "meal_type": "breakfast"
        }
        response = requests.post(f"{BASE_URL}/api/food/records", json=food_record, headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print("饮食记录创建成功！")
            print(f"摄入热量：{response.json().get('calories')} kcal")
        
        # 10. 测试创建运动记录
        print("\n10. 测试创建运动记录...")
        sport_record = {
            "sport_id": 1,
            "duration_minutes": 30,
            "notes": "晨跑"
        }
        response = requests.post(f"{BASE_URL}/api/sport/records", json=sport_record, headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print("运动记录创建成功！")
            print(f"消耗热量：{response.json().get('calories_burned')} kcal")
        
        # 11. 测试获取饮食统计
        print("\n11. 测试获取饮食统计...")
        response = requests.get(f"{BASE_URL}/api/food/records/stats", headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print(f"响应：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        # 12. 测试获取运动统计
        print("\n12. 测试获取运动统计...")
        response = requests.get(f"{BASE_URL}/api/sport/records/stats", headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print(f"响应：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        # 13. 测试 AI 健康分析（需要配置 DeepSeek API）
        print("\n13. 测试 AI 健康分析...")
        ai_request = {
            "request_content": "我最近感觉有点疲劳，有什么建议吗？",
            "analysis_type": "健康咨询"
        }
        response = requests.post(f"{BASE_URL}/api/ai/analysis", json=ai_request, headers=headers)
        print(f"状态码：{response.status_code}")
        if response.status_code == 200:
            print("AI 分析成功！")
            print(f"响应：{response.json().get('response_content', '')[:100]}...")
        elif response.status_code == 500:
            print(f"AI 服务未配置或不可用：{response.json().get('detail', '')}")
        else:
            print(f"错误：{response.json()}")
        
        print("\n" + "=" * 60)
        print("API 测试完成！")
        print("=" * 60)
    else:
        print(f"登录失败：{response.json()}")
        print("请确保已创建测试用户")

if __name__ == "__main__":
    test_api()
