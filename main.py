import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from database import engine, Base
from routers import auth, health, food, sport, ai_analysis, warning, tongue, chat
from async_tasks import start_task_queue, stop_task_queue
from services.llm_service import close_http_client

logger = logging.getLogger(__name__)

load_dotenv()

# Database tables are managed by Alembic migrations.
# Run "alembic upgrade head" to apply all migrations.
# For development convenience, create_all is kept as a fallback:
if os.getenv("ENV", "development") == "development":
    Base.metadata.create_all(bind=engine)
    logger.debug("Development mode: create_all executed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_task_queue()
    logger.info("应用启动完成")
    yield
    stop_task_queue()
    await close_http_client()
    logger.info("应用关闭完成")


app = FastAPI(
    title="大学生健康系统",
    description="用于管理大学生身体健康数据的 Web 应用程序",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """S7: 添加安全响应头（CSP/X-Frame-Options/X-Content-Type-Options）。"""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; font-src 'self' data:",
    )
    return response

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(food.router)
app.include_router(sport.router)
app.include_router(ai_analysis.router)
app.include_router(warning.router)
app.include_router(tongue.router)
app.include_router(chat.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.error("未处理异常: %s %s -> %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "请求的资源不存在"},
    )


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    static_root = os.path.abspath(static_dir)
    static_file_path = os.path.abspath(os.path.join(static_root, full_path)) if os.path.exists(static_root) else None
    if (static_file_path and os.path.commonpath([static_root, static_file_path]) == static_root
            and os.path.isfile(static_file_path)):
        return FileResponse(static_file_path)
    index_path = os.path.join(static_root, "index.html") if os.path.exists(static_root) else None
    if index_path:
        return FileResponse(index_path)
    return {"message": "API is running, but frontend is not available"}
