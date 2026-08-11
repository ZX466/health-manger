"""
集中配置模块
所有可调参数从环境变量读取，带合理默认值
"""

import os

# ── Auth / JWT ──
JWT_ALGORITHM = "HS256"
MIN_SECRET_KEY_LENGTH = 32
MAX_PASSWORD_LENGTH = 72
BCRYPT_ROUNDS = 12
DEFAULT_TOKEN_EXPIRE_MINUTES = 15
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ── LLM (智谱 AI) ──
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_API_URL = os.getenv("ZHIPU_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4.5-Air")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60.0"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.0"))
LLM_QUESTION_MAX_LENGTH = int(os.getenv("LLM_QUESTION_MAX_LENGTH", "500"))
LLM_FIELD_MAX_LENGTH = int(os.getenv("LLM_FIELD_MAX_LENGTH", "100"))

# Per-endpoint LLM config
AI_ANALYSIS_TEMPERATURE = float(os.getenv("AI_ANALYSIS_TEMPERATURE", "1.0"))
AI_ANALYSIS_MAX_TOKENS = int(os.getenv("AI_ANALYSIS_MAX_TOKENS", "1000"))
AI_QUICK_TEMPERATURE = float(os.getenv("AI_QUICK_TEMPERATURE", "0.7"))
AI_QUICK_MAX_TOKENS = int(os.getenv("AI_QUICK_MAX_TOKENS", "1500"))
AI_EVAL_TEMPERATURE = float(os.getenv("AI_EVAL_TEMPERATURE", "0.8"))
AI_EVAL_MAX_TOKENS = int(os.getenv("AI_EVAL_MAX_TOKENS", "2000"))
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.7"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1500"))

# ── Rate Limiting ──
AI_ANALYSIS_RATE_LIMIT = int(os.getenv("AI_ANALYSIS_RATE_LIMIT", "10"))
AI_QUICK_RATE_LIMIT = int(os.getenv("AI_QUICK_RATE_LIMIT", "5"))
AI_EVAL_RATE_LIMIT = int(os.getenv("AI_EVAL_RATE_LIMIT", "5"))
CHAT_RATE_LIMIT = int(os.getenv("CHAT_RATE_LIMIT", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# ── Chat Context ──
CHAT_CONTEXT_MAX_MESSAGES = int(os.getenv("CHAT_CONTEXT_MAX_MESSAGES", "10"))
CHAT_CONTEXT_MAX_TOKENS = int(os.getenv("CHAT_CONTEXT_MAX_TOKENS", "3000"))
CHARS_PER_TOKEN_ZH = int(os.getenv("CHARS_PER_TOKEN_ZH", "2"))
CHAT_SESSION_LIST_LIMIT = int(os.getenv("CHAT_SESSION_LIST_LIMIT", "20"))
CHAT_MESSAGE_LIST_LIMIT = int(os.getenv("CHAT_MESSAGE_LIST_LIMIT", "50"))

# ── Cache ──
LLM_CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "1800"))
LLM_CACHE_MAX_SIZE = int(os.getenv("LLM_CACHE_MAX_SIZE", "100"))
TONGUE_CACHE_TTL = int(os.getenv("TONGUE_CACHE_TTL", "3600"))
TONGUE_CACHE_MAX_SIZE = int(os.getenv("TONGUE_CACHE_MAX_SIZE", "50"))

# ── Upload ──
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join("uploads", "tongue"))
MAX_UPLOAD_FILE_SIZE = int(os.getenv("MAX_UPLOAD_FILE_SIZE", str(10 * 1024 * 1024)))
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ── Async Task Queue ──
TASK_QUEUE_MAX_WORKERS = int(os.getenv("TASK_QUEUE_MAX_WORKERS", "2"))
TASK_RESULT_TTL = int(os.getenv("TASK_RESULT_TTL", "3600"))

# ── ARK (火山引擎) ──
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_MODEL_ID = os.getenv("ARK_MODEL_ID", "doubao-seed-1-6-vision-250815")
ARK_API_URL = os.getenv("ARK_API_URL", "https://ark.cn-beijing.volces.com/api/v3/responses")
ARK_REQUEST_TIMEOUT = int(os.getenv("ARK_REQUEST_TIMEOUT", "60"))

# ── Stats ──
DEFAULT_STATS_WINDOW_DAYS = int(os.getenv("DEFAULT_STATS_WINDOW_DAYS", "7"))

# ── Sanitize ──
SANITIZE_MAX_INPUT_LENGTH = int(os.getenv("SANITIZE_MAX_INPUT_LENGTH", "2000"))
