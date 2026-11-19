"""视觉模型失败提示：把上游状态翻译成可操作信息（不回显原文）。"""

import pytest

from services import vision_service
from services.vision_service import VisionServiceError, analyze_image_json_sync


class _FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None):
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]


def _run(monkeypatch, responses):
    monkeypatch.setattr(vision_service.httpx, "Client", lambda timeout: _FakeClient(responses))
    config = {"provider": "zhipu", "base_url": "https://example.test/v1/chat/completions",
              "model": "some-model", "api_key": "test-key"}
    with pytest.raises(VisionServiceError) as excinfo:
        analyze_image_json_sync(b"fake-image-bytes", "prompt", config=config)
    return str(excinfo.value)


def test_non_vision_model_gets_actionable_message(monkeypatch):
    body = '{"error":{"code":"1210","message":"messages.content.type 参数非法，取值范围 [\'text\']"}}'
    message = _run(monkeypatch, [_FakeResponse(400, body), _FakeResponse(400, body)])
    assert "不支持图片输入" in message
    assert "glm-4v-plus" in message


def test_auth_failure_mentions_api_key(monkeypatch):
    message = _run(monkeypatch, [_FakeResponse(401, '{"error":{"message":"invalid api key"}}')])
    assert "鉴权失败" in message
    assert "401" in message


def test_generic_bad_request_keeps_status(monkeypatch):
    body = '{"error":{"message":"bad request"}}'
    message = _run(monkeypatch, [_FakeResponse(400, body), _FakeResponse(400, body)])
    assert "HTTP 400" in message
    assert "bad request" not in message  # 不回显上游原文
