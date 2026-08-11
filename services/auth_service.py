import os


INVITE_CODES_DEFAULT = ["health2026"]


def get_invite_codes() -> list:
    env_codes = os.getenv("INVITE_CODES", "")
    if env_codes.strip():
        return [code.strip() for code in env_codes.split(",") if code.strip()]
    return INVITE_CODES_DEFAULT


def validate_invite_code(code: str) -> bool:
    return code in get_invite_codes()
