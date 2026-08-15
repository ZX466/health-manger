"""
中医舌诊分析模块
基于云端视觉模型的舌象特征提取和中医体质辨识
需要配置 ARK_API_KEY 和 ARK_MODEL_ID 以启用云端分析
"""

import os
from typing import Optional

from tongue.feature_mapping import (
    TONGUE_COLOR_DETAILS, COATING_COLOR_DETAILS,
    COATING_THICKNESS_DESCRIPTIONS, TONGUE_SHAPE_DESCRIPTIONS,
    MOISTURE_LEVEL_DESCRIPTIONS, TCM_SYNDROMES,
)

import logging

logger = logging.getLogger(__name__)

# 以下数据统一由 feature_mapping.py 提供，此处保留向后兼容别名
TONGUE_COLORS = TONGUE_COLOR_DETAILS
COATING_COLORS = COATING_COLOR_DETAILS
COATING_THICKNESS = COATING_THICKNESS_DESCRIPTIONS
TONGUE_SHAPES = TONGUE_SHAPE_DESCRIPTIONS
MOISTURE_LEVELS = MOISTURE_LEVEL_DESCRIPTIONS

_cloud_analyzer = None


def _get_cloud_analyzer():
    """懒加载云端分析器"""
    global _cloud_analyzer
    if _cloud_analyzer is None:
        try:
            from tongue.cloud_analyzer import cloud_analyzer
            _cloud_analyzer = cloud_analyzer
            if _cloud_analyzer.is_configured:
                logger.info(f"云端 ARK 分析器就绪 (模型: {_cloud_analyzer.model_id})")
            else:
                logger.warning("云端 ARK 未配置，将在 .env 中设置 ARK_API_KEY 和 ARK_MODEL_ID 后启用")
        except ImportError:
            logger.warning("未安装云端分析模块，请确保 cloud_tongue_analyzer.py 存在")
    return _cloud_analyzer


def analyze_tongue_image(image_path: str, vision_config: Optional[dict] = None) -> dict:
    """
    分析舌象图像

    Args:
        image_path: 舌象图像文件路径
        vision_config: 用户自定义视觉模型配置 {provider, base_url, model, api_key}；
                       为空时回退默认 ARK 视觉模型。

    Returns:
        舌诊分析结果字典

    Raises:
        FileNotFoundError: 图像文件不存在
        RuntimeError: 云端分析服务不可用或调用失败
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图像文件不存在：{image_path}")

    # 用户配置了视觉模型则用之，否则回退默认 ARK
    if vision_config and vision_config.get("api_key") and vision_config.get("model"):
        from tongue.cloud_analyzer import CloudTongueAnalyzer

        cloud = CloudTongueAnalyzer(
            api_key=vision_config["api_key"],
            model_id=vision_config["model"],
            base_url=vision_config.get("base_url"),
        )
    else:
        cloud = _get_cloud_analyzer()
        if not cloud or not cloud.is_configured:
            raise RuntimeError("分析服务暂不可用：未配置视觉模型，请在 AI 设置或 .env 中配置")

    try:
        ai_result = cloud.analyze(image_path)
    except Exception as e:
        logger.error(f"云端分析失败：{e}")
        raise RuntimeError(f"分析服务暂不可用：云端分析请求失败 ({e})") from e

    tongue_color = ai_result.get('tongue_color', '淡红')
    coating_color = ai_result.get('coating_color', '白苔')
    coating_thickness = ai_result.get('coating_thickness', '薄苔')
    has_cracks = ai_result.get('has_cracks', False)
    has_teeth_marks = ai_result.get('has_teeth_marks', False)
    tongue_shape = ai_result.get('tongue_shape', '正常')
    moisture_level = ai_result.get('moisture_level', '正常')
    tongue_spirit = ai_result.get('tongue_spirit', '荣润')
    confidence = ai_result.get('confidence', 0.85)

    logger.info(f"云端 ARK 分析结果：舌色={tongue_color}, 苔色={coating_color}, 舌形={tongue_shape}, 置信度={confidence}")

    overall_type, tcm_syndrome = _determine_overall_type(
        tongue_color, coating_color, coating_thickness,
        has_cracks, has_teeth_marks, tongue_shape, moisture_level
    )

    health_advice = _generate_health_advice(tcm_syndrome)
    diet_suggestion = _generate_diet_suggestion(tcm_syndrome)
    lifestyle_advice = _generate_lifestyle_advice(tcm_syndrome)

    details = [
        {"feature": "舌色", "value": tongue_color, "desc": TONGUE_COLORS.get(tongue_color, {"desc": "未知"})["desc"]},
        {"feature": "苔色", "value": coating_color, "desc": COATING_COLORS.get(coating_color, {"desc": "未知"})["desc"]},
        {"feature": "苔质", "value": coating_thickness, "desc": COATING_THICKNESS.get(coating_thickness, "未知")},
        {"feature": "舌形", "value": tongue_shape, "desc": TONGUE_SHAPES.get(tongue_shape, "未知")},
        {"feature": "润燥", "value": moisture_level, "desc": MOISTURE_LEVELS.get(moisture_level, "未知")},
        {"feature": "裂纹", "value": "有" if has_cracks else "无", "desc": ""},
        {"feature": "齿痕", "value": "有" if has_teeth_marks else "无", "desc": ""}
    ]

    return {
        "tongue_color": tongue_color,
        "coating_color": coating_color,
        "coating_thickness": coating_thickness,
        "has_cracks": has_cracks,
        "has_teeth_marks": has_teeth_marks,
        "tongue_shape": tongue_shape,
        "moisture_level": moisture_level,
        "tongue_spirit": tongue_spirit,
        "overall_type": overall_type,
        "confidence_score": confidence,
        "tcm_syndrome": TCM_SYNDROMES.get(tcm_syndrome, {"name": "未知"})["name"],
        "health_advice": health_advice,
        "diet_suggestion": diet_suggestion,
        "lifestyle_advice": lifestyle_advice,
        "details": details,
        "is_ai_analysis": True,
    }


def _determine_overall_type(tongue_color, coating_color, thickness, cracks, teeth_marks, shape, moisture) -> tuple:
    """判断总体类型和中医证型"""
    score = 0

    if tongue_color == "淡红":
        score += 20
    elif tongue_color in ["红", "绛红"]:
        score -= 10
    elif tongue_color in ["淡白", "青紫"]:
        score -= 15

    if coating_color == "白苔" and thickness == "薄苔":
        score += 15
    elif coating_color == "黄苔":
        score -= 10
    elif coating_color in ["灰黑苔"]:
        score -= 15

    if not cracks and not teeth_marks:
        score += 10
    if shape == "正常":
        score += 15
    elif shape in ["胖大", "齿痕"]:
        score -= 5
    elif shape in ["瘦薄", "裂纹"]:
        score -= 10

    if moisture == "正常":
        score += 10
    elif moisture in ["干燥"]:
        score -= 8
    elif moisture == "滑润":
        score -= 5

    if score >= 60:
        return "正常舌象", "normal"
    elif score >= 40:
        if tongue_color in ["淡白"]:
            return "偏虚寒舌象", "qi_deficiency"
        elif tongue_color in ["红", "绛红"]:
            return "偏实热舌象", "yin_deficiency"
        elif teeth_marks or shape in ["胖大", "齿痕"]:
            return "痰湿舌象", "phlegm_dampness"
        else:
            return "轻度异常舌象", "qi_deficiency"
    else:
        if tongue_color == "青紫":
            return "血瘀舌象", "blood_stasis"
        elif coating_color == "黄苔" and thickness in ["厚苔", "腻苔"]:
            return "湿热舌象", "damp_heat"
        elif tongue_color == "淡白":
            return "阳虚舌象", "yang_deficiency"
        else:
            return "异常舌象", "qi_deficiency"


def _generate_health_advice(syndrome: str) -> str:
    advices = {
        "normal": "您的舌象显示身体状况良好，阴阳气血调和。建议保持健康的生活方式，定期进行健康检查。",
        "qi_deficiency": "舌象提示气虚体质，建议适当补气养血。可多食用山药、红枣、黄芪等补气食物，避免过度劳累。",
        "yang_deficiency": "舌象提示阳虚体质，建议注意保暖，避免生冷食物。可适量食用羊肉、生姜、桂圆等温补食物。",
        "yin_deficiency": "舌象提示阴虚体质，建议滋阴降火。多食用银耳、百合、梨等滋阴润燥之品，保证充足睡眠。",
        "phlegm_dampness": "舌象提示痰湿体质，建议健脾祛湿。饮食清淡，少吃油腻甜食，可食用薏米、赤小豆、冬瓜等。",
        "damp_heat": "舌象提示湿热内蕴，建议清热利湿。饮食清淡，忌辛辣油腻，多饮水，可食用绿豆、苦瓜等。",
        "blood_stasis": "舌象提示血瘀倾向，建议活血化瘀。适度运动促进血液循环，可食用山楂、黑木耳、玫瑰花茶等。",
        "qi_stagnation": "舌象提示气机郁滞，建议疏肝解郁。保持心情舒畅，适度运动，可饮用玫瑰花茶、菊花茶等。"
    }
    return advices.get(syndrome, advices["normal"])


def _generate_diet_suggestion(syndrome: str) -> str:
    suggestions = {
        "normal": "均衡饮食，五谷杂粮搭配，多吃新鲜蔬菜水果，适量摄入优质蛋白质。",
        "qi_deficiency": "推荐：小米粥、山药炖鸡、红枣桂圆汤、黄芪党参茶。避免：生冷寒凉食物。",
        "yang_deficiency": "推荐：当归生姜羊肉汤、韭菜炒蛋、核桃芝麻糊。避免：冰饮、西瓜、苦瓜等寒凉食物。",
        "yin_deficiency": "推荐：银耳莲子羹、百合雪梨汤、桑葚膏、枸杞菊花茶。避免：辛辣烧烤食物。",
        "phlegm_dampness": "推荐：薏米红豆粥、冬瓜排骨汤、陈皮普洱茶。避免：甜食、油炸食品、肥肉。",
        "damp_heat": "推荐：绿豆汤、苦瓜炒蛋、冬瓜海带汤、荷叶茶。避免：辛辣、油腻、甜食、酒类。",
        "blood_stasis": "推荐：山楂红糖水、黑木耳凉拌、三七粉、玫瑰花茶。避免：高脂肪食物。",
        "qi_stagnation": "推荐：玫瑰花茶、茉莉花茶、柑橘类水果、芹菜炒木耳。避免：过度饮酒、情绪化进食。"
    }
    return suggestions.get(syndrome, suggestions["normal"])


def _generate_lifestyle_advice(syndrome: str) -> str:
    suggestions = {
        "normal": "保持规律作息，每天运动 30 分钟以上，保持良好心态，定期体检。",
        "qi_deficiency": "避免过度劳累，保证充足睡眠 (7-8 小时)，选择温和的运动如太极拳、散步。",
        "yang_deficiency": "注意保暖，尤其是腹部和脚部。可选择晨练晒太阳，温水泡脚促进血液循环。",
        "yin_deficiency": "避免熬夜，晚上 11 点前入睡。选择舒缓运动如瑜伽、太极，避免剧烈出汗过多。",
        "phlegm_dampness": "保持环境干燥通风，坚持有氧运动出汗排湿。规律作息，避免久坐不动。",
        "damp_heat": "保持环境清爽，勤洗澡换衣。适度运动但避免暴晒，保持大便通畅。",
        "blood_stasis": "坚持规律运动，特别是有氧运动。注意保暖，避免受寒。保持心情愉快。",
        "qi_stagnation": "学会释放压力，培养兴趣爱好。多参加社交活动，保持乐观心态。规律作息不熬夜。"
    }
    return suggestions.get(syndrome, suggestions["normal"])


def get_tongue_color_info(color: str) -> dict:
    """获取舌色信息"""
    return TONGUE_COLORS.get(color, {"color": "#CCCCCC", "desc": "未知"})


def get_coating_color_info(color: str) -> dict:
    """获取苔色信息"""
    return COATING_COLORS.get(color, {"color": "#CCCCCC", "desc": "未知"})


def get_syndrome_info(syndrome_key: str) -> dict:
    """获取中医证型信息"""
    return TCM_SYNDROMES.get(syndrome_key, {"name": "未知", "desc": "无法确定"})
