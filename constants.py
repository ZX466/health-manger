"""
医学阈值常量 — 单源真相
基于中国临床诊断标准，所有健康评估模块必须从此处引用。
"""

# ── BMI ──────────────────────────────────────────────
BMI_UNDERWEIGHT = 18.5
BMI_NORMAL_UPPER = 24.0
BMI_OVERWEIGHT_UPPER = 28.0
BMI_THIN = 17.0  # 严重偏瘦分界

# ── 血压 (mmHg) ─────────────────────────────────────
BP_SYSTOLIC_LOW = 90
BP_SYSTOLIC_NORMAL = 120
BP_SYSTOLIC_ELEVATED = 140
BP_SYSTOLIC_HIGH = 160

BP_DIASTOLIC_LOW = 60
BP_DIASTOLIC_NORMAL = 80
BP_DIASTOLIC_ELEVATED = 90
BP_DIASTOLIC_HIGH = 100

# ── 心率 (次/分钟) ──────────────────────────────────
HR_LOW = 60
HR_HIGH = 100
HR_VERY_LOW = 50
HR_VERY_HIGH = 110
HR_EXTREME_LOW = 40
HR_EXTREME_HIGH = 120

# ── 体温 (°C) ───────────────────────────────────────
TEMP_LOW = 35.0
TEMP_NORMAL_LOW = 36.0
TEMP_NORMAL_HIGH = 37.3
TEMP_FEVER = 37.5
TEMP_HIGH_FEVER = 38.0
