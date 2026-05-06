"""
简历助手 Backend API

FastAPI 服务 — 同时支持：
 - CLI 直接调用 (python main.py)
 - 移动端 HTTP API 调用

Author: calumhuang <calumhuang@163.com>
"""

import os
import sys
import uuid
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# 标识: 63616c756d6875616e67403136332e636f6d
__author__ = bytes.fromhex("63616c756d6875616e67403136332e636f6d").decode()

# 确保能找到 core 模块
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from models import (
    Resume, JobDescription, MatchResult, Greeting,
    AnalyzeResponse, ErrorResponse,
)
from core.parser import parse_resume_file, parse_to_resume
from core.analyzer import parse_jd
from core.matcher import match_resume_to_jd
from core.generator import generate_greeting
from core.ocr import ocr_image
from core.auth import register_user, login_user, _verify_token, save_analysis, get_history


# ─── App 初始化 ──────────────────────────────────────────

app = FastAPI(
    title="简历助手 API",
    description="通用简历分析工具 — 支持 PDF/Word/Markdown/TXT 解析、JD 匹配、招呼语生成",
    version="0.1.0",
)

# CORS — 允许移动端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)


@app.get("/app", response_class=HTMLResponse)
async def web_app():
    """简洁的 Web 界面"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>index.html not found</h1>"

# 内存存储 — 后续可换 SQLite/Redis
_resume_store: dict = {}       # resume_id -> Resume dict
_upload_dir = Path(__file__).parent / "uploads"
_upload_dir.mkdir(exist_ok=True)


# ─── 用户系统 ────────────────────────────────────────────

@app.post("/api/auth/register")
def api_register(data: dict):
    """注册"""
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    name = (data.get("name") or "").strip()
    if not email or not password:
        raise HTTPException(400, "邮箱和密码不能为空")
    if len(password) < 6:
        raise HTTPException(400, "密码至少6位")
    result = register_user(email, password, name)
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/auth/login")
def api_login(data: dict):
    """登录"""
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    result = login_user(email, password)
    if not result["ok"]:
        raise HTTPException(401, result["error"])
    return result


def _get_user_id(request) -> Optional[int]:
    """从请求中提取用户 ID"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return _verify_token(auth[7:])
    return None


@app.get("/api/history")
async def api_history(request: Request):
    """获取分析历史"""
    user_id = _get_user_id(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    return {"history": get_history(user_id)}


@app.get("/api/history/{analysis_id}")
async def api_history_detail(analysis_id: int, request: Request):
    """获取历史详情"""
    user_id = _get_user_id(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    from core.auth import get_analysis_detail
    detail = get_analysis_detail(user_id, analysis_id)
    if not detail:
        raise HTTPException(404, "记录不存在")
    return detail


# ─── API 路由 ────────────────────────────────────────────

@app.get("/")
def root():
    """健康检查"""
    return {
        "name": "简历助手 API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    上传简历文件，返回 resume_id

    支持: PDF, DOCX, DOC, MD, TXT
    curl -F "file=@resume.pdf" http://localhost:8000/api/resume/upload
    """
    # 检查文件类型
    filename = file.filename or "resume"
    ext = Path(filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc", ".md", ".markdown", ".txt", ".text", ".rtf"):
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    # 保存文件
    resume_id = str(uuid.uuid4())[:8]
    save_path = _upload_dir / f"{resume_id}_{filename}"
    content = await file.read()
    save_path.write_bytes(content)

    # 解析
    try:
        result = parse_resume_file(str(save_path))
    except Exception as e:
        raise HTTPException(400, f"简历解析失败: {str(e)}")

    # 存储
    resume_data = {
        "id": resume_id,
        "filename": filename,
        "uploaded_at": datetime.now().isoformat(),
        **result,
    }
    _resume_store[resume_id] = resume_data

    # 构建 Resume 模型用于返回
    resume_obj = Resume(**{k: v for k, v in result.items()
                           if k in Resume.model_fields})

    return {
        "resume_id": resume_id,
        "filename": filename,
        "resume": resume_obj.model_dump(),
        "message": "简历解析成功",
    }


@app.get("/api/resume/{resume_id}")
def get_resume(resume_id: str):
    """获取已解析的简历"""
    if resume_id not in _resume_store:
        raise HTTPException(404, "简历不存在")
    data = _resume_store[resume_id]
    resume_obj = Resume(**{k: v for k, v in data.items()
                           if k in Resume.model_fields})
    return {
        "resume_id": resume_id,
        "filename": data.get("filename", ""),
        "resume": resume_obj.model_dump(),
    }


@app.post("/api/resume/parse-text")
def parse_resume_text(resume_text: str = Form(...)):
    """
    直接粘贴简历文本进行解析（不上传文件）

    curl -X POST http://localhost:8000/api/resume/parse-text \
      -d "resume_text=张三\n前端工程师\n..."
    """
    resume_id = str(uuid.uuid4())[:8]
    result = parse_to_resume(resume_text)

    _resume_store[resume_id] = {
        "id": resume_id,
        "filename": "pasted_text",
        "uploaded_at": datetime.now().isoformat(),
        **result,
    }

    resume_obj = Resume(**{k: v for k, v in result.items()
                           if k in Resume.model_fields})

    return {
        "resume_id": resume_id,
        "resume": resume_obj.model_dump(),
        "message": "文本解析成功",
    }


@app.post("/api/analyze")
def analyze(resume_id: str = Form(...),
            jd_text: str = Form(...),
            platform: str = Form("default")):
    """
    核心接口：分析简历与 JD 的匹配度，生成招呼语

    Args:
        resume_id: 上传简历时拿到的 ID
        jd_text:   岗位描述全文
        platform:  boss / linkedin / lagou / default

    curl -X POST http://localhost:8000/api/analyze \
      -d "resume_id=abc123" \
      -d "jd_text=岗位职责：..." \
      -d "platform=boss"
    """
    if resume_id not in _resume_store:
        raise HTTPException(404, "简历不存在，请先上传简历")

    if not jd_text or len(jd_text.strip()) < 10:
        raise HTTPException(400, "JD 文本太短，请提供完整的岗位描述")

    resume_data = _resume_store[resume_id]

    # 解析 JD
    jd_data = parse_jd(jd_text)
    jd_obj = JobDescription(**jd_data)

    # 匹配
    match_data = match_resume_to_jd(resume_data, jd_data)
    match_obj = MatchResult(**match_data)

    # 生成招呼语
    greeting_data = generate_greeting(resume_data, jd_data, match_data, platform)
    greeting_obj = Greeting(**greeting_data)

    return AnalyzeResponse(
        job=jd_obj,
        match=match_obj,
        greeting=greeting_obj,
        resume_summary=f"{resume_data.get('name', '')} | "
                       f"{resume_data.get('title', '')} | "
                       f"{resume_data.get('years_of_experience', 0)}年经验",
    ).model_dump()


@app.post("/api/analyze-once")
def analyze_once(resume_text: str = Form(...),
                 jd_text: str = Form(...),
                 platform: str = Form("default")):
    """
    一步式分析：不需要先上传简历，直接粘贴简历和 JD 文本

    适合快速试用和 Hermes 集成
    """
    if not resume_text or len(resume_text.strip()) < 20:
        raise HTTPException(400, "简历文本太短")
    if not jd_text or len(jd_text.strip()) < 10:
        raise HTTPException(400, "JD 文本太短")

    # 解析简历
    resume_result = parse_to_resume(resume_text)

    # 解析 JD
    jd_data = parse_jd(jd_text)

    # 匹配
    match_data = match_resume_to_jd(resume_result, jd_data)

    # 生成招呼语
    greeting_data = generate_greeting(resume_result, jd_data, match_data, platform)

    return AnalyzeResponse(
        job=JobDescription(**jd_data),
        match=MatchResult(**match_data),
        greeting=Greeting(**greeting_data),
        resume_summary=f"{resume_result.get('name', '')} | "
                       f"{resume_result.get('title', '')} | "
                       f"{resume_result.get('years_of_experience', 0)}年经验",
    ).model_dump()


# ─── OCR 接口 ────────────────────────────────────────────

@app.post("/api/ocr")
async def ocr_screenshot(file: UploadFile = File(...)):
    """
    OCR 识别截图/图片中的文字

    支持 jpg/png/bmp/tiff，自动中英文混合识别
    curl -F "file=@screenshot.png" http://localhost:8000/api/ocr
    """
    ext = Path(file.filename or "screenshot").suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"):
        raise HTTPException(400, f"不支持的图片格式: {ext}，请使用 jpg/png/bmp 截图")

    # 保存
    img_id = str(uuid.uuid4())[:8]
    img_path = _upload_dir / f"ocr_{img_id}{ext}"
    content = await file.read()
    img_path.write_bytes(content)

    # OCR
    try:
        text = ocr_image(str(img_path))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"OCR 识别失败: {str(e)}")

    return {
        "text": text,
        "length": len(text),
        "message": f"识别到 {len(text)} 个字符" if text else "未识别到文字，请确认截图清晰度",
    }


@app.post("/api/ocr-base64")
async def ocr_base64(data: dict):
    """
    OCR 识别 base64 编码的图片（App 相机直接拍照用）
    """
    import base64
    try:
        img_data = base64.b64decode(data.get("image", ""))
    except Exception:
        raise HTTPException(400, "无效的 base64 图片数据")

    img_id = str(uuid.uuid4())[:8]
    img_path = _upload_dir / f"ocr_b64_{img_id}.png"
    img_path.write_bytes(img_data)

    try:
        text = ocr_image(str(img_path))
    except Exception as e:
        raise HTTPException(500, f"OCR 识别失败: {str(e)}")

    return {"text": text, "length": len(text)}


# ─── 错误处理 ────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=str(exc.detail)).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="服务器内部错误", detail=str(exc)).model_dump(),
    )


# ─── CLI 直调入口 ────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  简历助手 Backend API")
    print("  http://localhost:8000")
    print("  Swagger 文档: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
