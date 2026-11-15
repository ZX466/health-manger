"""PHQ-9 / GAD-7 量表定义与评分。

纯函数模块：不依赖数据库与第三方库，供 API 路由、预警与测试复用。
量表题目与 0-3 计分口径固定；风险分级仅用于初筛提示，不构成诊断。
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["minimal", "mild", "moderate", "moderately_severe", "severe"]

_OPTIONS: tuple[tuple[int, str], ...] = (
    (0, "完全不会"),
    (1, "好几天"),
    (2, "一半以上的天数"),
    (3, "几乎每天"),
)

_RISK_LABELS: dict[RiskLevel, str] = {
    "minimal": "无明显症状",
    "mild": "轻度",
    "moderate": "中度",
    "moderately_severe": "中重度",
    "severe": "重度",
}


@dataclass(frozen=True)
class ScaleDef:
    """一个标准化心理量表的定义。"""

    key: str
    name: str
    questions: tuple[str, ...]
    options: tuple[tuple[int, str], ...] = _OPTIONS

    @property
    def max_score(self) -> int:
        return len(self.questions) * 3

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "questions": list(self.questions),
            "options": [{"score": score, "label": label} for score, label in self.options],
            "max_score": self.max_score,
        }


@dataclass(frozen=True)
class ScoreResult:
    """评分结果；crisis_flag 表示需要立即展示危机干预资源。"""

    scale_type: str
    score: int
    max_score: int
    risk_level: RiskLevel
    label: str
    crisis_flag: bool

    def to_dict(self) -> dict:
        return {
            "scale_type": self.scale_type,
            "score": self.score,
            "max_score": self.max_score,
            "risk_level": self.risk_level,
            "label": self.label,
            "crisis_flag": self.crisis_flag,
        }


PHQ9 = ScaleDef(
    key="phq9",
    name="PHQ-9 抑郁初筛",
    questions=(
        "做事时提不起劲或没有兴趣",
        "感到心情低落、沮丧或绝望",
        "入睡困难、睡不安稳或睡眠过多",
        "感觉疲倦或没有活力",
        "食欲不振或吃太多",
        "觉得自己很糟，或觉得自己很失败，或让自己或家人失望",
        "对事物专注有困难，例如阅读报纸或看电视时",
        "动作或说话速度缓慢到别人已经察觉，或正好相反——烦躁或坐立不安、动来动去的情况比平时更多",
        "有不如死掉或用某种方式伤害自己的念头",
    ),
)

GAD7 = ScaleDef(
    key="gad7",
    name="GAD-7 焦虑初筛",
    questions=(
        "感到紧张、焦虑或急切",
        "不能停止或控制担忧",
        "对各种各样的事情担忧过多",
        "很难放松下来",
        "由于不安而无法静坐",
        "变得容易烦恼或急躁",
        "感到似乎将有可怕的事情发生而害怕",
    ),
)

SCALES: dict[str, ScaleDef] = {PHQ9.key: PHQ9, GAD7.key: GAD7}


def get_scale(scale_type: str) -> ScaleDef:
    """按类型取量表定义，未知类型抛 ValueError。"""
    try:
        return SCALES[scale_type]
    except KeyError as exc:
        raise ValueError(f"未知量表类型: {scale_type}") from exc


def _normalize_answers(scale_def: ScaleDef, answers: Sequence[int]) -> list[int]:
    if len(answers) != len(scale_def.questions):
        raise ValueError(f"{scale_def.key} 需要 {len(scale_def.questions)} 个作答")
    normalized: list[int] = []
    for answer in answers:
        if isinstance(answer, bool) or not isinstance(answer, int) or not 0 <= answer <= 3:
            raise ValueError("每项作答必须是 0-3 的整数")
        normalized.append(answer)
    return normalized


def _phq9_risk(total: int) -> RiskLevel:
    if total <= 4:
        return "minimal"
    if total <= 9:
        return "mild"
    if total <= 14:
        return "moderate"
    if total <= 19:
        return "moderately_severe"
    return "severe"


def _gad7_risk(total: int) -> RiskLevel:
    if total <= 4:
        return "minimal"
    if total <= 9:
        return "mild"
    if total <= 14:
        return "moderate"
    return "severe"


def score(scale_type: str, answers: Sequence[int]) -> ScoreResult:
    """计算量表总分与风险等级。

    PHQ-9 第 9 题（自伤/自杀念头）任何非零作答都置 crisis_flag；
    GAD-7 达到重度（>=15）同样需要立即展示支持资源。
    """
    scale_def = get_scale(scale_type)
    normalized = _normalize_answers(scale_def, answers)
    total = sum(normalized)

    if scale_type == PHQ9.key:
        risk_level = _phq9_risk(total)
        crisis_flag = normalized[8] > 0 or total >= 20
    else:
        risk_level = _gad7_risk(total)
        crisis_flag = total >= 15

    return ScoreResult(
        scale_type=scale_type,
        score=total,
        max_score=scale_def.max_score,
        risk_level=risk_level,
        label=_RISK_LABELS[risk_level],
        crisis_flag=crisis_flag,
    )
