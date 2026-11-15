"""图片预处理服务（M-PERF2）。

职责：把上游上传的原始图片收敛成「安全、体积小、方向正确、无元数据」的 JPEG，
再交给视觉模型或落盘。所有校验都在这里做一次，调用方不必重复。

设计要点：
- 拒绝 >10MiB、非 jpg/png/webp、像素数超限（解压炸弹）的输入；
- `ImageOps.exif_transpose` 纠正手机拍摄方向，输出不携带 EXIF/GPS；
- 长边压到 `max_edge`，Lanczos 重采样，JPEG `optimize=True`；
- 纯函数式：不写文件、不碰数据库，便于单测与复用（舌诊 / 识餐 / OCR）。
"""

import io
import logging

from PIL import Image, ImageOps

import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_EDGE = 1024
DEFAULT_QUALITY = 85
ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
# 解压炸弹防护：正常手机照片远小于此值，超过即视为可疑输入
MAX_PIXELS = 40_000_000

# 让 PIL 自己的炸弹检查也生效（PIL 默认约 1.79 亿像素，过于宽松）
if Image.MAX_IMAGE_PIXELS is None or Image.MAX_IMAGE_PIXELS > MAX_PIXELS:
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class ImageValidationError(ValueError):
    """输入图片不合法（调用方应转 400）。"""


def prepare_image(
    raw: bytes,
    *,
    max_edge: int = DEFAULT_MAX_EDGE,
    quality: int = DEFAULT_QUALITY,
) -> bytes:
    """校验并压缩图片，返回 JPEG 字节。失败抛 `ImageValidationError`。"""
    if not raw:
        raise ImageValidationError("图片内容为空")
    if len(raw) > settings.MAX_UPLOAD_FILE_SIZE:
        limit_mb = settings.MAX_UPLOAD_FILE_SIZE // (1024 * 1024)
        raise ImageValidationError(f"图片大小不能超过 {limit_mb}MB")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            image_format = probe.format
            width, height = probe.size
            has_alpha = probe.mode in ("RGBA", "LA", "P")
            # 必须先读完再离开上下文，后续操作在副本上进行
            work = probe.copy()
    except ImageValidationError:
        raise
    except Exception as exc:  # PIL 抛的异常类型很多，统一收敛
        raise ImageValidationError("文件不是有效的图片") from exc

    if image_format not in ALLOWED_FORMATS:
        raise ImageValidationError("仅支持 JPG / PNG / WEBP 图片")
    if width * height > MAX_PIXELS:
        raise ImageValidationError("图片尺寸过大")

    # 方向纠正：手机竖拍照片的 EXIF Orientation 必须在缩放前应用
    work = ImageOps.exif_transpose(work)

    if has_alpha:
        # 透明背景铺白，避免转 JPEG 后变黑
        rgba = work.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        work = background
    elif work.mode != "RGB":
        work = work.convert("RGB")

    if max(work.size) > max_edge:
        work.thumbnail((max_edge, max_edge), Image.LANCZOS)

    buffer = io.BytesIO()
    # 不传 exif 参数 => 输出不含 EXIF / GPS / 缩略图
    work.save(buffer, format="JPEG", quality=quality, optimize=True)
    result = buffer.getvalue()

    logger.debug(
        "prepare_image: %d -> %d bytes, %dx%d -> %dx%d",
        len(raw),
        len(result),
        width,
        height,
        work.size[0],
        work.size[1],
    )
    return result
