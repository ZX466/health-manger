"""Regression tests for tongue diagnosis failure cleanup (D1)."""

import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

import models
from services import tongue_service


class _TongueResultCache:
    def get(self, key):
        return None

    def set(self, key, value):
        pass


@pytest.fixture(autouse=True)
def _fresh_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tongue_service, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(tongue_service, "tongue_result_cache", _TongueResultCache())
    return tmp_path


def _make_valid_png() -> bytes:
    """用 PIL 生成一张有效的 1x1 PNG（可通过 S5 魔数校验）。"""
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def _fake_png_file(content=None):
    if content is None:
        content = _make_valid_png()

    async def read():
        return content

    return SimpleNamespace(content_type="image/png", filename="tongue.png", read=read)


@pytest.mark.asyncio
async def test_failed_analysis_removes_orphan_file_and_record(db, _fresh_upload_dir, monkeypatch):
    """分析失败后：磁盘无孤儿图片文件，DB 无 failed 记录残留。"""

    def boom(image_path):
        raise RuntimeError("analyze failed")

    monkeypatch.setattr("tongue.analyze_tongue_image", boom)

    with pytest.raises(HTTPException):
        await tongue_service.upload_and_analyze(_fake_png_file(), user_id=1, db=db)

    assert os.listdir(str(_fresh_upload_dir)) == [], "失败后磁盘应无孤儿图片文件"

    records = db.execute(select(models.TongueDiagnosis)).scalars().all()
    assert records == [], "失败后不应残留 failed 记录"


@pytest.mark.asyncio
async def test_failed_analysis_cleans_file_but_reports_503(db, _fresh_upload_dir, monkeypatch):
    """分析失败应返回 503（RuntimeError），且不污染 DB 与磁盘。"""

    def boom(image_path):
        raise RuntimeError("analyze failed")

    monkeypatch.setattr("tongue.analyze_tongue_image", boom)

    with pytest.raises(HTTPException) as excinfo:
        await tongue_service.upload_and_analyze(_fake_png_file(), user_id=1, db=db)

    assert excinfo.value.status_code == 503
    assert os.listdir(str(_fresh_upload_dir)) == []
    records = db.execute(select(models.TongueDiagnosis)).scalars().all()
    assert records == []
