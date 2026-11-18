"""上传图片的边界校验（识别类草稿接口共用）。"""

from fastapi import HTTPException, UploadFile

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


async def read_image_upload(file: UploadFile) -> bytes:
    """读取并校验图片上传：类型、扩展名、大小、真实图像魔数。"""
    import io
    import os

    from PIL import Image

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="请上传 jpg/png/webp 图片")

    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件格式，允许: .jpg/.jpeg/.png/.webp")

    content = await file.read(MAX_IMAGE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="文件不是有效的图片")

    return content
