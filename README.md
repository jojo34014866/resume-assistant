# 📋 简历助手 (Resume Assistant)

> 上传简历 + 粘贴 JD → 秒出匹配分析、招呼语、注意事项

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📄 **简历解析** | PDF / Word / Markdown / TXT → 自动提取姓名、技能、经历、学历 |
| 📸 **JD 截图 OCR** | 上传 BOSS直聘/猎聘截图 → 自动识别文字 |
| 🔍 **智能匹配** | 逐项对比简历 vs JD，0-100 分 + 同义词映射 |
| 💬 **招呼语生成** | BOSS直聘/LinkedIn/拉勾 多平台风格 |
| ⚠️ **精准提醒** | 根据实际匹配数据生成注意事项（非套话） |
| 📱 **移动端可用** | 手机浏览器直接打开，适配触屏 |

---

## 🚀 快速开始

### 1. 安装

```bash
# Python 依赖
pip install -r backend/requirements.txt

# OCR 引擎（需要 sudo）
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

### 2. 启动

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. 打开

**浏览器访问：http://localhost:8000/app**

手机同 WiFi → `http://<电脑IP>:8000/app`

---

## 📁 项目结构

```
resume-assistant/
├── backend/
│   ├── main.py              # FastAPI 入口，9 个接口
│   ├── models.py            # Pydantic 数据模型
│   ├── requirements.txt     # Python 依赖
│   ├── core/
│   │   ├── parser.py        # 简历解析 (PDF/Word/MD/TXT)
│   │   ├── analyzer.py      # JD 结构化分析
│   │   ├── matcher.py       # 智能匹配引擎 + 同义词映射
│   │   ├── generator.py     # 招呼语生成 + 注意事项
│   │   ├── ocr.py           # OCR (Tesseract 中英文)
│   │   └── auth.py          # 用户系统 (JWT + SQLite)
│   └── static/
│       └── index.html       # 前端网页
├── app/                     # Android App (Capacitor)
│   ├── capacitor.config.json
│   ├── package.json
│   └── www/index.html
├── scripts/
│   ├── quick_test.sh        # API 测试脚本
│   ├── install_deps.sh      # 依赖安装
│   └── install_ocr.sh       # OCR 安装
└── README.md
```

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/app` | 网页界面 |
| POST | `/api/resume/upload` | 上传简历文件 (PDF/Word/MD/TXT) |
| POST | `/api/resume/parse-text` | 粘贴简历文本 |
| POST | `/api/analyze` | 匹配分析（先上传简历拿到 ID） |
| POST | `/api/analyze-once` | 一步式分析（粘贴简历 + JD 直出结果） |
| POST | `/api/ocr` | 图片 OCR 识别 |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/history` | 历史记录（需 Token） |

### 使用示例

```bash
# 一步式分析
curl -X POST http://localhost:8000/api/analyze-once \
  -d "resume_text=张三 | 后端工程师 | 5年经验
技能: Python, Go, Docker, Kubernetes
经历: 2020-2024 阿里巴巴 | 高级后端工程师" \
  -d "jd_text=【岗位】高级后端工程师
【任职要求】
1. 5年以上后端开发经验
2. 精通Python或Go
3. 熟悉Docker、K8s" \
  -d "platform=boss"
```

```json
// 响应
{
  "match": {
    "overall_score": 91,
    "matches": [{"jd_requirement": "精通Python...", "match_level": "full"}],
    "gaps": []
  },
  "greeting": {
    "short": "您好，看到贵公司正在招聘...",
    "risk_flags": ["JD 未标注薪资范围..."]
  }
}
```

---

## 🧠 匹配引擎说明

### 技能词库覆盖范围

- 🖥 **开发** Python/Java/Go/JS/React/Vue/Docker/K8s...
- 🔧 **IT 运维** ITIL/AD域/Helpdesk/桌面运维/TCP-IP/DNS/DHCP/O365...
- 📊 **数据** SQL/MySQL/Redis/Spark/Kafka...
- 🎨 **设计** Figma/Photoshop/Sketch...
- 📋 **产品运营** 数据分析/用户研究/竞品分析...

### 同义词映射（例）

| JD 描述 | 自动映射到简历中的 |
|---------|------------------|
| 计算机软硬件知识 | Windows, MacOS, 硬件故障, 桌面运维 |
| 网络基础知识 | TCP/IP, DNS, DHCP, 网络配置 |
| Helpdesk 经验 | Helpdesk, 桌面运维, IT 运维, 服务台 |

### 注意事项生成规则

每条注意事项都是数据驱动的，不是模板：

- 年限不足 → 「JD 要求约 5 年经验，你的简历约 4 年。可用项目经历弥补。」
- 学历不符 → 「若不完全符合，可突出实战经验来弥补。」
- 技能缺失 → 「缺失关键技术栈：Java, Spring。若实际有但简历未体现，请补充。」
- 地点不匹配 → 「你在上海，岗位在北京。确认是否异地。」
- 薪资未标 → 「JD 未标注薪资，建议尽早确认。」

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| OCR | Tesseract 5.5 (中英文) |
| PDF 解析 | PyMuPDF |
| Word 解析 | python-docx |
| 用户认证 | JWT + SQLite |
| 前端 | 单页 HTML/CSS/JS |

---

## 📝 License

**MIT License — Non-Commercial**

本软件仅供个人、教育、研究及非商业用途免费使用。

**禁止商用**（包括但不限于收费分发、作为付费服务的一部分使用等）。
商业使用需获得作者书面授权：calumhuang@163.com

详见 [LICENSE](LICENSE)

---

## 🟢 Hermes Agent 绿皮书

[**查看完整指南 →**](https://github.com/jojo34014866/hermes-green-book)

涵盖：快速上手 · 多 Agent 协作 · 定时任务 · 多平台网关 · 记忆与技能 · MCP 服务器 · 常见问题 20+ · 进阶玩法 · 命令速查
