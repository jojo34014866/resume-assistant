"""
智能匹配引擎

将简历与 JD 做对比分析，输出：
 - 整体匹配分数
 - 逐项匹配/部分匹配/缺失
 - 优势与短板
 - 面试建议
"""

from typing import List, Dict, Tuple
import re


def match_resume_to_jd(resume: dict, jd: dict) -> dict:
    """
    主匹配函数

    Args:
        resume: parse_to_resume() 的输出字典
        jd:     parse_jd() 的输出字典

    Returns:
        MatchResult 对应的字典
    """
    matches = []
    partial = []
    gaps = []
    strengths = []
    weaknesses = []

    # 1. 逐项匹配任职要求
    for req in jd.get("requirements", []):
        match_item = _match_single_requirement(req, resume)
        if match_item["match_level"] == "full":
            matches.append(match_item)
        elif match_item["match_level"] == "partial":
            partial.append(match_item)
        else:
            gaps.append(match_item)

    # 2. 额外检查
    _check_experience_years(resume, jd, matches, partial, gaps)
    _check_education(resume, jd, matches, partial, gaps)
    _check_location(resume, jd, matches, partial, gaps)

    # 3. 加分项检查
    for item in jd.get("nice_to_have", []):
        match_item = _match_text_against_resume(item, resume, "nice_to_have")
        if match_item["match_level"] != "missing":
            strengths.append(f"加分项匹配: {item}")

    # 4. 计算分数
    total_items = len(matches) + len(partial) + len(gaps)
    if total_items == 0:
        score = 50  # 无法分析时给中间分
    else:
        score = int((len(matches) * 100 + len(partial) * 50) / total_items)

    # 5. 生成优势和短板
    if matches:
        strengths.append(f"匹配 {len(matches)} 项核心要求: " +
                        "、".join(m["jd_requirement"][:30] for m in matches[:5]))
    if gaps:
        weaknesses.append(f"缺失 {len(gaps)} 项要求: " +
                         "、".join(g["jd_requirement"][:30] for g in gaps[:5]))
    if partial:
        weaknesses.append(f"部分匹配 {len(partial)} 项，建议在简历中补充细节")

    # 年限
    jd_years = _extract_min_years(jd)
    resume_years = resume.get("years_of_experience", 0)
    if jd_years and resume_years < jd_years:
        weaknesses.append(f"工作年限: JD要求{jd_years}年，简历为{resume_years}年 — 可用项目经历弥补")

    # 6. 总结
    summary = _generate_summary(score, len(matches), len(partial), len(gaps),
                                 resume.get("title", ""), jd.get("title", ""))

    return {
        "overall_score": score,
        "summary": summary,
        "matches": matches,
        "partial_matches": partial,
        "gaps": gaps,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def _match_single_requirement(req: dict, resume: dict) -> dict:
    """匹配单条 JD 要求"""
    text = req.get("content", "")
    cat = req.get("category", "other")

    resume_match = ""
    level = "missing"

    if cat == "hard_skill":
        # 检查技能匹配
        skills = resume.get("hard_skills", [])
        matched_skills = _find_matching_skills(text, skills)
        if matched_skills:
            resume_match = "、".join(matched_skills)
            level = "full" if len(matched_skills) >= 1 else "partial"

    elif cat == "soft_skill":
        soft = resume.get("soft_skills", [])
        matched = [s for s in soft if s in text]
        if matched:
            resume_match = "、".join(matched)
            level = "full"

    elif cat == "language":
        langs = resume.get("languages", [])
        if langs:
            resume_match = "、".join(langs)
            level = "full"

    elif cat == "education":
        edu = resume.get("education", [])
        if edu:
            # 检查学历等级
            edu_text = " ".join(e.get("role", "") + e.get("description", "") for e in edu)
            edu_text += " " + resume.get("summary", "")
            resume_match = edu[0].get("role", "") if edu else ""
            if any(kw in edu_text for kw in ["本科", "硕士", "研究生", "博士", "MBA"]):
                level = "full"
            else:
                level = "partial"

    elif cat == "experience":
        years = req.get("years")
        if years:
            resume_years = resume.get("years_of_experience", 0)
            if resume_years >= years:
                resume_match = f"{resume_years}年经验"
                level = "full"
            elif resume_years >= years * 0.7:
                resume_match = f"{resume_years}年经验（接近JD要求的{years}年）"
                level = "partial"
            else:
                resume_match = f"仅有{resume_years}年经验"
                level = "missing"
        else:
            # 无具体年限，有工作经验就算匹配
            if resume.get("work_experience"):
                resume_match = "有相关工作经验"
                level = "full"
            else:
                level = "missing"

    else:
        # other — 文本模糊匹配
        match_result = _fuzzy_text_match(text, resume)
        resume_match = match_result[0]
        level = match_result[1]

    return {
        "category": cat,
        "jd_requirement": text,
        "resume_match": resume_match,
        "match_level": level,
    }


def _find_matching_skills(jd_text: str, resume_skills: List[str]) -> List[str]:
    """找出简历中有的、JD要求的技能（支持中英文同义词映射）"""
    matched = []
    jd_lower = jd_text.lower()

    # 同义词/相关词映射：JD 中文描述 → 简历可能的技能关键词
    synonym_map = {
        "计算机软硬件": ["Windows", "MacOS", "macOS", "Linux", "Windows Server",
                          "硬件故障", "硬件排错", "硬件维修", "电脑维修", "PC维修",
                          "桌面运维", "桌面支持", "IT 运维", "IT运维"],
        "软硬件故障": ["Windows", "MacOS", "macOS", "硬件故障", "硬件排错",
                        "桌面运维", "IT 运维", "IT运维"],
        "软硬件知识": ["Windows", "MacOS", "macOS", "硬件故障", "硬件排错"],
        "网络基础": ["TCP/IP", "DNS", "DHCP", "VPN", "LAN", "WAN", "VLAN",
                      "网络配置", "网络运维", "网络排错", "网络故障"],
        "网络设备": ["TCP/IP", "DNS", "DHCP", "VPN", "Cisco", "网络配置"],
        "helpdesk": ["Helpdesk", "Help Desk", "桌面运维", "桌面支持", "IT 运维",
                      "IT运维", "IT Support", "IT 支持", "服务台", "IT服务台"],
        "桌面运维": ["桌面运维", "桌面支持", "Helpdesk", "Help Desk", "IT 运维", "IT运维"],
        "打印机": ["打印机", "复印机", "硬件维修", "硬件故障"],
        "复印机": ["打印机", "复印机", "硬件维修"],
        "办公设备": ["打印机", "复印机", "硬件维修", "硬件故障", "IT 资产", "IT资产"],
        "办公软件": ["Office 365", "Microsoft 365", "OA", "OA系统"],
        "沟通能力": ["沟通", "团队协作"],
        "团队协作": ["沟通", "团队协作"],
        "抗压": ["抗压能力"],
        "ad": ["AD 域", "域控", "AD域控", "Active Directory"],
        "域控": ["AD 域", "域控", "AD域控", "Active Directory"],
    }

    # 先检查简历技能是否直接在 JD 中出现
    for skill in resume_skills:
        skill_lower = skill.lower()
        if skill_lower in jd_lower:
            matched.append(skill)
        else:
            # 别名匹配
            aliases = _get_skill_aliases(skill)
            for alias in aliases:
                if alias.lower() in jd_lower:
                    matched.append(skill)
                    break

    # 再检查 JD 中的中文描述是否通过同义词映射匹配到简历技能
    for jd_term, resume_keywords in synonym_map.items():
        if jd_term in jd_lower:
            for kw in resume_keywords:
                if kw in resume_skills and kw not in matched:
                    matched.append(kw)

    return matched


def _get_skill_aliases(skill: str) -> List[str]:
    """技能别名映射"""
    aliases_map = {
        "Kubernetes": ["K8s", "k8s", "K8S"],
        "JavaScript": ["JS", "js"],
        "TypeScript": ["TS", "ts"],
        "PostgreSQL": ["Postgres", "PG"],
        "Elasticsearch": ["ES", "Elastic"],
        "React Native": ["RN"],
        "机器学习": ["ML", "Machine Learning"],
        "深度学习": ["DL", "Deep Learning"],
        "自然语言处理": ["NLP"],
        "计算机视觉": ["CV", "Computer Vision"],
    }
    return aliases_map.get(skill, [])


def _fuzzy_text_match(jd_text: str, resume: dict) -> Tuple[str, str]:
    """
    模糊文本匹配：在简历的各段经历和摘要中搜索 JD 要求的关键词
    返回 (resume_match, level)
    """
    # 提取 JD 文本中的关键词
    keywords = _extract_keywords(jd_text)
    if not keywords:
        return "", "missing"

    # 在简历全文搜索
    resume_text = resume.get("raw_text", "")
    if not resume_text:
        resume_text = _build_resume_text(resume)

    resume_lower = resume_text.lower()
    matched = [kw for kw in keywords if kw.lower() in resume_lower]

    if len(matched) >= len(keywords) * 0.7:
        return f"简历涉及: {', '.join(matched[:5])}", "full"
    elif len(matched) >= len(keywords) * 0.3:
        return f"部分涉及: {', '.join(matched[:3])}", "partial"
    elif matched:
        return f"仅涉及: {', '.join(matched[:2])}", "partial"
    else:
        return "", "missing"


def _extract_keywords(text: str) -> List[str]:
    """从文本中提取实义词作为关键词"""
    # 去掉标点，取长度 >= 2 的中英文词
    cleaned = re.sub(r'[，,。\.；;：:！!\？\?\s\n\[\]【】()（）""''""《》<>]', ' ', text)
    words = cleaned.split()
    keywords = []
    stop_words = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那",
        "具有", "具备", "以上", "优先", "相关", "经验", "能力", "熟悉", "了解",
        "掌握", "负责", "能够", "具有", "良好", "一定", "以上学历",
        "以上", "以下", "以及", "及", "等", "包括", "例如", "比如",
        "the", "a", "an", "is", "are", "be", "to", "of", "in", "for",
        "and", "or", "with", "on", "at", "as", "by", "from", "can", "will",
        "must", "should", "experience", "years", "skills", "ability", "knowledge",
        "plus", "preferred", "familiar", "proficient", "strong", "good",
        "excellent", "relevant",
    }

    for w in words:
        w_clean = w.strip(",.;:!?()[]{}'\"")
        if len(w_clean) >= 2 and w_clean.lower() not in stop_words:
            keywords.append(w_clean)

    return list(dict.fromkeys(keywords))[:15]


def _build_resume_text(resume: dict) -> str:
    """从结构化的简历重建文本"""
    parts = []
    parts.append(resume.get("summary", ""))
    parts.append(" ".join(resume.get("hard_skills", [])))
    for exp in resume.get("work_experience", []):
        parts.append(exp.get("description", ""))
    for proj in resume.get("projects", []):
        parts.append(proj.get("description", ""))
    return "\n".join(parts)


def _match_text_against_resume(text: str, resume: dict, category: str) -> dict:
    """检查一段文本在简历中的匹配"""
    resume_text = resume.get("raw_text", "") or _build_resume_text(resume)
    match, level = _fuzzy_text_match(text, {"raw_text": resume_text})
    return {
        "category": category,
        "jd_requirement": text,
        "resume_match": match,
        "match_level": level if match else "missing",
    }


def _check_experience_years(resume: dict, jd: dict,
                             matches: list, partial: list, gaps: list):
    """检查工作年限是否已覆盖"""
    # 已在 _match_single_requirement 中处理，这里是补充检查
    jd_years = _extract_min_years(jd)
    if jd_years:
        existing = [m for m in matches if m["category"] == "experience"]
        if not existing:
            resume_years = resume.get("years_of_experience", 0)
            item = {
                "category": "experience",
                "jd_requirement": f"{jd_years}年以上工作经验",
                "resume_match": f"{resume_years}年经验" if resume_years else "未检测到工作经历",
                "match_level": "full" if resume_years >= jd_years else
                               "partial" if resume_years >= jd_years * 0.7 else "missing",
            }
            (matches if item["match_level"] == "full"
             else partial if item["match_level"] == "partial"
             else gaps).append(item)


def _check_education(resume: dict, jd: dict,
                     matches: list, partial: list, gaps: list):
    """检查学历要求"""
    edu_items = [r for r in jd.get("requirements", []) if r["category"] == "education"]
    if not edu_items:
        return  # JD 没写学历要求

    resume_edu = resume.get("education", [])
    if not resume_edu:
        gaps.append({
            "category": "education",
            "jd_requirement": "学历要求",
            "resume_match": "简历未检测到教育背景",
            "match_level": "missing",
        })


def _check_location(resume: dict, jd: dict,
                    matches: list, partial: list, gaps: list):
    """检查工作地点匹配"""
    jd_loc = jd.get("location", "")
    resume_city = resume.get("city", "")
    if jd_loc and resume_city:
        if resume_city in jd_loc or jd_loc in resume_city:
            matches.append({
                "category": "location",
                "jd_requirement": f"工作地点: {jd_loc}",
                "resume_match": f"所在城市: {resume_city}",
                "match_level": "full",
            })
        else:
            partial.append({
                "category": "location",
                "jd_requirement": f"工作地点: {jd_loc}",
                "resume_match": f"所在城市: {resume_city} — 可能需要relocate",
                "match_level": "partial",
            })


def _extract_min_years(jd: dict) -> float:
    """从 JD 中提取最低年限要求"""
    min_years = None
    for req in jd.get("requirements", []):
        y = req.get("years")
        if y is not None:
            if min_years is None or y < min_years:
                min_years = y
    return min_years


def _generate_summary(score: int, n_match: int, n_partial: int, n_gap: int,
                       resume_title: str, jd_title: str) -> str:
    """生成匹配总结"""
    if score >= 80:
        level = "高匹配度"
        advice = "你的背景与该岗位高度契合，建议投递并重点突出匹配项。"
    elif score >= 60:
        level = "中等匹配"
        advice = "有一定匹配度，但存在差距。建议在沟通中强调可迁移技能和学习能力。"
    elif score >= 40:
        level = "较低匹配"
        advice = "与该岗位要求差距较大。如果确实感兴趣，需要在打招呼中说明你对该领域的热情和快速学习能力。"
    else:
        level = "低匹配度"
        advice = "背景与该岗位不太匹配，建议寻找更适合的方向，或大幅调整简历。"

    return f"[{level}] 综合匹配度 {score}%。共 {n_match+n_partial+n_gap} 项要求：完全匹配 {n_match} 项，部分匹配 {n_partial} 项，缺失 {n_gap} 项。{advice}"
