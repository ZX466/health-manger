"""
大学生健康管理系统 - 全面功能测试
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name):
        self.total += 1
        self.passed += 1
        print(f"  ✅ {name}")

    def add_fail(self, name, reason):
        self.total += 1
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ {name} - {reason}")

results = TestResults()

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_subheader(title):
    print(f"\n--- {title} ---")

print("\n大学生健康管理系统 - 全面功能测试")
print(f"测试时间: {TIMESTAMP}")
print(f"测试地址: {BASE_URL}")

# 获取Token
def get_auth():
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "testuser",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

token = get_auth()
headers = {"Authorization": f"Bearer {token}"}

print_header("1. 用户认证系统测试")

# 1.1 健康检查
print_subheader("1.1 健康检查")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200 and response.json().get("status") == "healthy":
        results.add_pass("健康检查端点")
    else:
        results.add_fail("健康检查端点", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("健康检查端点", str(e))

# 1.2 用户登录
print_subheader("1.2 用户登录")
try:
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "testuser",
        "password": "test123"
    })
    if response.status_code == 200 and "access_token" in response.json():
        results.add_pass("有效用户登录")
    else:
        results.add_fail("有效用户登录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("有效用户登录", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    if response.status_code == 401:
        results.add_pass("无效密码登录拒绝")
    else:
        results.add_fail("无效密码登录拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("无效密码登录拒绝", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "nonexistent",
        "password": "test123"
    })
    if response.status_code == 401:
        results.add_pass("不存在用户登录拒绝")
    else:
        results.add_fail("不存在用户登录拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("不存在用户登录拒绝", str(e))

# 1.3 Token验证
print_subheader("1.3 Token验证")
try:
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200 and "id" in response.json():
        results.add_pass("获取当前用户信息")
        user_info = response.json()
    else:
        results.add_fail("获取当前用户信息", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取当前用户信息", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/auth/me")
    if response.status_code == 401:
        results.add_pass("无Token访问拒绝")
    else:
        results.add_fail("无Token访问拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("无Token访问拒绝", str(e))

# 1.4 用户注册
print_subheader("1.4 用户注册")
timestamp = int(time.time())
try:
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": f"newuser_{timestamp}",
        "password": "newpass123",
        "invite_code": "HEALTH2024"
    })
    if response.status_code == 200:
        results.add_pass("新用户注册")
    else:
        results.add_fail("新用户注册", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("新用户注册", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": f"newuser_{timestamp}",
        "password": "newpass123",
        "invite_code": "HEALTH2024"
    })
    if response.status_code == 400 or response.status_code == 409:
        results.add_pass("重复用户名拒绝")
    else:
        results.add_fail("重复用户名拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("重复用户名拒绝", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "baduser",
        "password": "short",
        "invite_code": "WRONG"
    })
    if response.status_code == 400:
        results.add_pass("无效邀请码拒绝")
    else:
        results.add_fail("无效邀请码拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("无效邀请码拒绝", str(e))

print_header("2. 健康记录管理测试")

# 2.1 创建健康记录
print_subheader("2.1 创建健康记录")
try:
    response = requests.post(f"{BASE_URL}/api/health/records", json={
        "height": 175,
        "weight": 70,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "heart_rate": 75,
        "temperature": 36.5,
        "sleep_hours": 7.5,
        "exercise_frequency": "每周3次",
        "diet_habit": "均衡饮食"
    }, headers=headers)
    if response.status_code == 200 and "bmi" in response.json():
        results.add_pass("创建健康记录")
        health_record_id = response.json()["id"]
    else:
        results.add_fail("创建健康记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("创建健康记录", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/health/records", json={
        "height": 175,
        "weight": 70
    }, headers=headers)
    if response.status_code == 200:
        results.add_pass("创建最小化健康记录")
    else:
        results.add_fail("创建最小化健康记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("创建最小化健康记录", str(e))

# 2.2 查询健康记录
print_subheader("2.2 查询健康记录")
try:
    response = requests.get(f"{BASE_URL}/api/health/records", headers=headers)
    if response.status_code == 200 and isinstance(response.json(), list):
        results.add_pass("获取健康记录列表")
    else:
        results.add_fail("获取健康记录列表", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取健康记录列表", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/health/records/{health_record_id}", headers=headers)
    if response.status_code == 200 and response.json()["id"] == health_record_id:
        results.add_pass("获取单条健康记录")
    else:
        results.add_fail("获取单条健康记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取单条健康记录", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/health/records/99999", headers=headers)
    if response.status_code == 404:
        results.add_pass("不存在的记录返回404")
    else:
        results.add_fail("不存在的记录返回404", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("不存在的记录返回404", str(e))

# 2.3 健康分析
print_subheader("2.3 健康分析")
try:
    response = requests.get(f"{BASE_URL}/api/health/analysis/latest", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取最新健康分析")
    else:
        results.add_fail("获取最新健康分析", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取最新健康分析", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/health/analysis/history", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取健康分析历史")
    else:
        results.add_fail("获取健康分析历史", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取健康分析历史", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/health/rating/latest", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取健康评级")
        rating_data = response.json()
    else:
        results.add_fail("获取健康评级", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取健康评级", str(e))

# 2.4 删除健康记录
print_subheader("2.4 删除健康记录")
try:
    response = requests.delete(f"{BASE_URL}/api/health/records/{health_record_id}", headers=headers)
    if response.status_code == 200:
        results.add_pass("删除健康记录")
    else:
        results.add_fail("删除健康记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("删除健康记录", str(e))

try:
    response = requests.delete(f"{BASE_URL}/api/health/records/99999", headers=headers)
    if response.status_code == 404:
        results.add_pass("删除不存在的记录返回404")
    else:
        results.add_fail("删除不存在的记录返回404", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("删除不存在的记录返回404", str(e))

print_header("3. 饮食管理系统测试")

# 3.1 获取食物列表
print_subheader("3.1 食物列表")
try:
    response = requests.get(f"{BASE_URL}/api/food/foods")
    if response.status_code == 200 and len(response.json()) > 0:
        results.add_pass("获取食物列表")
        foods = response.json()
    else:
        results.add_fail("获取食物列表", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取食物列表", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/food/foods", params={"search": "米"})
    if response.status_code == 200:
        results.add_pass("搜索食物")
    else:
        results.add_fail("搜索食物", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("搜索食物", str(e))

# 3.2 创建饮食记录
print_subheader("3.2 饮食记录")
try:
    food_id = foods[0]["id"] if foods else 1
    response = requests.post(f"{BASE_URL}/api/food/records", json={
        "food_id": food_id,
        "quantity_grams": 200,
        "meal_type": "breakfast"
    }, headers=headers)
    if response.status_code == 200:
        results.add_pass("创建饮食记录")
    else:
        results.add_fail("创建饮食记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("创建饮食记录", str(e))

# 3.3 饮食统计
print_subheader("3.3 饮食统计")
try:
    response = requests.get(f"{BASE_URL}/api/food/records/stats", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取饮食统计")
    else:
        results.add_fail("获取饮食统计", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取饮食统计", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/food/records", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取饮食记录列表")
    else:
        results.add_fail("获取饮食记录列表", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取饮食记录列表", str(e))

print_header("4. 运动管理系统测试")

# 4.1 获取运动列表
print_subheader("4.1 运动列表")
try:
    response = requests.get(f"{BASE_URL}/api/sport/sports")
    if response.status_code == 200 and len(response.json()) > 0:
        results.add_pass("获取运动列表")
        sports = response.json()
    else:
        results.add_fail("获取运动列表", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取运动列表", str(e))

# 4.2 创建运动记录
print_subheader("4.2 运动记录")
try:
    sport_id = sports[0]["id"] if sports else 1
    response = requests.post(f"{BASE_URL}/api/sport/records", json={
        "sport_id": sport_id,
        "duration_minutes": 30
    }, headers=headers)
    if response.status_code == 200:
        results.add_pass("创建运动记录")
    else:
        results.add_fail("创建运动记录", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("创建运动记录", str(e))

# 4.3 运动统计
print_subheader("4.3 运动统计")
try:
    response = requests.get(f"{BASE_URL}/api/sport/records/stats", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取运动统计")
    else:
        results.add_fail("获取运动统计", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取运动统计", str(e))

print_header("5. 健康预警系统测试")

# 5.1 健康预警检查
print_subheader("5.1 预警检查")
try:
    response = requests.post(f"{BASE_URL}/api/warning/check", headers=headers)
    if response.status_code == 200:
        results.add_pass("健康预警检查")
    else:
        results.add_fail("健康预警检查", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("健康预警检查", str(e))

# 5.2 获取预警列表
print_subheader("5.2 预警列表")
try:
    response = requests.get(f"{BASE_URL}/api/warning/list", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取预警列表")
    else:
        results.add_fail("获取预警列表", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取预警列表", str(e))

# 5.3 预警统计
print_subheader("5.3 预警统计")
try:
    response = requests.get(f"{BASE_URL}/api/warning/stats", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取预警统计")
    else:
        results.add_fail("获取预警统计", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取预警统计", str(e))

# 5.4 标记预警已读
print_subheader("5.4 标记已读")
try:
    warnings = requests.get(f"{BASE_URL}/api/warning/list", headers=headers).json()
    if warnings and len(warnings) > 0:
        warning_id = warnings[0]["id"]
        response = requests.put(f"{BASE_URL}/api/warning/read/{warning_id}", headers=headers)
        if response.status_code == 200:
            results.add_pass("标记预警已读")
        else:
            results.add_fail("标记预警已读", f"状态码:{response.status_code}")
    else:
        results.add_pass("标记预警已读 (无预警)")
except Exception as e:
    results.add_fail("标记预警已读", str(e))

print_header("6. AI健康分析测试")

# 6.1 创建AI分析
print_subheader("6.1 AI分析")
try:
    response = requests.post(f"{BASE_URL}/api/ai/analysis", json={
        "request_content": "我最近感觉有点疲劳，请给我一些健康建议",
        "analysis_type": "健康咨询"
    }, headers=headers)
    if response.status_code == 200:
        results.add_pass("AI健康分析")
        ai_result = response.json()
    elif response.status_code == 500 and "API" in response.text:
        results.add_fail("AI健康分析", "API未配置")
    else:
        results.add_fail("AI健康分析", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("AI健康分析", str(e))

# 6.2 快速分析
print_subheader("6.2 快速分析")
try:
    response = requests.post(f"{BASE_URL}/api/ai/quick-analysis", headers=headers)
    if response.status_code == 200:
        results.add_pass("快速健康分析")
    elif response.status_code == 500 and "API" in response.text:
        results.add_fail("快速健康分析", "API未配置")
    else:
        results.add_fail("快速健康分析", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("快速健康分析", str(e))

# 6.3 AI历史
print_subheader("6.3 AI历史")
try:
    response = requests.get(f"{BASE_URL}/api/ai/analysis/history", headers=headers)
    if response.status_code == 200:
        results.add_pass("获取AI分析历史")
    else:
        results.add_fail("获取AI分析历史", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("获取AI分析历史", str(e))

print_header("7. 边界情况和错误处理测试")

# 7.1 无效输入
print_subheader("7.1 输入验证")
try:
    response = requests.post(f"{BASE_URL}/api/health/records", json={
        "height": -100,
        "weight": -50
    }, headers=headers)
    if response.status_code == 200 or response.status_code == 422:
        results.add_pass("负数身高体重处理")
    else:
        results.add_fail("负数身高体重处理", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("负数身高体重处理", str(e))

try:
    response = requests.post(f"{BASE_URL}/api/sport/records", json={
        "sport_id": 1,
        "duration_minutes": 0
    }, headers=headers)
    if response.status_code == 200 or response.status_code == 400:
        results.add_pass("零时长运动处理")
    else:
        results.add_fail("零时长运动处理", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("零时长运动处理", str(e))

# 7.2 认证边界
print_subheader("7.2 认证边界")
try:
    response = requests.get(f"{BASE_URL}/api/health/records", headers={
        "Authorization": "Bearer invalid_token"
    })
    if response.status_code == 401:
        results.add_pass("无效Token拒绝")
    else:
        results.add_fail("无效Token拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("无效Token拒绝", str(e))

try:
    response = requests.get(f"{BASE_URL}/api/food/records", headers={
        "Authorization": "Bearer expired_or_invalid_token"
    })
    if response.status_code == 401:
        results.add_pass("过期Token拒绝")
    else:
        results.add_fail("过期Token拒绝", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("过期Token拒绝", str(e))

# 7.3 资源边界
print_subheader("7.3 资源访问")
try:
    response = requests.get(f"{BASE_URL}/api/health/records/abc", headers=headers)
    if response.status_code == 422 or response.status_code == 404:
        results.add_pass("非数字ID参数处理")
    else:
        results.add_fail("非数字ID参数处理", f"状态码:{response.status_code}")
except Exception as e:
    results.add_fail("非数字ID参数处理", str(e))

print_header("8. 数据完整性测试")

# 8.1 BMI计算验证
print_subheader("8.1 BMI计算")
bmi_test_cases = [
    (175, 70, 22.86),
    (180, 80, 24.69),
    (160, 50, 19.53),
]
for height, weight, expected_bmi in bmi_test_cases:
    try:
        response = requests.post(f"{BASE_URL}/api/health/records", json={
            "height": height,
            "weight": weight
        }, headers=headers)
        if response.status_code == 200:
            actual_bmi = response.json().get("bmi", 0)
            if abs(actual_bmi - expected_bmi) < 0.1:
                results.add_pass(f"BMI计算({height}cm/{weight}kg={expected_bmi})")
            else:
                results.add_fail(f"BMI计算({height}cm/{weight}kg)", f"期望:{expected_bmi},实际:{actual_bmi}")
        else:
            results.add_fail(f"BMI计算({height}cm/{weight}kg)", f"状态码:{response.status_code}")
    except Exception as e:
        results.add_fail(f"BMI计算({height}cm/{weight}kg)", str(e))

# 打印测试总结
print_header("测试结果汇总")
print(f"\n总计: {results.total}")
print(f"通过: {results.passed} ✅")
print(f"失败: {results.failed} ❌")
print(f"通过率: {results.passed/results.total*100:.1f}%")

if results.errors:
    print("\n失败详情:")
    for name, reason in results.errors:
        print(f"  - {name}: {reason}")

# 写入测试报告
report = f"""
================================================================================
                    大学生健康管理系统 - 测试报告
================================================================================

测试时间: {TIMESTAMP}
测试地址: {BASE_URL}

--------------------------------------------------------------------------------
一、测试结果汇总
--------------------------------------------------------------------------------
总计测试用例: {results.total}
通过: {results.passed}
失败: {results.failed}
通过率: {results.passed/results.total*100:.1f}%

--------------------------------------------------------------------------------
二、测试覆盖模块
--------------------------------------------------------------------------------
1. 用户认证系统 (注册、登录、Token验证)
2. 健康记录管理 (CRUD、健康分析、评级)
3. 饮食管理系统 (食物、记录、统计)
4. 运动管理系统 (运动、记录、统计)
5. 健康预警系统 (检查、列表、统计)
6. AI健康分析 (智能分析、快速分析)
7. 边界情况和错误处理
8. 数据完整性 (BMI计算等)

--------------------------------------------------------------------------------
三、测试用例详情
--------------------------------------------------------------------------------
"""

# 打印最终统计
pass_rate = results.passed/results.total*100
report += f"""
通过率: {pass_rate:.1f}%
状态: {"✅ 全部通过" if results.failed == 0 else "⚠️ 存在失败项"}

"""

if results.errors:
    report += "--------------------------------------------------------------------------------\n四、失败项详情\n--------------------------------------------------------------------------------\n"
    for name, reason in results.errors:
        report += f"- {name}: {reason}\n"

report += """
--------------------------------------------------------------------------------
五、系统状态
--------------------------------------------------------------------------------
"""

if results.failed == 0:
    report += "✅ 所有功能测试通过，系统可以正常部署使用\n"
else:
    report += f"⚠️ 存在 {results.failed} 个失败项，建议修复后再部署\n"

report += """
================================================================================
                              报告结束
================================================================================
"""

with open("d:/aidevelop/project7/tests/TEST_REPORT.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\n测试报告已保存到: tests/TEST_REPORT.md")
