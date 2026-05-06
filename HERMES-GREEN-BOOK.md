# 🟢 Hermes Agent 绿皮书

> **全覆盖使用指南 — 从零到高手**
> 热门技能 · 常见问题 · 进阶技巧 · 速查手册

---

## 目录

1. [快速上手](#1-快速上手)
2. [热门技能精选](#2-热门技能精选)
3. [常见问题与解决方案](#3-常见问题与解决方案)
4. [进阶玩法](#4-进阶玩法)
5. [配置速查](#5-配置速查)
6. [命令速查表](#6-命令速查表)

---

## 1. 快速上手

### 安装

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### 三步开始

```bash
hermes setup          # 1. 配置向导（选模型、API key）
hermes                # 2. 进入对话
/help                 # 3. 查看所有命令
```

### 五个必知命令

| 命令 | 作用 |
|------|------|
| `hermes` | 进入对话 |
| `hermes chat -q "问题"` | 单次提问，不进入对话 |
| `/new` | 开新会话 |
| `hermes model` | 切换模型 |
| `hermes doctor` | 诊断环境 |

---

## 2. 热门技能精选

### 2.1 🔥 多 Agent 协作

Hermes 最强大的能力之一是同时运行多个 Agent 分工协作。

**方式一：`delegate_task`（推荐，轻量）**

```
# 单任务委托
「帮我把这个 PR review 一下」→ Agent 自动 delegate_task

# 并行多任务
「同时研究 A 和 B，然后汇总给我」→ Agent 并行 spawn 两个子 Agent
```

**方式二：tmux 自主 Agent（重量，适合长任务）**

```bash
# 启动一个独立 Agent 做后端
tmux new-session -d -s backend -x 120 -y 40 'hermes -w'

# 发任务给它
tmux send-keys -t backend 'Build REST API for user management' Enter

# 检查进度
tmux capture-pane -t backend -p | tail -30
```

**何时用 delegate_task vs 独立进程：**

| | delegate_task | 独立进程 |
|---|-------------|---------|
| 时长 | 几分钟 | 几小时/天 |
| 隔离性 | 共享进程 | 完全独立 |
| 适用 | 快速并行子任务 | 长期自主任务 |

### 2.2 🕐 定时任务 Cron

让 Hermes 定时自动执行任务。

```bash
# 每天 9 点总结 GitHub Trending
hermes cron create "0 9 * * *" --prompt "总结今天 GitHub Trending 的前 10 个项目"

# 每 30 分钟检查服务器状态
hermes cron create "30m" --prompt "检查服务器 CPU/内存/磁盘是否正常"

# 每周一生成周报
hermes cron create "every monday 9am" --prompt "生成本周工作总结"

# 管理
hermes cron list        # 查看所有任务
hermes cron pause ID    # 暂停
hermes cron run ID      # 立即执行一次
hermes cron remove ID   # 删除
```

### 2.3 💬 多平台消息网关

同一个 Hermes Agent 可以在多个平台使用：

```bash
hermes gateway setup    # 交互式配置平台
hermes gateway run      # 启动网关（前台）
hermes gateway install  # 安装为后台服务
```

**支持的平台（20+）：**

| 平台 | 配置要点 |
|------|---------|
| Telegram | Bot Token（@BotFather 获取） |
| Discord | Bot Token + 开启 Message Content Intent |
| Slack | Socket Mode + OAuth Token |
| WhatsApp | QR 码扫码绑定 |
| 微信 | 企业微信应用配置 |
| 钉钉/飞书 | Webhook + App 凭证 |
| Email | IMAP/SMTP 配置 |
| Signal/Matrix | 扫码或 Token |

**跨平台同步：** 在 Telegram 聊到一半，切到手机 Discord 继续 `/resume` 恢复会话。

### 2.4 🧠 持久记忆与技能

**记忆系统：** Hermes 会记住你的偏好、环境、修正。

```bash
hermes memory setup     # 配置记忆后端
hermes memory status    # 查看状态
```

**技能系统：** Agent 学会了就保存为技能，下次自动加载。

```bash
hermes skills list              # 已安装的技能
hermes skills search "git"      # 搜索技能市场
hermes skills install ID        # 安装
/skill <name>                   # 对话中加载技能
```

**最受欢迎的技能（社区热门）：**

| 技能 | 用途 |
|------|------|
| `test-driven-development` | TDD 红-绿-重构循环 |
| `systematic-debugging` | 四阶段根因调试法 |
| `writing-plans` | 写实施计划 |
| `github-pr-workflow` | PR 生命周期管理 |
| `subagent-driven-development` | 委托子 Agent 执行计划 |
| `python-debugpy` | Python 远程调试 |
| `node-inspect-debugger` | Node.js 调试 |
| `obsidian` | Obsidian 笔记读写 |
| `huggingface-hub` | HF 模型管理 |
| `spotify` | Spotify 播放控制 |

### 2.5 🔌 MCP 服务器

连接外部工具和数据源。

```bash
hermes mcp add my-server --command "python server.py"  # 本地进程
hermes mcp add my-server --url "http://localhost:3000"  # HTTP 服务
hermes mcp test my-server    # 测试连接
hermes mcp list              # 列出所有
```

### 2.6 📦 多 Profile 隔离

不同项目用不同的 Agent 配置：

```bash
hermes profile create work    # 创建工作 Profile
hermes profile use work       # 切换到工作 Profile
hermes -p work                # 临时用某个 Profile
```

**实战场景：**
- `work` — 公司项目，OpenAI 模型，禁用娱乐工具
- `personal` — 个人项目，DeepSeek，全工具
- `writing` — 写作专用，Claude，只开文件和搜索

---

## 3. 常见问题与解决方案

### 3.1 安装与启动

**Q: 安装后 `hermes` 命令找不到？**
```bash
source ~/.bashrc          # 刷新 PATH
# 或重新打开终端
```

**Q: WSL2 上 Gateway 服务关闭终端就挂了？**
```bash
# 方案一：启用 systemd
echo "[boot]" | sudo tee -a /etc/wsl.conf
echo "systemd=true" | sudo tee -a /etc/wsl.conf
# 重启 WSL 后生效

# 方案二：启用用户 linger
sudo loginctl enable-linger $USER
```

**Q: 启动报错 "No models provided"？**
```bash
# config.yaml 编码问题（Windows BOM）
# 确保保存为 UTF-8 without BOM
hermes doctor --fix
```

### 3.2 模型与 API

**Q: 怎么换模型？**
```bash
hermes model              # 交互式选择
# 或直接指定
hermes chat -m "anthropic/claude-sonnet-4"
```

**Q: API key 放哪里？**
```bash
hermes config env-path    # 查看 .env 路径
# 编辑 .env 文件，写入：
# OPENROUTER_API_KEY=sk-xxx
# ANTHROPIC_API_KEY=sk-ant-xxx
```

**Q: Copilot 返回 403？**
- `gh auth login` 的 token 不能用于 Copilot API
- 必须用 Copilot 专用的 OAuth 流程：`hermes model` → 选 GitHub Copilot → 按提示认证

**Q: 怎么用国产模型（DeepSeek/GLM/Kimi）？**
```bash
# 在 .env 中设置对应的 key
DEEPSEEK_API_KEY=sk-xxx
GLM_API_KEY=xxx
KIMI_API_KEY=sk-xxx

# 然后切换模型
hermes model  # 选择对应 provider
```

### 3.3 工具与命令

**Q: 工具开关不生效？**
- 工具变更需要 `/reset`（开新会话）才生效
- 这是为了保持 prompt 缓存有效

**Q: 某些工具消失了？**
```bash
hermes tools              # 交互式查看
hermes tools list         # 列出所有工具及状态
# 部分工具需要环境变量（如 API key）才显示
```

**Q: 怎么禁用危险命令的确认提示？**
```bash
# 三种方式
hermes config set approvals.mode smart   # 推荐：AI 判断风险
hermes config set approvals.mode off     # 激进：全跳过
hermes --yolo                            # 单次跳过
```

### 3.4 Gateway 消息平台

**Q: Discord Bot 不说话？**
1. Discord Developer Portal → Bot → Privileged Gateway Intents
2. 开启 **Message Content Intent**
3. 重启 Gateway

**Q: Slack Bot 只在私聊中回复？**
- 需要订阅 `message.channels` 事件

**Q: Telegram Bot 收不到消息？**
```bash
# 检查 Bot Token 是否正确
# 检查是否已经给 Bot 发过 /start
# 查看日志
grep "telegram" ~/.hermes/logs/gateway.log | tail -20
```

### 3.5 技能与记忆

**Q: 技能不加载？**
```bash
hermes skills config     # 检查平台启用状态
/skill <name>            # 手动加载
hermes -s skill1,skill2  # 启动时预加载
```

**Q: Agent 忘了之前说过的事？**
```bash
hermes memory status     # 检查记忆状态
hermes memory setup      # 重新配置
# 或显式告诉 Agent: "记住这件事"
```

**Q: 技能太多，想清理？**
```bash
hermes curator status    # 查看技能状态
hermes curator run       # 自动清理不活跃的技能
```

### 3.6 性能与优化

**Q: Agent 跑得太慢？**
```bash
# 减少工具集
hermes tools disable browser image_gen spotify

# 降低思考级别
/reasoning low

# 使用更快的模型
hermes model  # 选轻量模型
```

**Q: Token 消耗太大？**
```bash
/usage                   # 查看当前会话消耗
hermes config set compression.enabled true   # 开启上下文压缩
hermes config set compression.threshold 0.5  # 50% 时触发压缩
```

**Q: 怎么查看日志排查问题？**
```bash
hermes logs --follow              # 实时日志
grep ERROR ~/.hermes/logs/errors.log | tail -20
grep "failed" ~/.hermes/logs/gateway.log | tail -20
```

### 3.7 Windows/WSL 特有

**Q: WSL2 中文件权限问题？**
```bash
# 不要跨文件系统操作（/mnt/c/ ↔ ~/）
# 项目放 ~/ 目录内，不要放 /mnt/c/Users/
```

**Q: WSL 中文乱码？**
```bash
export LANG=C.UTF-8
# 或加到 ~/.bashrc
echo "export LANG=C.UTF-8" >> ~/.bashrc
```

---

## 4. 进阶玩法

### 4.1 🎯 Agent 协作流水线

用 cron + delegate_task 搭建自动化工作流：

```bash
# 第一步：每天凌晨拉取数据
hermes cron create "0 2 * * *" \
  --prompt "从 API 拉取今日数据到 ~/data/today.csv"

# 第二步：早晨分析数据
hermes cron create "0 8 * * *" \
  --prompt "分析 ~/data/today.csv 中昨天的数据，生成报告到 ~/reports/daily.md" \
  --context_from <job1-id>
```

### 4.2 🏠 智能家居 + Agent

```bash
hermes tools enable homeassistant
# 配置 Home Assistant 连接后
「把客厅灯调成暖色，打开空调到 26 度」
「如果温度超过 30 度就开空调」
```

### 4.3 🔄 Git Worktree 并行开发

```bash
# 多个 Agent 同时改不同分支，互不冲突
hermes -w   # worktree 模式
tmux new-session -d -s agent1 'hermes -w'
tmux new-session -d -s agent2 'hermes -w'
```

### 4.4 🎨 自定义 Skill 开发

当你发现 Hermes 反复执行某个工作流，可以保存为技能：

```bash
# 1. 在对话中成功完成一个复杂任务后
「把这个工作流保存为技能」

# 2. 或手动创建
mkdir -p ~/.hermes/skills/my-skill
# 编写 SKILL.md（YAML 元数据 + Markdown 正文）

# 3. 重新加载
/reload-skills
```

**Skill 模板：**
```markdown
---
name: my-skill
description: "描述这个技能做什么"
version: 1.0.0
category: devops
---

# 技能名称

## 触发条件
- 用户提到 XXX 关键词时加载

## 步骤
1. 检查 XXX
2. 执行 YYY
3. 验证 ZZZ

## 注意事项
- 常见陷阱 A
- 平台差异 B
```

### 4.5 🔐 多 API Key 轮换

避免单个 Key 被限流：

```bash
hermes auth add    # 往池子里加 Key
hermes auth list   # 查看池子
# Agent 会自动在多个 Key 间轮换
```

### 4.6 📊 用量分析

```bash
hermes insights --days 30   # 30 天用量统计
/insights 7                  # 对话中查看
```

---

## 5. 配置速查

### 核心配置文件

| 文件 | 用途 |
|------|------|
| `~/.hermes/config.yaml` | 主配置 |
| `~/.hermes/.env` | API Key 和密钥 |

### 常用配置项

```bash
# 模型
hermes config set model.default "anthropic/claude-sonnet-4"

# Agent 行为
hermes config set agent.max_turns 90          # 最大工具调用轮次
hermes config set compression.enabled true    # 开启上下文压缩
hermes config set compression.threshold 0.5   # 压缩触发阈值

# 安全
hermes config set approvals.mode smart        # AI 判断风险
hermes config set security.redact_secrets true # 自动屏蔽密钥

# 显示
hermes config set display.show_cost true      # 显示费用
hermes config set display.show_reasoning true # 显示推理过程
hermes config set display.skin "dark"         # 暗色主题

# 委派
hermes config set delegation.max_iterations 50
hermes config set delegation.max_concurrent_children 3
```

### 环境变量速查

| 变量 | 用途 |
|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `GOOGLE_API_KEY` | Google Gemini |
| `XAI_API_KEY` | xAI (Grok) |
| `GROQ_API_KEY` | Groq 快速推理 |
| `HF_TOKEN` | Hugging Face |
| `GLM_API_KEY` | 智谱 GLM |
| `KIMI_API_KEY` | Moonshot/Kimi |
| `DASHSCOPE_API_KEY` | 阿里通义 |
| `GITHUB_TOKEN` | GitHub API |
| `HERMES_YOLO_MODE=1` | 跳过审批 |
| `HERMES_TUI=1` | 启用 TUI 模式 |

---

## 6. 命令速查表

### 会话控制

| 命令 | 作用 |
|------|------|
| `/new` | 新会话 |
| `/resume [name]` | 恢复会话 |
| `/title <name>` | 命名会话 |
| `/compress` | 手动压缩上下文 |
| `/rollback [N]` | 回滚文件变更 |
| `/undo` | 撤销上轮对话 |
| `/retry` | 重发最后一条消息 |
| `/background <prompt>` | 后台执行 |
| `/steer <prompt>` | 工具执行后注入 |

### 工具与技能

| 命令 | 作用 |
|------|------|
| `/tools` | 管理工具开关 |
| `/skill <name>` | 加载技能 |
| `/yolo` | 跳过本次确认 |
| `/browser` | 打开浏览器 |
| `/image <path>` | 上传图片 |

### 模型与配置

| 命令 | 作用 |
|------|------|
| `/model [name]` | 切换模型 |
| `/config` | 查看配置 |
| `/reasoning [level]` | 推理深度 |
| `/verbose` | 详细输出 |
| `/voice [on\|off]` | 语音模式 |
| `/usage` | Token 用量 |

### 查看与调试

| 命令 | 作用 |
|------|------|
| `/help` | 命令列表 |
| `/status` | 会话状态 |
| `/history` | 对话历史 |
| `/save` | 保存对话 |
| `/insights [N]` | 用量分析 |
| `/debug` | 上传调试报告 |
| `/quit` | 退出 |

### CLI 快速命令

```bash
hermes                                    # 进入对话
hermes chat -q "问题"                      # 单次提问
hermes chat -m "模型名" -q "问题"          # 指定模型
hermes --yolo -q "危险操作"                # 跳过确认
hermes -s skill1,skill2                    # 预加载技能
hermes --resume <session-id>               # 恢复会话
hermes --continue                          # 继续上次
```

---

## 附录

### 官方资源

| 资源 | 链接 |
|------|------|
| 官方文档 | https://hermes-agent.nousresearch.com/docs/ |
| GitHub | https://github.com/NousResearch/hermes-agent |
| 技能市场 | `hermes skills browse` |
| 问题反馈 | https://github.com/NousResearch/hermes-agent/issues |

### 版本信息

- 最新稳定版请查看 GitHub Releases
- 更新命令：`hermes update`

---

> 💡 **提示：** 这份绿皮书会持续更新。如果你发现了新的技巧或踩了坑，欢迎补充。
>
> 📧 作者：calumhuang@163.com
> 📅 更新：2026年5月
