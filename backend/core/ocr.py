"""
OCR 模块 — 截图文字提取
使用 Tesseract OCR，支持中英文混合识别
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

# Tesseract 路径
# 优先系统安装，其次项目内置
_SYSTEM_TESSERACT = None
for p in ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]:
    if os.path.exists(p):
        _SYSTEM_TESSERACT = p
        break

_TESSERACT_DIR = Path(__file__).parent.parent.parent / "tesseract"
_TESSERACT_BIN = _TESSERACT_DIR / "usr/bin/tesseract"
_TESSDATA_DIR = _TESSERACT_DIR / "usr/share/tesseract-ocr/5/tessdata"

def _get_tesseract_cmd() -> Optional[str]:
    """获取可用的 tesseract 命令路径"""
    if _SYSTEM_TESSERACT:
        return _SYSTEM_TESSERACT
    if _TESSERACT_BIN.exists():
        return str(_TESSERACT_BIN)
    return None


def _get_tessdata_dir() -> Optional[str]:
    """获取 tessdata 目录"""
    # 系统路径优先
    for p in ["/usr/share/tesseract-ocr/5/tessdata",
              "/usr/share/tesseract-ocr/4.00/tessdata",
              "/usr/share/tessdata"]:
        if os.path.exists(p):
            return p
    if _TESSDATA_DIR.exists():
        return str(_TESSDATA_DIR)
    return None


# pytesseract 可选
try:
    import pytesseract
    _HAS_PYTESSERACT = True
except ImportError:
    _HAS_PYTESSERACT = False

# PIL 用于图片预处理
try:
    from PIL import Image, ImageEnhance, ImageFilter
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def ocr_image(image_path: str, lang: str = "chi_sim+eng") -> str:
    """
    对图片进行 OCR 识别

    Args:
        image_path: 图片文件路径（支持 jpg/png/bmp/tiff）
        lang: 识别语言，默认中英文混合

    Returns:
        识别出的文字
    """
    tesseract_cmd = _get_tesseract_cmd()
    if not tesseract_cmd:
        raise RuntimeError("Tesseract 未安装。请运行: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")

    tessdata = _get_tessdata_dir()

    # 优先用 pytesseract
    if _HAS_PYTESSERACT and _HAS_PIL:
        return _ocr_with_pytesseract(image_path, lang, tesseract_cmd, tessdata)

    # 回退：直接调 tesseract 命令行
    return _ocr_with_cli(image_path, lang, tesseract_cmd, tessdata)


def _preprocess_image(image_path: str) -> str:
    """
    图片预处理：增强对比度、锐化，提升 OCR 准确率
    返回预处理后的临时文件路径
    """
    if not _HAS_PIL:
        return image_path

    img = Image.open(image_path)

    # 转灰度
    if img.mode != 'L':
        img = img.convert('L')

    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # 锐化
    img = img.filter(ImageFilter.SHARPEN)

    # 放大（如果太小）
    w, h = img.size
    if w < 800:
        scale = 800 / w
        img = img.resize((800, int(h * scale)), Image.LANCZOS)

    # 保存到临时文件
    tmp_path = image_path + ".ocr.png"
    img.save(tmp_path)
    return tmp_path


def _ocr_with_pytesseract(image_path: str, lang: str,
                           tesseract_cmd: str, tessdata: Optional[str]) -> str:
    """使用 pytesseract 进行 OCR"""
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    # 预处理
    processed = _preprocess_image(image_path)

    custom_config = r'--oem 3 --psm 6'
    if tessdata:
        custom_config += f' --tessdata-dir "{tessdata}"'

    try:
        text = pytesseract.image_to_string(
            processed, lang=lang, config=custom_config
        )
    finally:
        # 清理临时文件
        if processed != image_path and os.path.exists(processed):
            os.unlink(processed)

    return text.strip()


def _ocr_with_cli(image_path: str, lang: str,
                   tesseract_cmd: str, tessdata: Optional[str]) -> str:
    """使用 tesseract 命令行进行 OCR"""
    import tempfile

    # 预处理
    processed = _preprocess_image(image_path)

    # 输出到临时文件
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        output_base = f.name

    # 去掉 .txt 后缀（tesseract 自动加）
    output_base = output_base[:-4]

    env = os.environ.copy()
    # 如果使用项目内置 tesseract，设置库路径
    if str(_TESSERACT_DIR) in tesseract_cmd:
        lib_path = str(_TESSERACT_DIR / "usr/lib/x86_64-linux-gnu")
        env['LD_LIBRARY_PATH'] = lib_path + ":" + env.get('LD_LIBRARY_PATH', '')

    cmd = [tesseract_cmd, processed, output_base, '-l', lang]
    if tessdata:
        cmd.extend(['--tessdata-dir', tessdata])

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        output_file = output_base + '.txt'
        if os.path.exists(output_file):
            text = Path(output_file).read_text(encoding='utf-8', errors='ignore')
            os.unlink(output_file)
            return text.strip()
        else:
            # tesseract stderr 有日志信息，不算错误
            return ""
    finally:
        if processed != image_path and os.path.exists(processed):
            os.unlink(processed)

    return ""
