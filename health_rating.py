"""
健康综合评级模块
基于多维度健康评估的评级体系
"""

from constants import (
    BMI_UNDERWEIGHT, BMI_NORMAL_UPPER, BMI_OVERWEIGHT_UPPER, BMI_THIN,
    BP_SYSTOLIC_LOW, BP_SYSTOLIC_NORMAL, BP_SYSTOLIC_ELEVATED, BP_SYSTOLIC_HIGH,
    BP_DIASTOLIC_LOW, BP_DIASTOLIC_NORMAL, BP_DIASTOLIC_ELEVATED, BP_DIASTOLIC_HIGH,
    HR_LOW, HR_HIGH, HR_VERY_LOW, HR_VERY_HIGH, HR_EXTREME_LOW, HR_EXTREME_HIGH,
    TEMP_LOW, TEMP_NORMAL_LOW, TEMP_NORMAL_HIGH, TEMP_FEVER, TEMP_HIGH_FEVER,
)


def calculate_health_rating(record) -> tuple[str, int, str]:
    """
    计算健康综合评级
    
    返回: (评级名称, 分数, 详细说明)
    
    评级体系：
    - 优秀 (95-100分): 所有指标正常
    - 良好 (80-94分): 大部分指标正常
    - 中等 (60-79分): 部分指标异常
    - 较差 (40-59分): 多项指标异常
    - 危险 (0-39分): 健康状况较差
    """
    
    scores = []
    details = []
    
    # BMI 评分 (25分满分)
    bmi_score, bmi_detail = _calculate_bmi_score(record)
    scores.append(bmi_score)
    details.append(f"BMI{bmi_detail}")
    
    # 血压评分 (25分满分)
    bp_score, bp_detail = _calculate_blood_pressure_score(record)
    scores.append(bp_score)
    details.append(f"血压{bp_detail}")
    
    # 心率评分 (25分满分)
    hr_score, hr_detail = _calculate_heart_rate_score(record)
    scores.append(hr_score)
    details.append(f"心率{hr_detail}")
    
    # 体温评分 (25分满分)
    temp_score, temp_detail = _calculate_temperature_score(record)
    scores.append(temp_score)
    details.append(f"体温{temp_detail}")
    
    # 计算总分
    total_score = sum(scores)
    
    # 确定评级
    if total_score >= 95:
        rating = "优秀"
    elif total_score >= 80:
        rating = "良好"
    elif total_score >= 60:
        rating = "中等"
    elif total_score >= 40:
        rating = "较差"
    else:
        rating = "危险"
    
    return rating, total_score, f"综合评分{total_score}分 ({'/'.join(details)})"


def _calculate_bmi_score(record) -> tuple[int, str]:
    """计算BMI得分"""
    if not record.bmi:
        return 0, "未检测(0分)"
    
    bmi = record.bmi
    
    if BMI_UNDERWEIGHT <= bmi < BMI_NORMAL_UPPER:
        return 25, f"{bmi:.1f}满分(25分)"
    elif BMI_NORMAL_UPPER <= bmi < BMI_OVERWEIGHT_UPPER:
        return 18, f"{bmi:.1f}偏高(18分)"
    elif bmi >= BMI_OVERWEIGHT_UPPER:
        return 10, f"{bmi:.1f}肥胖(10分)"
    elif BMI_THIN <= bmi < BMI_UNDERWEIGHT:
        return 15, f"{bmi:.1f}偏瘦(15分)"
    else:
        return 8, f"{bmi:.1f}过轻(8分)"


def _calculate_blood_pressure_score(record) -> tuple[int, str]:
    """计算血压得分"""
    systolic = record.blood_pressure_systolic
    diastolic = record.blood_pressure_diastolic
    
    if not systolic or not diastolic:
        return 0, "未检测(0分)"
    
    # 低血压（任一臂低于下限）必须前置，否则被“正常/偏高”分支遮蔽
    if systolic < BP_SYSTOLIC_LOW or diastolic < BP_DIASTOLIC_LOW:
        return 15, f"{systolic}/{diastolic}偏低(15分)"
    # 正常：收缩压 < 120 且 舒张压 < 80
    if systolic < BP_SYSTOLIC_NORMAL and diastolic < BP_DIASTOLIC_NORMAL:
        return 25, f"{systolic}/{diastolic}正常(25分)"
    # 正常高值：收缩压 120-139 或 舒张压 80-89
    elif (BP_SYSTOLIC_NORMAL <= systolic < BP_SYSTOLIC_ELEVATED
          or BP_DIASTOLIC_NORMAL <= diastolic < BP_DIASTOLIC_ELEVATED):
        return 20, f"{systolic}/{diastolic}偏高(20分)"
    # 高血压1级：收缩压 140-159 或 舒张压 90-99
    elif (BP_SYSTOLIC_ELEVATED <= systolic < BP_SYSTOLIC_HIGH
          or BP_DIASTOLIC_ELEVATED <= diastolic < BP_DIASTOLIC_HIGH):
        return 12, f"{systolic}/{diastolic}高血压1级(12分)"
    # 高血压2级：收缩压 >= 160 或 舒张压 >= 100
    elif systolic >= BP_SYSTOLIC_HIGH or diastolic >= BP_DIASTOLIC_HIGH:
        return 5, f"{systolic}/{diastolic}高血压2级(5分)"
    else:
        return 20, f"{systolic}/{diastolic}(20分)"


def _calculate_heart_rate_score(record) -> tuple[int, str]:
    """计算心率得分"""
    if not record.heart_rate:
        return 0, "未检测(0分)"
    
    hr = record.heart_rate
    
    if HR_LOW <= hr <= HR_HIGH:
        return 25, f"{hr}正常(25分)"
    elif HR_VERY_LOW <= hr < HR_LOW or HR_HIGH < hr <= HR_VERY_HIGH:
        return 18, f"{hr}略异常(18分)"
    elif HR_EXTREME_LOW <= hr < HR_VERY_LOW or HR_VERY_HIGH < hr <= HR_EXTREME_HIGH:
        return 10, f"{hr}异常(10分)"
    else:
        return 5, f"{hr}严重异常(5分)"


def _calculate_temperature_score(record) -> tuple[int, str]:
    """计算体温得分"""
    if not record.temperature:
        return 0, "未检测(0分)"
    
    temp = record.temperature
    
    if TEMP_NORMAL_LOW <= temp <= TEMP_NORMAL_HIGH:
        return 25, f"{temp}°C正常(25分)"
    elif TEMP_NORMAL_HIGH < temp <= TEMP_FEVER:
        return 18, f"{temp}°C略高(18分)"
    elif TEMP_FEVER < temp <= TEMP_HIGH_FEVER:
        return 10, f"{temp}°C发烧(10分)"
    elif temp > TEMP_HIGH_FEVER:
        return 5, f"{temp}°C高烧(5分)"
    elif TEMP_LOW <= temp < TEMP_NORMAL_LOW:
        return 15, f"{temp}°C略低(15分)"
    else:
        return 5, f"{temp}°C过低(5分)"


def get_rating_emoji(rating: str) -> str:
    """获取评级表情"""
    emojis = {
        "优秀": "🏆",
        "良好": "🥇",
        "中等": "👤",
        "较差": "😐",
        "危险": "❌"
    }
    return emojis.get(rating, "❓")


def get_rating_color(rating: str) -> str:
    """获取评级颜色"""
    colors = {
        "优秀": "#52c41a",      # 绿色
        "良好": "#1890ff",    # 蓝色
        "中等": "#faad14",  # 橙色
        "较差": "#fa8c16",    # 深橙色
        "危险": "#f5222d"   # 红色
    }
    return colors.get(rating, "#999999")


def get_rating_bg_color(rating: str) -> str:
    """获取评级背景颜色"""
    colors = {
        "优秀": "#f6ffed",      # 浅绿
        "良好": "#e6f7ff",    # 浅蓝
        "中等": "#fffbe6",  # 浅黄
        "较差": "#fff7e6",     # 浅橙
        "危险": "#fff1f0"   # 浅红
    }
    return colors.get(rating, "#f5f5f5")
