"""E2E-1：核心用户链路冒烟（不触网、不依赖真实 AI Key）。

覆盖：注册/登录 → 创建健康记录 → 自动预警/已读 → 心理打卡 →
PHQ-9 危机分支 → AI 快速分析（mock LLM）→ 聊天流式 safety→delta→done。
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from chat_session import ChatMessage


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        event = ""
        data = {}
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: ") :].strip()
            elif line.startswith("data: "):
                data = json.loads(line[len("data: ") :])
        if event:
            events.append((event, data))
    return events


@pytest.mark.asyncio
@pytest.mark.integration
async def test_core_user_journey(app, db):
    credentials = {"name": "e2e_journey", "password": "e2e-pass-123", "invite_code": "health2026"}

    # 1) 注册 + 登录
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        registered = await anon.post("/api/auth/register", json=credentials)
        assert registered.status_code == 200, registered.text
        logged_in = await anon.post(
            "/api/auth/login",
            data={"username": credentials["name"], "password": credentials["password"]},
        )
        assert logged_in.status_code == 200, logged_in.text
        token = logged_in.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=headers
    ) as client:
        # 2) 创建健康记录（高血压值，触发 K-1 自动预警）
        record = await client.post(
            "/api/health/records",
            json={
                "height": 175,
                "weight": 72,
                "blood_pressure_systolic": 160,
                "blood_pressure_diastolic": 100,
                "heart_rate": 88,
                "sleep_hours": 5,
                "diet_habit": "E2E 冒烟",
            },
        )
        assert record.status_code == 200, record.text
        assert record.json()["id"] > 0

        # 3) 预警列表 + 标记已读
        warnings = await client.get("/api/warning/list")
        assert warnings.status_code == 200, warnings.text
        warning_items = warnings.json()
        assert warning_items, "健康记录提交后应自动生成预警"
        warning_id = warning_items[0]["id"]
        marked = await client.put(f"/api/warning/read/{warning_id}")
        assert marked.status_code == 200, marked.text
        refreshed = await client.get("/api/warning/list")
        read_item = next(item for item in refreshed.json() if item["id"] == warning_id)
        assert read_item["is_read"] is True

        # 4) 心理打卡
        mood = await client.post(
            "/api/mental/mood",
            json={"mood_score": 2, "stress_tags": ["备考"], "sleep_hours": 4, "note": "E2E"},
        )
        assert mood.status_code == 200, mood.text

        # 5) PHQ-9 危机分支（Q9 阳性）；限流由独立测试覆盖，这里不消耗额度
        with patch("routers.mental.check_rate_limit"):
            scale = await client.post(
                "/api/mental/scales/phq9/submit",
                json={"answers": [0, 0, 0, 0, 0, 0, 0, 0, 1]},
            )
        assert scale.status_code == 200, scale.text
        scale_data = scale.json()
        assert scale_data["crisis_flag"] is True
        assert scale_data["resources"], "危机分支必须返回求助资源"

        # 6) AI 快速分析（mock LLM，不触网）
        with (
            patch("routers.ai_analysis.check_rate_limit"),
            patch(
                "routers.ai_analysis.call_llm",
                new=AsyncMock(return_value=("E2E 快速分析结论", 9)),
            ),
        ):
            quick = await client.post("/api/ai/quick-analysis")
        assert quick.status_code == 200, quick.text
        analysis = await client.get(f"/api/ai/analysis/{quick.json()['analysis_id']}")
        assert analysis.status_code == 200, analysis.text
        assert analysis.json()["response_content"] == "E2E 快速分析结论"

        # 7) 聊天流式：safety 首帧 → delta* → done
        session = await client.post(
            "/api/chat/session",
            json={"title": "E2E 会话", "context_type": "health"},
        )
        assert session.status_code == 200, session.text
        session_id = session.json()["id"]

        class _DummySession:
            def close(self):
                pass

        fixture_db = db

        def _fake_add_message(db=None, session_id=0, role="", content="", tokens_used=None):
            # 流式端点用独立的 stream_db 落库；测试里统一落到 transactional 会话。
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
            )
            fixture_db.add(message)
            fixture_db.commit()
            fixture_db.refresh(message)
            return message

        async def _fake_stream(messages, config):
            yield "你"
            yield "好"

        with (
            patch("routers.chat.check_rate_limit"),
            patch("routers.chat.stream_llm", new=_fake_stream),
            patch("routers.chat.SessionLocal", new=lambda: _DummySession()),
            patch("routers.chat.add_message", new=_fake_add_message),
        ):
            streamed = await client.post(
                f"/api/chat/session/{session_id}/stream",
                json={"content": "你好"},
            )

        assert streamed.status_code == 200, streamed.text
        events = _parse_sse(streamed.text)
        assert events[0][0] == "safety", f"首个事件必须是 safety，实际 {events[:1]}"
        assert any(event == "delta" for event, _ in events)
        assert events[-1][0] == "done", f"最后一个事件必须是 done，实际 {events[-1:]}"
        assert "".join(data["content"] for event, data in events if event == "delta") == "你好"
