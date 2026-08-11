"""
舌象特征映射模块
参考 TongueDiagnosis 项目的标准化特征映射设计
支持中英文标签和多维度分类
"""

TONGUE_COLOR_MAP = {
    "cn": {
        0: "淡白",
        1: "淡红",
        2: "红",
        3: "绛红",
        4: "青紫"
    },
    "en": {
        0: "Pale white",
        1: "Light red",
        2: "Red",
        3: "Crimson",
        4: "Bluish-purple"
    },
    "descriptions": {
        "淡白": "气血不足，阳虚",
        "淡红": "正常舌色，气血调和",
        "红": "热证，体内有热",
        "绛红": "热盛，阴虚火旺",
        "青紫": "血瘀或寒凝"
    }
}

COATING_COLOR_MAP = {
    "cn": {
        0: "白苔",
        1: "黄苔",
        2: "灰黑苔"
    },
    "en": {
        0: "White coating",
        1: "Yellow coating",
        2: "Gray-black coating"
    },
    "descriptions": {
        "白苔": "正常或寒证",
        "黄苔": "热证，脾胃湿热",
        "灰黑苔": "重证，寒热错杂"
    }
}

COATING_THICKNESS_MAP = {
    "cn": {
        0: "薄苔",
        1: "厚苔"
    },
    "en": {
        0: "Thin",
        1: "Thick"
    },
    "descriptions": {
        "薄苔": "正常舌苔",
        "厚苔": "食积或湿盛"
    }
}

ROT_GREASY_MAP = {
    "cn": {
        0: "腐苔",
        1: "腻苔"
    },
    "en": {
        0: "Curdy",
        1: "Greasy"
    },
    "descriptions": {
        "腐苔": "胃浊蕴热",
        "腻苔": "痰湿内阻"
    }
}

TONGUE_COLOR_DETAILS = {
    "淡红": {"color": "#FFB6C1", "desc": "正常舌色，气血调和"},
    "红": {"color": "#FF4444", "desc": "热证，体内有热"},
    "绛红": {"color": "#CC0000", "desc": "热盛，阴虚火旺"},
    "青紫": {"color": "#800080", "desc": "血瘀或寒凝"},
    "淡白": {"color": "#F5F5DC", "desc": "虚寒，气血不足"}
}

COATING_COLOR_DETAILS = {
    "白苔": {"color": "#FFFFFF", "desc": "正常或寒证"},
    "黄苔": {"color": "#FFD700", "desc": "热证，脾胃湿热"},
    "灰黑苔": {"color": "#696969", "desc": "重证，寒热错杂"},
    "剥苔": {"color": "#FFE4B5", "desc": "胃阴不足"},
    "无苔": {"color": "#FF6347", "desc": "胃气不足或阴虚"}
}

COATING_THICKNESS_DESCRIPTIONS = {
    "薄苔": "正常舌苔",
    "厚苔": "食积或湿盛",
    "腻苔": "痰湿内阻",
    "腐苔": "胃浊蕴热"
}

TONGUE_SHAPE_DESCRIPTIONS = {
    "正常": "舌体适中，形态正常",
    "胖大": "脾肾阳虚或水湿内停",
    "瘦薄": "气血不足或阴虚火旺",
    "齿痕": "脾虚湿盛",
    "裂纹": "热盛伤阴或血虚",
    "芒刺": "脏腑热极"
}

MOISTURE_LEVEL_DESCRIPTIONS = {
    "正常": "津液正常",
    "少津": "阴虚或燥邪伤津",
    "干燥": "热盛伤津或阴液亏虚",
    "滑润": "水湿内停"
}

TCM_SYNDROMES = {
    "normal": {"name": "平和质", "desc": "阴阳气血调和，身体健康"},
    "qi_deficiency": {"name": "气虚质", "desc": "元气不足，气息低弱"},
    "yang_deficiency": {"name": "阳虚质", "desc": "阳气不足，畏寒怕冷"},
    "yin_deficiency": {"name": "阴虚质", "desc": "阴液亏虚，口干咽燥"},
    "phlegm_dampness": {"name": "痰湿质", "desc": "痰湿凝聚，形体肥胖"},
    "damp_heat": {"name": "湿热质", "desc": "湿热内蕴，面垢油光"},
    "blood_stasis": {"name": "血瘀质", "desc": "血行不畅，肤色晦暗"},
    "qi_stagnation": {"name": "气郁质", "desc": "气机郁滞，情志不畅"}
}

ANALYSIS_STATUS_CODES = {
    0: {"status": "pending", "message": "等待分析"},
    1: {"status": "analyzing", "message": "正在分析"},
    100: {"status": "completed", "message": "分析完成"},
    201: {"status": "no_tongue", "message": "未检测到舌象"},
    202: {"status": "multiple_tongues", "message": "检测到多个舌象区域"},
    203: {"status": "analysis_error", "message": "分析过程出错"},
    204: {"status": "invalid_image", "message": "无效的图像文件"},
    205: {"status": "model_error", "message": "模型加载失败"}
}

FEATURE_MAP = {
    "tongue_color": TONGUE_COLOR_MAP,
    "coating_color": COATING_COLOR_MAP,
    "coating_thickness": COATING_THICKNESS_MAP,
    "rot_greasy": ROT_GREASY_MAP
}


def get_feature_label(feature_type: str, value: int, lang: str = "cn") -> str:
    """
    获取特征标签

    Args:
        feature_type: 特征类型 (tongue_color, coating_color, etc.)
        value: 特征值 (0, 1, 2, etc.)
        lang: 语言 (cn, en)

    Returns:
        特征标签字符串
    """
    if feature_type not in FEATURE_MAP:
        return "未知"

    feature_map = FEATURE_MAP[feature_type]
    lang_map = feature_map.get(lang, feature_map.get("cn", {}))

    return lang_map.get(value, "未知")


def get_feature_description(feature_type: str, label: str) -> str:
    """
    获取特征描述

    Args:
        feature_type: 特征类型
        label: 特征标签

    Returns:
        特征描述字符串
    """
    if feature_type not in FEATURE_MAP:
        return "未知特征"

    descriptions = FEATURE_MAP[feature_type].get("descriptions", {})
    return descriptions.get(label, "未知")


def get_status_info(code: int) -> dict:
    """
    获取状态信息

    Args:
        code: 状态码

    Returns:
        状态信息字典
    """
    return ANALYSIS_STATUS_CODES.get(code, {"status": "unknown", "message": "未知状态"})


def format_features_for_prompt(tongue_color: int, coating_color: int,
                                thickness: int, rot_greasy: int,
                                lang: str = "cn") -> str:
    """
    格式化特征用于 AI 提示词

    Args:
        tongue_color: 舌色编码
        coating_color: 苔色编码
        thickness: 厚度编码
        rot_greasy: 腐腻编码
        lang: 语言

    Returns:
        格式化的特征字符串
    """
    features = [
        f"舌色: {get_feature_label('tongue_color', tongue_color, lang)}",
        f"苔色: {get_feature_label('coating_color', coating_color, lang)}",
        f"厚度: {get_feature_label('coating_thickness', thickness, lang)}",
        f"腐腻: {get_feature_label('rot_greasy', rot_greasy, lang)}"
    ]
    return "，".join(features)


def label_to_code(feature_type: str, label: str) -> int:
    """
    将标签转换为编码

    Args:
        feature_type: 特征类型
        label: 特征标签

    Returns:
        特征编码
    """
    if feature_type not in FEATURE_MAP:
        return -1

    lang_map = FEATURE_MAP[feature_type].get("cn", {})
    for code, lbl in lang_map.items():
        if lbl == label:
            return code

    return -1
