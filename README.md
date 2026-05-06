# 📋 简历助手 (Resume Assistant)

> 智能简历匹配与打招呼语生成工具  
> 上传简历 + 粘贴 JD → 秒出匹配分析、招呼语、注意事项

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Web-brightgreen)]()

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📄 **简历解析** | 支持 PDF / Word / Markdown / TXT 上传，自动提取结构化信息 |
| 📸 **JD 截图 OCR** | 上传 BOSS直聘/猎聘截图，自动识别岗位描述文字 |
| 🔍 **智能匹配** | 逐项对比简历与 JD，输出匹配度分数和详细分析 |
| 💬 **招呼语生成** | 自动生成个性化打招呼语，支持 BOSS直聘/LinkedIn/拉勾风格 |
| ⚠️ **注意事项** | 根据匹配结果数据化生成风险提示（年限/学历/技能/地点/薪资） |
| 📱 **多端支持** | 网页版 + Android App（Capacitor 封装） |
| 👤 **用户系统** | 注册/登录，历史记录保存 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python 依赖
pip install -r backend/requirements.txt

# 系统依赖（OCR 引擎）
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

### 2. 启动服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. 打开网页

浏览器访问：**http://localhost:8000/app**

---

## 🏗 项目结构

```
resume-assistant/
├── backend/                    # 后端服务 (FastAPI)
│   ├── main.py                 # API 入口 + 路由
│   ├── models.py               # Pydantic 数据模型
│   ├── requirements.txt        # Python 依赖
│   ├── core/                   # 核心引擎
│   │   ├── parser.py           # 简历解析 (PDF/Word/MD/TXT)
│   │   ├── analyzer.py         # JD 结构化分析
│   │   ├── matcher.py          # 智能匹配引擎
│   │   ├── generator.py        # 招呼语生成 + 建议
│   │   ├── ocr.py              # OCR 识别 (Tesseract)
│   │   └── auth.py             # 用户系统 (JWT + SQLite)
│   ├── static/
│   │   └── index.html          # 前端网页（单页应用）
│   ├── data/                   # SQLite 数据库
│   └── uploads/                # 上传文件
├── app/                        # 移动 App (Capacitor)
│   ├── package.json
│   ├── capacitor.config.json
│   └── www/index.html          # App 内嵌网页
└── README.md
```

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 健康检查 |
| GET | `/app` | 网页界面 |
| POST | `/api/resume/upload` | 上传简历文件 |
| POST | `/api/resume/parse-text` | 粘贴简历文本 |
| POST | `/api/analyze` | 匹配分析（需 resume_id） |
| POST | `/api/analyze-once` | 一步式分析（直接粘贴简历+JD） |
| POST | `/api/ocr` | 图片 OCR 识别 |
| POST | `/api/ocr-base64` | Base64 图片 OCR |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/history` | 分析历史（需登录） |

---

## 🔧 API 使用示例

```bash
# 一步式分析
curl -X POST http://localhost:8000/api/analyze-once \
  -d "resume_text=张三 | 高级后端工程师 | 5年经验
技能: Python, Go, Docker, Kubernetes
经历: 2020-2024 阿里巴巴 | 高级后端工程师" \
  -d "jd_text=【岗位】高级后端工程师
【任职要求】
1. 5年以上后端开发经验
2. 精通Python或Go
3. 熟悉Docker、Kubernetes" \
  -d "platform=boss"
```

**响应示例：**
```json
{
  "job": {
    "title": "高级后端工程师",
    "company": "",
    "location": "",
    "salary_range": ""
  },
  "match": {
    "overall_score": 91,
    "summary": "[高匹配度] 综合匹配度 91%...",
    "matches": [...],
    "gaps": [...]
  },
  "greeting": {
    "short": "您好，看到贵公司正在招聘高级后端工程师...",
    "full": "贵公司的招聘负责人您好...",
    "risk_flags": ["JD 未标注薪资范围..."]
  }
}
```

---

## 📱 构建 Android App

### 前置条件
- Node.js 18+
- Java JDK 17+
- Android Studio + Android SDK 34

### 构建步骤

```bash
cd app
npm install

# 初始化 Android 平台
npx cap add android

# 修改 API 地址（部署后端后）
# 编辑 capacitor.config.json → server.url

# 同步 web 资源到 Android 工程
npx cap sync

# 在 Android Studio 中打开
npx cap open android
```

Android Studio 中：**Build → Generate Signed Bundle / APK → Android App Bundle**

详细的部署和上架指南见 [DEPLOY.md](app/DEPLOY.md)

---

## 🎯 支持的平台

招呼语生成支持以下平台风格：

- **BOSS直聘** — 短版招呼语（~100字限制）
- **LinkedIn** — 完整长版招呼语
- **拉勾** — 拉勾风格
- **通用** — 默认通用

---

## 🧠 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python) |
| OCR 引擎 | Tesseract 5.5 + pytesseract |
| PDF 解析 | PyMuPDF |
| Word 解析 | python-docx |
| 用户认证 | JWT + SQLite |
| 移动 App | Capacitor 6 (WebView) |
| 前端 | 单页 HTML/CSS/JS（移动端适配） |

---

## 📝 License

MIT License — 详见 [LICENSE](LICENSE)

---

## 👤 作者

黄凯伦 (Calum Huang) — calumhuang@163.com
