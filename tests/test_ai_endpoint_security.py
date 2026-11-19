"""S-1 P1：AI 出站地址与密钥绑定、上游错误脱敏。"""

import pytest

from async_tasks import _public_task_error
from services import llm_service
from services.llm_service import LLMConfig


def test_custom_url_without_own_key_is_rejected():
    with pytest.raises(ValueError, match="独立 API 密钥"):
        LLMConfig(provider="zhipu", base_url="https://evil.example/v1/chat/completions")


def test_custom_url_with_own_key_is_allowed():
    config = LLMConfig(
        provider="zhipu",
        base_url="https://gateway.example/v1/chat/completions",
        api_key="user-key",
    )
    assert config.api_key == "user-key"
    assert config.base_url.startswith("https://gateway.example")


def test_service_key_is_only_used_for_default_zhipu_endpoint(monkeypatch):
    monkeypatch.setattr(llm_service, "ZHIPU_API_KEY", "service-secret")

    default_config = LLMConfig()
    assert default_config.api_key == "service-secret"

    other_provider = LLMConfig(provider="openai")
    assert other_provider.api_key == ""

    custom_url = LLMConfig(
        provider="zhipu",
        base_url="https://gateway.example/v1/chat/completions",
        api_key="user-key",
    )
    assert custom_url.api_key == "user-key"


def test_plain_http_and_private_custom_hosts_are_rejected():
    with pytest.raises(ValueError, match="HTTPS"):
        LLMConfig(
            provider="zhipu",
            base_url="http://gateway.example/v1/chat/completions",
            api_key="user-key",
        )
    with pytest.raises(ValueError, match="内网"):
        LLMConfig(
            provider="zhipu",
            base_url="https://10.0.0.8/v1/chat/completions",
            api_key="user-key",
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_endpoint_rejects_custom_url_without_key(client):
    response = await client.put(
        "/api/ai/config",
        json={
            "provider": "zhipu",
            "model": "glm-4.5-Air",
            "base_url": "https://evil.example/v1/chat/completions",
        },
    )
    assert response.status_code == 400
    assert "密钥" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_endpoint_accepts_custom_url_with_own_key(client):
    response = await client.put(
        "/api/ai/config",
        json={
            "provider": "zhipu",
            "model": "glm-4.5-Air",
            "base_url": "https://gateway.example/v1/chat/completions",
            "api_key": "sk-user-owned",
        },
    )
    assert response.status_code == 200
    assert response.json()["has_api_key"] is True


@pytest.mark.asyncio
async def test_upstream_response_body_is_not_exposed(monkeypatch):
    class FakeResponse:
        status_code = 500
        text = "INTERNAL-UPSTREAM-SECRET"

    class FakeClient:
        async def post(self, *args, **kwargs):
            return FakeResponse()

    async def fake_get_client():
        return FakeClient()

    monkeypatch.setattr(llm_service, "_get_client", fake_get_client)
    monkeypatch.setattr(llm_service, "MAX_RETRIES", 1)

    config = LLMConfig(
        provider="zhipu",
        base_url="https://gateway.example/v1/chat/completions",
        api_key="user-key",
    )
    with pytest.raises(RuntimeError) as exc_info:
        await llm_service.call_llm([{"role": "user", "content": "ping"}], config)

    assert "INTERNAL-UPSTREAM-SECRET" not in str(exc_info.value)
    assert "HTTP 500" in str(exc_info.value)


def test_async_task_error_is_sanitized():
    message = _public_task_error(RuntimeError("INTERNAL-UPSTREAM-SECRET"))
    assert "INTERNAL-UPSTREAM-SECRET" not in message
    assert "稍后重试" in message
