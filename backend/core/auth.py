"""
用户认证 & 历史记录模块 (c) calumhuang@163.com

使用 SQLite + JWT，支持：
- 用户注册/登录
- 分析历史保存和查询
"""

import sqlite3
import hashlib
import hmac
import json
import time
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "app.db"

# 简单的 JWT secret（生产环境应该从环境变量读取）
JWT_SECRET = os.environ.get("JWT_SECRET", "resume-assistant-secret-change-me")


def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_db():
    """初始化数据库表"""
    db = _get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_text TEXT,
            jd_text TEXT,
            job_title TEXT DEFAULT '',
            company TEXT DEFAULT '',
            match_score INTEGER DEFAULT 0,
            greeting_short TEXT DEFAULT '',
            risk_flags TEXT DEFAULT '[]',
            raw_result TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id, created_at DESC);
    """)
    db.commit()
    db.close()


# 初始化
init_db()


def _hash_password(password: str) -> str:
    """简单的密码哈希"""
    salt = "resume-salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def _make_token(user_id: int) -> str:
    """生成简单的 JWT-like token"""
    header = json.dumps({"alg": "HS256", "typ": "JWT"})
    payload = json.dumps({"user_id": user_id, "exp": int(time.time()) + 86400 * 30})
    msg = base64_url_encode(header) + "." + base64_url_encode(payload)
    sig = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return msg + "." + sig


def _verify_token(token: str) -> Optional[int]:
    """验证 token，返回 user_id"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        msg = parts[0] + "." + parts[1]
        expected_sig = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(parts[2], expected_sig):
            return None
        payload = json.loads(base64_url_decode(parts[1]))
        if payload.get("exp", 0) < time.time():
            return None
        return payload["user_id"]
    except Exception:
        return None


def base64_url_encode(data: str) -> str:
    import base64
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def base64_url_decode(data: str) -> str:
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data).decode()


# ── 用户操作 ──

def register_user(email: str, password: str, name: str = "") -> dict:
    """注册用户"""
    db = _get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email, _hash_password(password), name)
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        token = _make_token(user["id"])
        return {"ok": True, "token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "该邮箱已注册"}
    finally:
        db.close()


def login_user(email: str, password: str) -> dict:
    """登录"""
    db = _get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    if not user:
        return {"ok": False, "error": "邮箱未注册"}
    if user["password_hash"] != _hash_password(password):
        return {"ok": False, "error": "密码错误"}
    token = _make_token(user["id"])
    return {"ok": True, "token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}


# ── 历史记录 ──

def save_analysis(user_id: int, resume_text: str, jd_text: str,
                   job_title: str, company: str, match_score: int,
                   greeting_short: str, risk_flags: list, raw_result: dict) -> int:
    """保存分析记录"""
    db = _get_db()
    cur = db.execute(
        """INSERT INTO analyses (user_id, resume_text, jd_text, job_title, company,
           match_score, greeting_short, risk_flags, raw_result)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, resume_text, jd_text, job_title, company,
         match_score, greeting_short, json.dumps(risk_flags, ensure_ascii=False),
         json.dumps(raw_result, ensure_ascii=False))
    )
    db.commit()
    aid = cur.lastrowid
    db.close()
    return aid


def get_history(user_id: int, limit: int = 20) -> list:
    """获取分析历史"""
    db = _get_db()
    rows = db.execute(
        "SELECT id, job_title, company, match_score, greeting_short, created_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    return [{
        "id": r["id"],
        "job_title": r["job_title"],
        "company": r["company"],
        "match_score": r["match_score"],
        "greeting_short": r["greeting_short"],
        "created_at": r["created_at"],
    } for r in rows]


def get_analysis_detail(user_id: int, analysis_id: int) -> Optional[dict]:
    """获取单条分析详情"""
    db = _get_db()
    row = db.execute(
        "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id)
    ).fetchone()
    db.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "job_title": row["job_title"],
        "company": row["company"],
        "match_score": row["match_score"],
        "greeting_short": row["greeting_short"],
        "risk_flags": json.loads(row["risk_flags"]),
        "raw_result": json.loads(row["raw_result"]),
        "created_at": row["created_at"],
    }
