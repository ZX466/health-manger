"""
手动测试：AI 模块路由（原 tests/test_ai_module.py 的 TestAIModuleRouter）

说明：ai_module 路由已从生产代码移除（routers/ai_analysis.py 不再包含
/pipeline、/metrics 端点），本文件仅作为历史回归参考保留。
默认不参与自动收集（tests/manual/conftest.py 的 collect_ignore_glob = ["*"]）。

夹具约定（tests/conftest.py）：
- client     = 已认证客户端（token 在 conftest 中配置）
- anon_client = 未认证客户端
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestAIModuleRouter:
    @pytest.mark.asyncio
    async def test_run_pipeline_endpoint(self, client, db):
        # 创建健康记录
        record_data = {
            "height": 175.0,
            "weight": 70.0,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 75,
            "temperature": 36.5,
        }
        await client.post("/api/health/records", json=record_data)

        with patch("services.ai_module_service.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = ("分析结果", 100)
            response = await client.post(
                "/api/ai-module/pipeline",
                json={
                    "input_type": "health_data",
                    "data": {"request": "请分析我的健康状况"},
                    "pipeline_type": "health_analysis",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_metrics_endpoint(self, client):
        response = await client.get("/api/ai-module/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data

    @pytest.mark.asyncio
    async def test_run_pipeline_invalid_type(self, client):
        response = await client.post(
            "/api/ai-module/pipeline",
            json={
                "input_type": "unknown",
                "data": {},
                "pipeline_type": "invalid_type",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_run_pipeline_unauthorized(self, anon_client):
        response = await anon_client.post(
            "/api/ai-module/pipeline",
            json={"input_type": "health_data", "data": {}, "pipeline_type": "health_analysis"},
        )
        assert response.status_code == 401
