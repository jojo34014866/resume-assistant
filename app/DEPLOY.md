# 简历助手 — 安卓 App 上架指南

## 当前进度

✅ 后端 API (FastAPI) — 完成
✅ OCR 引擎 (Tesseract) — 完成
✅ 匹配引擎 + 招呼语生成 — 完成
✅ Capacitor 项目创建 — 完成（android/ 目录已生成）
✅ 用户系统（JWT + SQLite） — 完成
⏳ Java 安装中...
⬜ Android SDK
⬜ 签名证书
⬜ 云端部署
⬜ 上架

---

## 第一步：安装 Android Studio（在你的 Windows 上）

WSL 无法运行 Android 模拟器，推荐在 Windows 上装 Android Studio。

1. 下载 Android Studio：https://developer.android.com/studio
2. 安装时勾选 Android SDK
3. 打开 Android Studio → SDK Manager → 安装 Android 14 (API 34)

---

## 第二步：构建 AAB（Android App Bundle）

```bash
# 进入项目
cd /home/administrator/resume-app

# 同步 web 资源
npx cap sync

# 在 Android Studio 中打开
npx cap open android
```

Android Studio 打开后：
1. Build → Generate Signed Bundle / APK → Android App Bundle
2. 创建签名密钥（记住密码和别名）
3. 等待构建完成 → 生成 `android/app/release/app-release.aab`

---

## 第三步：部署后端到云服务器

### 选项 A：阿里云/腾讯云轻量应用服务器（推荐）

1. 购买轻量服务器（2核2G，约68元/月）
2. SSH 连接后：

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y python3 python3-pip tesseract-ocr tesseract-ocr-chi-sim

# 上传代码
scp -r /home/administrator/resume-assistant/backend root@你的服务器IP:/app/

# 安装 Python 依赖
pip3 install fastapi uvicorn pymupdf python-docx pydantic python-multipart pytesseract Pillow

# 启动服务（生产环境用 gunicorn + nginx）
cd /app && uvicorn main:app --host 0.0.0.0 --port 8000
```

3. 配置 Nginx 反向代理 + SSL（Let's Encrypt）
4. 把域名指向服务器 IP

### 选项 B：免费部署

用 Railway / Render 免费托管（有休眠限制）：

1. 在 GitHub 上创建仓库
2. 连接 Railway/render.com
3. 自动部署

---

## 第四步：修改 API 地址

部署后端后，修改 App 的 API 地址：

```bash
# 编辑 capacitor.config.json
# 把 "url": "http://10.0.2.2:8000/app" 
# 改成 "url": "https://你的域名.com/app"
npx cap sync
```

---

## 第五步：上架 Google Play

1. 注册 Google Play 开发者账号（$25 一次性费用）
2. Play Console → 创建应用
3. 上传 .aab 文件
4. 填写应用信息（描述、截图、隐私政策）
5. 提交审核（通常 1-3 天）

**所需素材清单：**
- 应用图标：512x512 PNG
- 应用截图：至少 2 张（1080px 宽）
- 隐私政策链接
- 简短描述（80字）+ 完整描述

---

## 第六步：华为应用市场

1. 注册华为开发者联盟（免费）
2. 上传 AAB 或 APK
3. 审核约 3-5 天

---

## 项目文件结构

```
resume-assistant/          # 后端
├── backend/
│   ├── main.py            # FastAPI 服务
│   ├── models.py
│   ├── core/
│   │   ├── parser.py
│   │   ├── analyzer.py
│   │   ├── matcher.py
│   │   ├── generator.py
│   │   ├── ocr.py
│   │   └── auth.py        # 用户系统
│   └── data/
│       └── app.db         # SQLite 用户+历史

resume-app/                # 移动 App
├── www/
│   └── index.html         # 前端页面（已适配移动端）
├── android/               # Capacitor 生成的 Android 工程
├── capacitor.config.json
└── package.json
```

---

## 快速命令参考

```bash
# 启动后端开发服务器
cd resume-assistant
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 测试 OCR
curl -X POST http://localhost:8000/api/ocr -F "file=@screenshot.png"

# 测试分析
curl -X POST http://localhost:8000/api/analyze-once \
  -d "resume_text=..." -d "jd_text=..." -d "platform=boss"

# 构建 APK
cd resume-app
npx cap sync
npx cap open android  # 然后在 Android Studio 中 Build

# 访问网页版
浏览器打开: http://localhost:8000/app
```
