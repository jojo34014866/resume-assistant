"""
招呼语生成 & 建议模块

根据匹配结果生成不同平台风格的打招呼语、
建议向 HR 提问的问题、风险提示、面试准备建议
"""

import re
from typing import List, Dict


def generate_greeting(resume: dict, jd: dict, match: dict,
                       platform: str = "default") -> dict:
    """
    生成招呼语和全套建议

    Args:
        resume:   结构化简历 dict
        jd:      结构化 JD dict
        match:   match_resume_to_jd() 的输出
        platform: boss / linkedin / lagou / default

    Returns:
        Greeting 对应的字典
    """
    company = jd.get("company", "") or "贵公司"
    job_title = jd.get("title", "") or "该岗位"
    resume_title = resume.get("title", "") or "求职者"
    resume_years = resume.get("years_of_experience", 0)
    resume_name = resume.get("name", "") or "我"

    score = match.get("overall_score", 50)
    strengths_list = match.get("strengths", [])
    weaknesses_list = match.get("weaknesses", [])
    match_items = match.get("matches", [])
    gap_items = match.get("gaps", [])

    # 提取3个最匹配的技能/经验作为招呼语卖点
    top_matches = _get_top_matches(match_items, 3)

    # 1. 生成短版（BOSS直聘风格，约 100 字）
    short = _gen_short_greeting(
        company, job_title, resume_title, resume_years, resume_name,
        top_matches, gap_items, platform, score
    )

    # 2. 生成完整版（200-400 字）
    full = _gen_full_greeting(
        company, job_title, resume_title, resume_years, resume_name,
        top_matches, gap_items, match_items, platform, score
    )

    # 3. 沟通要点
    key_points = _gen_key_points(resume, jd, match)

    # 4. 建议提问
    questions = _gen_questions(jd, match)

    # 5. 风险提示
    risks = _gen_risk_flags(resume, jd, match)

    # 6. 面试准备建议
    prep_tips = _gen_prep_tips(resume, jd, match)

    return {
        "platform": platform,
        "short": short,
        "full": full,
        "key_points": key_points,
        "questions_to_ask": questions,
        "risk_flags": risks,
        "preparation_tips": prep_tips,
    }


def _get_top_matches(match_items: list, n: int) -> list:
    """取 top N 个完全匹配项"""
    return [m for m in match_items if m.get("match_level") == "full"][:n]


def _gen_short_greeting(company: str, job_title: str, resume_title: str,
                         resume_years: float, resume_name: str,
                         top_matches: list, gap_items: list,
                         platform: str, score: int) -> str:
    """生成短版招呼语（BOSS直聘限制约 100 字符）"""

    # 清理 job_title：去掉噪声、截断
    clean_title = job_title.replace("。", " ").replace("；", " ").strip()
    # 如果标题太长或含无关内容，取前8个字
    if len(clean_title) > 20 or re.search(r'[，,;；\d]', clean_title):
        clean_title = clean_title[:15].rstrip("，,;；。. ") or "该岗位"

    # 根据匹配度调整语气
    if score >= 80:
        tone = "自信直接"
    elif score >= 60:
        tone = "诚恳积极"
    else:
        tone = "跨领域尝试"

    parts = []

    # 开头
    parts.append(f"您好，看到贵公司正在招聘{job_title}，我很感兴趣。")

    # 核心卖点
    if top_matches:
        match_str = "、".join(m["jd_requirement"][:15] for m in top_matches[:2])
        parts[-1] += f"我在{match_str}方面有{resume_years}年经验，" if resume_years else f"我在{match_str}方面经验丰富，"

    # 结尾
    parts.append("期待能有机会进一步沟通，谢谢！")

    greeting = "".join(parts)

    if platform == "boss":
        # BOSS直聘严格字数限制，裁到 ~100 字
        if len(greeting) > 120:
            greeting = greeting[:117] + "..."
    return greeting


def _gen_full_greeting(company: str, job_title: str, resume_title: str,
                        resume_years: float, resume_name: str,
                        top_matches: list, gap_items: list, match_items: list,
                        platform: str, score: int) -> str:
    """生成完整版招呼语"""

    parts = []
    parts.append(f"{company}的招聘负责人您好，\n")

    # 自我介绍
    parts.append(f"我是{resume_title}，有{resume_years}年相关工作经验。")
    parts.append(f"看到贵公司正在招聘「{job_title}」，仔细阅读JD后认为我的背景比较匹配，特来自荐。\n")

    # 匹配亮点
    if match_items:
        parts.append("【我与岗位的匹配点】")
        for i, m in enumerate(match_items[:5], 1):
            parts.append(f"{i}. {m.get('jd_requirement', '')} — {m.get('resume_match', '')}")
        parts.append("")

    # 如果匹配度不高，加一段说明
    if score < 60 and gap_items:
        parts.append("【坦诚说明】")
        gaps_text = "、".join(g["jd_requirement"][:25] for g in gap_items[:3])
        parts.append(f"我注意到JD中要求{gaps_text}，这些方面我目前不完全符合。但我有较强的学习能力，可以在入职前快速补足。")
        parts.append("")

    # 结尾
    parts.append("我的简历已附上，方便的话可以进一步沟通。期待您的回复！")
    parts.append(f"— {resume_name}")

    return "\n".join(parts)


def _gen_key_points(resume: dict, jd: dict, match: dict) -> List[str]:
    """生成沟通中要突出的要点"""
    points = []

    # 匹配上的技能
    for m in match.get("matches", [])[:5]:
        rd = m.get("resume_match", "")
        if rd:
            points.append(f"强调: {rd}")

    # 如果有项目经历匹配
    projects = resume.get("projects", [])
    if projects:
        points.append(f"可详述 {len(projects)} 个项目经历来证明能力")

    # 如果有匹配加分项
    for s in match.get("strengths", []):
        if "加分" in s:
            points.append(s)

    return points if points else ["准备好介绍你最相关的项目经历"]


def _gen_questions(jd: dict, match: dict) -> List[str]:
    """生成建议向 HR 提问的问题"""
    questions = []

    company = jd.get("company", "")
    title = jd.get("title", "")

    # 基础问题
    questions.append(f"这个岗位的团队规模和发展方向是怎样的？")

    # 根据 JD 缺失信息提问
    if not jd.get("salary_range"):
        questions.append("薪资范围大概是什么水平？")

    if not jd.get("location") or len(jd.get("location", "")) < 2:
        questions.append("工作地点在哪个城市/区域？")

    # 如果有要求但可能不明确的
    gaps = match.get("gaps", [])
    if gaps:
        gap_desc = gaps[0].get("jd_requirement", "")[:20]
        questions.append(f"关于「{gap_desc}」这项要求，是否有培训或学习期？")

    # 福利相关
    benefits = jd.get("benefits", [])
    if not benefits:
        questions.append("公司的福利待遇（社保公积金缴纳比例、年终奖、假期等）是怎样的？")

    return questions


def _gen_risk_flags(resume: dict, jd: dict, match: dict) -> List[str]:
    """根据实际匹配结果生成精准的注意事项"""
    risks = []

    gaps = match.get("gaps", [])
    partial = match.get("partial_matches", [])
    matches = match.get("matches", [])
    score = match.get("overall_score", 0)

    resume_city = resume.get("city", "")
    jd_city = jd.get("location", "")
    resume_years = resume.get("years_of_experience", 0)

    # 1. 硬性门槛：年限不足
    for g in gaps:
        if g.get("category") == "experience":
            jd_years = _extract_years_from_text(g.get("jd_requirement", ""))
            if jd_years and resume_years < jd_years:
                risks.append(f"工作年限不足：JD 要求约{jd_years}年经验，你的简历显示约{resume_years}年。可用项目经历和成果量化数据来弥补年限差距。")
            else:
                risks.append(f"经验匹配待确认：{g.get('jd_requirement','')[:40]}。建议在招呼语中主动提及相关经历。")

    # 2. 学历
    for g in gaps:
        if g.get("category") == "education":
            risks.append(f"学历要求：{g.get('jd_requirement','')[:40]}。若学历不完全符合，可通过突出实战经验和技术深度来弥补。")

    # 3. 关键技能缺失（从缺失项中提取技能类）
    skill_gaps = [g for g in gaps if g.get("category") == "hard_skill"]
    if skill_gaps:
        names = "、".join(g["jd_requirement"][:25] for g in skill_gaps[:3])
        risks.append(f"缺失关键技术栈：{names}。若你实际有但简历未体现，请补充；若确实不会，建议在面试前快速了解基础概念。")

    # 4. 语言能力
    lang_gaps = [g for g in gaps if g.get("category") == "language"]
    if lang_gaps:
        risks.append(f"语言要求不匹配：{' '.join(g['jd_requirement'][:30] for g in lang_gaps[:2])}")

    # 5. 地点
    if resume_city and jd_city and resume_city not in jd_city and jd_city not in resume_city:
        risks.append(f"城市不匹配：你在「{resume_city}」，岗位在「{jd_city}」。投递前务必确认是否接受异地办公或能否 relocate。")

    # 6. 匹配分过低
    if score < 50:
        n_gaps = len(gaps)
        risks.append(f"整体匹配度偏低（{score}%），有 {n_gaps} 项要求未达标。如果不是十分心仪的岗位，建议优先投匹配度更高的职位以提高成功率。")

    # 7. 薪资未标注
    if not jd.get("salary_range") or len(jd.get("salary_range", "")) < 3:
        risks.append("JD 未标注薪资范围。建议在初步沟通时尽早确认薪资预算，避免双方投入时间后发现差距过大。")

    # 8. 公司信息缺失
    if not jd.get("company"):
        risks.append("未识别到公司名称。沟通前建议先确认对方公司信息，了解基本业务和规模。")

    # 9. 部分匹配项提醒
    if partial:
        p_names = "、".join(p["jd_requirement"][:25] for p in partial[:2])
        risks.append(f"部分匹配需加强：{p_names}。建议在简历中补充相关细节，将部分匹配变为完全匹配。")

    return risks if risks else ["暂无明显风险点，你的背景与该岗位匹配度较好。"]


def _extract_years_from_text(text: str) -> float:
    """从文本中提取年限数字"""
    import re
    m = re.search(r'(\d+)', text)
    return float(m.group(1)) if m else 0


def _gen_prep_tips(resume: dict, jd: dict, match: dict) -> List[str]:
    """面试准备建议"""
    tips = []

    gaps = match.get("gaps", [])
    partial = match.get("partial_matches", [])

    # 1. 针对缺失项准备
    if gaps:
        gap_texts = [g["jd_requirement"][:30] for g in gaps[:3]]
        tips.append(f"准备如何回应关于「{'」「'.join(gap_texts)}」的问题：可以说你正在自学，并举例说明学习能力")

    # 2. 针对部分匹配项加强
    if partial:
        p_texts = [p["jd_requirement"][:30] for p in partial[:2]]
        tips.append(f"加强「{'」「'.join(p_texts)}」相关的准备，面试时准备具体案例")

    # 3. 项目经历准备
    projects = resume.get("projects", [])
    if projects:
        tips.append(f"准备 {len(projects)} 个项目的 STAR 描述（情境-任务-行动-结果）")

    # 4. 常见面试问题
    tips.append("准备回答: 「为什么选择我们公司？」— 结合JD中的业务方向说")
    tips.append("准备回答: 「你未来3年的职业规划？」— 与岗位发展方向对齐")

    # 5. 行业相关
    industry = jd.get("industry_tags", [])
    if industry and industry[0] != "通用":
        tips.append(f"了解{industry[0]}行业最新动态，面试时展现行业认知")

    return tips
