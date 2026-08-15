"""
云端舌象分析模块
默认使用火山引擎 ARK 豆包视觉模型；支持 OpenAI 兼容视觉接口（自定义 Base URL/模型/Key）。
统一走 OpenAI 兼容 chat/completions 格式（image_url data URI），兼容智谱 GLM-4V / OpenAI / ARK 等。
"""
import os
import json
import base64
import re
import logging
from typing import Dict, Optional
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class CloudTongueAnalyzer:
    """云端舌象分析器（OpenAI 兼容视觉接口）。

    支持通过 api_key / model_id / base_url 注入用户自定义配置；
    未指定时回退默认火山引擎 ARK 豆包视觉模型。
    """

    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    SYSTEM_PROMPT = """你是一位专业的中医舌诊专家，具有20年临床经验。请根据用户上传的舌象图片，进行专业的舌象分析。

你需要分析以下内容并严格按JSON格式返回：
1. tongue_color（舌色）：淡红/淡白/红/绛红/青紫
2. coating_color（苔色）：白苔/黄苔/灰黑苔/剥苔/无苔
3. coating_thickness（苔质）：薄苔/厚苔/腻苔/腐苔
4. tongue_shape（舌形）：正常/胖大/瘦薄/齿痕/裂纹
5. moisture_level（润燥）：正常/少津/干燥/滑润
6. has_cracks（是否有裂纹）：true/false
7. has_teeth_marks（是否有齿痕）：true/false
8. tongue_spirit（舌神）：荣润/少润/枯槁
9. confidence（置信度）：0.0-1.0之间的数值

只返回JSON，不要其他文字。示例：
{"tongue_color":"淡红","coating_color":"白苔","coating_thickness":"薄苔","tongue_shape":"正常","moisture_level":"正常","has_cracks":false,"has_teeth_marks":false,"tongue_spirit":"荣润","confidence":0.85}"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ARK_API_KEY", "")
        self.model_id = model_id or os.getenv("ARK_MODEL_ID", "doubao-seed-1-6-vision-250815")
        self.base_url = base_url or os.getenv("ARK_API_URL", self.BASE_URL)
        self._session: Optional[requests.Session] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.model_id)

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
        return self._session

    @staticmethod
    def encode_image_base64(image_path: str) -> str:
        image_path = Path(image_path)
        ext = image_path.suffix.lower()
        mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp", ".gif": "gif"}
        mime_type = mime_map.get(ext, "jpeg")
        with open(image_path, "rb") as f:
            return f"data:image/{mime_type};base64,{base64.b64encode(f.read()).decode('utf-8')}"

    def analyze(self, image_path: str) -> Dict:
        if not self.is_configured:
            raise RuntimeError("未配置视觉模型 API Key / 模型，请在 AI 设置或 .env 中配置")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在：{image_path}")

        session = self._get_session()
        base64_image = self.encode_image_base64(image_path)

        # OpenAI 兼容视觉格式（智谱 GLM-4V / OpenAI / ARK /chat/completions 均支持）
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": base64_image}},
                        {"type": "text", "text": self.SYSTEM_PROMPT + "\n\n请分析这张舌象图片，返回JSON格式的诊断结果"},
                    ],
                }
            ],
            "max_tokens": 1000,
        }

        response = session.post(self.base_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        content = self._extract_content(data)
        return self._parse_response(content)

    @staticmethod
    def _extract_content(data: dict) -> str:
        if "output" in data and isinstance(data["output"], list):
            for item in data["output"]:
                if isinstance(item, dict) and item.get("type") == "message":
                    for content_item in item.get("content", []):
                        if isinstance(content_item, dict) and content_item.get("type") == "output_text":
                            return content_item["text"].strip()
            for item in data["output"]:
                if isinstance(item, dict) and "content" in item:
                    for content_item in item.get("content", []):
                        if isinstance(content_item, dict) and "text" in content_item:
                            return content_item["text"].strip()

        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            if "message" in choice:
                return choice["message"]["content"].strip()

        if "output_text" in data:
            return data["output_text"].strip()

        raise ValueError(f"无法从响应中提取内容：{json.dumps(data, ensure_ascii=False)[:500]}")

    @staticmethod
    def _parse_response(content: str) -> Dict:
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if not json_match:
            raise ValueError(f"无法解析模型返回结果：{content}")

        result = json.loads(json_match.group())

        defaults = {
            "tongue_color": "淡红",
            "coating_color": "白苔",
            "coating_thickness": "薄苔",
            "tongue_shape": "正常",
            "moisture_level": "正常",
            "has_cracks": False,
            "has_teeth_marks": False,
            "tongue_spirit": "荣润",
            "confidence": 0.75,
        }
        for key, default in defaults.items():
            result.setdefault(key, default)
        result["confidence"] = min(max(float(result["confidence"]), 0.0), 1.0)
        result["is_ai_analysis"] = True
        result["is_cloud_analysis"] = True
        return result

    def analyze_with_fallback(self, image_path: str, fallback_fn=None) -> Dict:
        try:
            result = self.analyze(image_path)
            logger.info(f"云端分析成功：置信度={result['confidence']}")
            return result
        except Exception as e:
            logger.warning(f"云端分析失败：{e}")
            if fallback_fn:
                logger.info("回退到备用分析模式...")
                return fallback_fn(image_path)
            raise


cloud_analyzer = CloudTongueAnalyzer()
