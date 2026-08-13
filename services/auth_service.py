import os


def get_invite_codes() -> list:
    """从环境变量读取邀请码列表。

    S6: 移除硬编码默认值——未配置 INVITE_CODES 时返回空列表（注册被禁止），
    避免"health2026"这类可预测默认码被源码泄露后注册门槛形同虚设。
    """
    env_codes = os.getenv("INVITE_CODES", "")
    if env_codes.strip():
        return [code.strip() for code in env_codes.split(",") if code.strip()]
    return []


def validate_invite_code(code: str) -> bool:
    return code in get_invite_codes()
