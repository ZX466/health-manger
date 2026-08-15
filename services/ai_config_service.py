"""AI 配置服务：API Key 加密存储 + 用户配置 CRUD。

安全：API Key 用 Fernet（密钥由 SECRET_KEY 派生）加密后落库，
前端仅能看到掩码版本；解密仅在服务端发起 LLM 请求时进行。
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from auth import SECRET_KEY

# 默认供应商配置（与 settings 一致，作为未配置时的回退）
DEFAULT_PROVIDER = "zhipu"
DEFAULT_MODEL = "glm-4.5-Air"
PROVIDERS = {
    "zhipu": {"label": "智谱 GLM", "default_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions"},
    "openai": {"label": "OpenAI 兼容", "default_url": "https://api.openai.com/v1/chat/completions"},
    "ark": {"label": "火山引擎 Ark", "default_url": "https://ark.cn-beijing.volces.com/api/v3/responses"},
}


def _fernet() -> Fernet:
    key = hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_api_key(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")


def mask_api_key(plain_or_encrypted: str) -> str:
    """返回掩码版本（不泄露明文）。传入明文或密文均只显前 4 后 2。"""
    if not plain_or_encrypted:
        return ""
    if len(plain_or_encrypted) <= 8:
        return "*" * len(plain_or_encrypted)
    return plain_or_encrypted[:4] + "*" * 8 + plain_or_encrypted[-2:]


def get_config(db: Session, user_id: int) -> Optional[models.AIConfig]:
    return db.execute(
        select(models.AIConfig).where(models.AIConfig.user_id == user_id)
    ).scalars().first()


def save_config(
    db: Session,
    user_id: int,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
    vision_base_url: Optional[str] = None,
    vision_api_key: Optional[str] = None,
) -> models.AIConfig:
    """保存/更新用户 AI 配置（聊天 + 舌诊视觉两套）。

    api_key / vision_api_key 为空则保留原值（编辑时不重复提交明文）。
    """
    config = get_config(db, user_id)
    if config is None:
        config = models.AIConfig(user_id=user_id)
        db.add(config)

    # 聊天/分析模型
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if base_url:
        config.base_url = base_url
    if api_key:
        config.api_key_encrypted = encrypt_api_key(api_key)

    # 舌诊视觉模型
    if vision_provider:
        config.vision_provider = vision_provider
    if vision_model:
        config.vision_model = vision_model
    if vision_base_url:
        config.vision_base_url = vision_base_url
    if vision_api_key:
        config.vision_api_key_encrypted = encrypt_api_key(vision_api_key)

    db.commit()
    db.refresh(config)
    return config


def build_vision_config_for_user(db: Session, user_id: int) -> Optional[dict]:
    """构造用户舌诊视觉模型配置 dict。

    返回 {provider, base_url, model, api_key}；未配置视觉模型返回 None（由舌诊回退默认 ARK）。
    """
    cfg = get_config(db, user_id)
    if not cfg or not cfg.vision_model:
        return None
    return {
        "provider": cfg.vision_provider or "ark",
        "base_url": cfg.vision_base_url,
        "model": cfg.vision_model,
        "api_key": decrypt_api_key(cfg.vision_api_key_encrypted) if cfg.vision_api_key_encrypted else None,
    }


def delete_config(db: Session, user_id: int) -> bool:
    config = get_config(db, user_id)
    if not config:
        return False
    db.delete(config)
    db.commit()
    return True


def build_llm_config_for_user(db: Session, user_id: int, base_config=None):
    """构造用户定制 LLMConfig：有用户 AI 配置则覆盖，否则回退默认。

    供 AI 分析/聊天端点使用，避免各端点重复读取与解密逻辑。
    """
    from services.llm_service import LLMConfig

    cfg = get_config(db, user_id)
    if not cfg:
        return base_config or LLMConfig()

    kwargs = {
        "provider": cfg.provider,
        "model": cfg.model,
        "base_url": cfg.base_url,
    }
    if cfg.api_key_encrypted:
        kwargs["api_key"] = decrypt_api_key(cfg.api_key_encrypted)

    if base_config is not None:
        kwargs["temperature"] = base_config.temperature
        kwargs["max_tokens"] = base_config.max_tokens
        kwargs["timeout"] = base_config.timeout

    return LLMConfig(**kwargs)
