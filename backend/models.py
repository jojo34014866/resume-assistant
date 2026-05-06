"""
数据模型 — 简历助手核心数据结构
适配移动端 API，所有字段有中文注释
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ─── 简历相关 ───────────────────────────────────────────

class ResumeSection(BaseModel):
    """简历的一个板块（工作经验、项目经历、教育等可复用的块）"""
    title: str = ""                    # 板块标题 如 "阿里巴巴 | 高级前端工程师"
    organization: str = ""            # 公司/学校/组织名称
    role: str = ""                    # 职位/角色
    start_date: str = ""             # 开始时间 如 "2022-03"
    end_date: str = ""               # 结束时间 如 "2024-06" 或 "至今"
    description: str = ""            # 工作内容/项目描述
    highlights: List[str] = []       # 关键成果/亮点
    skills_used: List[str] = []      # 用到的技能


class Resume(BaseModel):
    """结构化简历"""
    # 基本信息
    name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""                    # 所在城市
    title: str = ""                   # 当前/期望职位 如 "高级后端工程师"

    # 摘要
    summary: str = ""                 # 个人简介/自我评价

    # 技能
    hard_skills: List[str] = []       # 硬技能 Python, Docker, K8s...
    soft_skills: List[str] = []       # 软技能 沟通、项目管理...
    languages: List[str] = []         # 语言能力
    certificates: List[str] = []      # 证书/资质

    # 经历
    work_experience: List[ResumeSection] = []
    projects: List[ResumeSection] = []
    education: List[ResumeSection] = []

    # 元数据
    years_of_experience: float = 0.0  # 工作年限
    raw_text: str = ""                # 原始文本（用于 LLM 分析）


# ─── JD 相关 ────────────────────────────────────────────

class JDRequirement(BaseModel):
    """JD 中的一项要求"""
    category: str = ""                # 类别: hard_skill / soft_skill / experience / education / language / other
    content: str = ""                 # 具体要求文字
    required: bool = True            # 是否必须（False 为加分项）
    years: Optional[float] = None     # 要求年限（如有）


class JobDescription(BaseModel):
    """结构化岗位描述"""
    # 基本信息
    company: str = ""                 # 公司名
    title: str = ""                   # 岗位名称
    location: str = ""                # 工作地点
    salary_range: str = ""            # 薪资范围

    # 内容
    responsibilities: List[str] = []  # 岗位职责
    requirements: List[JDRequirement] = []  # 任职要求
    nice_to_have: List[str] = []      # 加分项
    benefits: List[str] = []          # 福利待遇

    # 元数据
    raw_text: str = ""                # JD 原始文本
    industry_tags: List[str] = []     # 行业标签


# ─── 匹配结果 ────────────────────────────────────────────

class MatchItem(BaseModel):
    """单个匹配项"""
    category: str = ""                # 类别
    jd_requirement: str = ""          # JD 要求
    resume_match: str = ""            # 简历中对应的内容
    match_level: str = "partial"     # full / partial / missing


class MatchResult(BaseModel):
    """匹配分析结果"""
    # 总体
    overall_score: int = 0            # 综合匹配分 0-100
    summary: str = ""                 # 总结文字

    # 详细
    matches: List[MatchItem] = []     # 匹配上的
    partial_matches: List[MatchItem] = []  # 部分匹配
    gaps: List[MatchItem] = []        # 缺失项

    # 亮点
    strengths: List[str] = []         # 你的优势
    weaknesses: List[str] = []        # 你的短板


class Greeting(BaseModel):
    """打招呼语"""
    platform: str = "default"         # boss / linkedin / lagou / default
    short: str = ""                   # 短版 50-100字 (BOSS直聘限制)
    full: str = ""                    # 完整版 200-400字
    key_points: List[str] = []        # 沟通中要突出的要点

    # 注意事项
    questions_to_ask: List[str] = []  # 建议向HR提问的问题
    risk_flags: List[str] = []        # 风险提示 (薪资不匹配、地点不明确等)
    preparation_tips: List[str] = []  # 面试准备建议


# ─── API 请求 / 响应 ───────────────────────────────────

class UploadResumeRequest(BaseModel):
    """上传简历请求"""
    format: str = "auto"              # pdf / word / md / txt / auto


class AnalyzeRequest(BaseModel):
    """分析请求"""
    resume_id: str = ""               # 已上传简历的ID（如支持多份）
    jd_text: str = ""                 # JD 文本
    platform: str = "default"         # 目标平台


class AnalyzeResponse(BaseModel):
    """分析响应"""
    job: JobDescription
    match: MatchResult
    greeting: Greeting
    resume_summary: str = ""          # 简历摘要


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: str = ""
