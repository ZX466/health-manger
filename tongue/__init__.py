"""舌诊模块包 — 整合舌象分析、云端识别、特征映射。"""

from tongue.diagnosis import (
    analyze_tongue_image,
    get_tongue_color_info,
    get_coating_color_info,
    TONGUE_COLORS,
    COATING_COLORS,
    COATING_THICKNESS,
    TONGUE_SHAPES,
    MOISTURE_LEVELS,
)
from tongue.feature_mapping import (
    TCM_SYNDROMES,
)

__all__ = [
    "analyze_tongue_image",
    "get_tongue_color_info",
    "get_coating_color_info",
    "TONGUE_COLORS",
    "COATING_COLORS",
    "COATING_THICKNESS",
    "TONGUE_SHAPES",
    "MOISTURE_LEVELS",
    "TCM_SYNDROMES",
]
