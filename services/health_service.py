from typing import Tuple

from constants import (
    BMI_UNDERWEIGHT, BMI_NORMAL_UPPER, BMI_OVERWEIGHT_UPPER,
    BP_SYSTOLIC_LOW, BP_SYSTOLIC_NORMAL, BP_SYSTOLIC_ELEVATED,
    BP_DIASTOLIC_LOW, BP_DIASTOLIC_NORMAL, BP_DIASTOLIC_ELEVATED,
)


def calculate_bmi(height: float, weight: float) -> float:
    if height <= 0 or weight <= 0:
        return 0.0
    height_m = height / 100
    return round(weight / (height_m * height_m), 2)


def analyze_bmi(bmi: float) -> Tuple[str, str]:
    if bmi < BMI_UNDERWEIGHT:
        return "偏瘦", "您的BMI偏低，建议加强营养摄入，适当增重。建议多食用富含蛋白质和碳水化合物的食物，如鸡蛋、牛奶、面包等。"
    elif BMI_UNDERWEIGHT <= bmi < BMI_NORMAL_UPPER:
        return "正常", "您的体重在正常范围内，请继续保持健康的饮食和运动习惯。"
    elif BMI_NORMAL_UPPER <= bmi < BMI_OVERWEIGHT_UPPER:
        return "偏胖", "您的BMI偏高，建议适当控制饮食，增加运动量。建议减少高热量食物摄入，增加有氧运动。"
    else:
        return "肥胖", "您的BMI过高，建议及时调整饮食结构，增加运动量，必要时咨询专业医生。"


def analyze_blood_pressure(systolic: int, diastolic: int) -> Tuple[str, str]:
    # 高血压必须优先于低血压判定：混合读数（如 170/55 严重高血压+低舒张压，
    # 或 85/90 低收缩压+高血压1级舒张压）应按更危险的高血压分级，而非遮蔽为偏低
    if systolic >= BP_SYSTOLIC_ELEVATED or diastolic >= BP_DIASTOLIC_ELEVATED:
        return "高血压", "您的血压过高，建议及时就医检查，遵循医生指导进行调理。"
    elif systolic < BP_SYSTOLIC_LOW or diastolic < BP_DIASTOLIC_LOW:
        return "低血压", "您的血压偏低，建议适当增加盐分摄入，多喝水，避免过度劳累。如有头晕等症状请及时就医。"
    elif systolic >= BP_SYSTOLIC_NORMAL or diastolic >= BP_DIASTOLIC_NORMAL:
        return "偏高", "您的血压偏高，建议减少盐分摄入，避免高脂肪食物，保持规律运动。"
    else:
        return "正常", "您的血压在正常范围内，请继续保持健康的生活方式。"
