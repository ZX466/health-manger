"""舌诊模块包 — 整合舌象分析、云端识别、特征映射。"""

from tongue.diagnosis import (
    COATING_COLORS,
    COATING_THICKNESS,
    MOISTURE_LEVELS,
    TONGUE_COLORS,
    TONGUE_SHAPES,
    analyze_tongue_image,
    get_coating_color_info,
    get_tongue_color_info,
)
from tongue.feature_mapping import (
    TCM_SYNDROMES,
)

__all__ = [
    "COATING_COLORS",
    "COATING_THICKNESS",
    "MOISTURE_LEVELS",
    "TCM_SYNDROMES",
    "TONGUE_COLORS",
    "TONGUE_SHAPES",
    "analyze_tongue_image",
    "get_coating_color_info",
    "get_tongue_color_info",
]
