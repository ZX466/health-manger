"""模型输出文本清洗（M-PERF3）。

只做**显示安全**清洗，不做提示注入过滤（那部分见 `services/security_service.py`
的 `sanitize_for_prompt`）：模型返回的字符串可能带 ANSI 转义（ESC/CSI）、
双向覆盖符（Trojan Source）或零宽字符，直接回给前端会污染终端/日志，
也会破坏 `LIKE` 匹配。这里统一抹掉，再折叠空白、截断长度。

不引入新依赖，纯 stdlib re。
"""

import re

MAX_NAME_LENGTH = 50

# ANSI 转义序列（必须整段抹掉，否则剩下的参数会变可见乱码，如 ESC[31m 会剩 "[31m"）
# OSC：ESC ] ... BEL/ST；CSI：ESC [ 参数 中间 终止符；其它两字节转义：ESC + 单字符
_ANSI_OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
_ANSI_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_ANSI_ESC_RE = re.compile(r"\x1b[@-Z\\-_]")
# C0/C1 控制符 + 零宽/双向控制符 + 行/段分隔符 + 软连字符
_UNSAFE_CHARS_RE = re.compile(
    r"[\x00-\x1f\x7f-\x9f\u00ad\u200b-\u200f\u2028-\u202e\u2060-\u206f\ufeff]"
)
_WHITESPACE_RE = re.compile(r"\s+")


def clean_output_text(value, *, max_length: int) -> str:
    """把模型给的字符串收敛成可安全展示的文本；非字符串返回空串。

    - 抹掉 ANSI 转义序列（ESC/CSI/OSC，含 ``ESC[31m`` 这类颜色与 ``ESC[2J`` 清屏）
    - 抹掉零宽字符与双向控制符（含 U+202E Trojan Source）
    - 连续空白折叠成单空格并去首尾空白
    - 超过 `max_length` 截断
    """
    if not isinstance(value, str):
        return ""

    cleaned = _ANSI_OSC_RE.sub("", value)
    cleaned = _ANSI_CSI_RE.sub("", cleaned)
    cleaned = _ANSI_ESC_RE.sub("", cleaned)
    cleaned = _UNSAFE_CHARS_RE.sub("", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned[:max_length].strip()


def clean_output_list(value, *, max_items: int, max_length: int) -> list[str]:
    """清洗字符串列表：丢弃非字符串与清洗后为空的项，最多 `max_items` 项。"""
    if not isinstance(value, list):
        return []

    result = []
    for item in value[:max_items]:
        text = clean_output_text(item, max_length=max_length)
        if text:
            result.append(text)
    return result
