"""
岗位描述 (JD) 分析器
从 JD 文本中提取结构化信息 + 行业/技能识别
"""

import re
from typing import List, Tuple


def parse_jd(jd_text: str) -> dict:
    """
    解析 JD 文本，返回结构化 dict

    返回字段: company, title, location, salary_range,
              responsibilities, requirements, nice_to_have, benefits,
              industry_tags, raw_text
    """
    result = {
        "company": "",
        "title": "",
        "location": "",
        "salary_range": "",
        "responsibilities": [],
        "requirements": [],
        "nice_to_have": [],
        "benefits": [],
        "industry_tags": [],
        "raw_text": jd_text,
    }

    lines = jd_text.strip().split("\n")

    # 1. 公司名、职位名 — 通常在最前面
    result["company"] = _extract_company(jd_text)
    result["title"] = _extract_job_title(jd_text)
    result["location"] = _extract_location(jd_text)
    result["salary_range"] = _extract_salary(jd_text)

    # 2. 分板块
    sections = _split_jd_sections(jd_text)

    # 3. 解析各板块
    result["responsibilities"] = _extract_list_items(
        sections.get("responsibility", "") or sections.get("_first_block", "")
    )

    result["requirements"] = _extract_requirements(
        sections.get("requirement", "") or ""
    )

    result["nice_to_have"] = _extract_list_items(
        sections.get("nice_to_have", "") or ""
    )

    result["benefits"] = _extract_list_items(
        sections.get("benefit", "") or ""
    )

    # 4. 行业标签
    result["industry_tags"] = _detect_industry(jd_text)

    return result


def _extract_company(text: str) -> str:
    """提取公司名"""
    patterns = [
        r'【?\s*公司\s*】?\s*[：:]?\s*(.+?)(?:[，,。\n]|$)',
        r'关于(.+?)(?:[，,。\n]|$)',
        r'^(.+?)(?:招聘|诚聘|急聘|高薪|直招)',
        r'(.+?)热招',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip()
            if len(name) >= 2 and len(name) <= 30:
                return name
    return ""


def _extract_job_title(text: str) -> str:
    """提取岗位名称"""
    # 预处理：去掉 【岗位】 【职位】 等标签（冒号可选）
    cleaned = re.sub(r'【?\s*(?:岗位|职位)(?:名称)?\s*】?\s*[：:]?\s*', '', text)

    # 先去噪声行
    lines = cleaned.strip().split("\n")
    title_candidates = []
    for line in lines:
        line = line.strip()
        # 跳过纯符号、纯英文噪声、太长的行、含句号的行（描述文本不是标题）
        if re.match(r'^[A-Z\s:]+$', line) and len(line) > 5:
            continue
        if len(line) > 25 or "。" in line or "；" in line:
            continue
        if line:
            title_candidates.append(line)

    # 优先匹配含职位关键词的行（必须是标准职位名格式）
    patterns = [
        # 标准职位名模式：XX工程师、XX运维、IT Support 等
        r'(?:招聘|诚聘|急聘)?\s*(.+?(?:工程师|经理|主管|专员|总监|设计师|分析师|架构师|顾问|助理|IT Support|IT 支持|桌面运维工程师?|运维工程师?))',
    ]
    for pat in patterns:
        for line in title_candidates:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                if len(title) >= 2 and len(title) <= 40:
                    return title

    # 取第一行有效内容（必须包含职位关键词才要）
    if title_candidates:
        for line in title_candidates:
            first = re.sub(r'【.*?】', '', line).strip()
            # 必须有职位含义的词
            if re.search(r'(工程师|经理|主管|专员|总监|运维|支持|开发|设计|分析|测试|运营|助理|顾问|代表)',
                        first) and len(first) <= 40:
                return first
        # 实在没有，用第一行截断
        first = re.sub(r'【.*?】', '', title_candidates[0]).strip()
        return first[:30]

    return ""


def _extract_location(text: str) -> str:
    """提取工作地点"""
    cities = [
        "北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "武汉",
        "西安", "重庆", "苏州", "天津", "长沙", "郑州", "东莞", "青岛",
        "沈阳", "宁波", "昆明", "大连", "厦门", "合肥", "佛山", "福州",
        "哈尔滨", "济南", "温州", "长春", "石家庄", "常州", "泉州", "南宁",
        "贵阳", "南昌", "太原", "烟台", "嘉兴", "南通", "金华", "珠海",
        "惠州", "徐汇", "静安", "浦东", "朝阳", "海淀", "南山", "福田",
        "天河", "余杭", "滨江", "高新", "武侯", "锦江",
    ]
    found = []
    for city in cities:
        if city in text:
            # 检查上下文
            for m in re.finditer(city, text):
                ctx = text[max(0, m.start()-20):m.end()+10]
                if any(kw in ctx for kw in ["地点", "工作", "地址", "base", "办公", "城市"]):
                    found.append(city)
                    break
    if not found:
        # 回退：找第一个出现的大城市
        for city in cities[:20]:
            if city in text:
                return city
    return " · ".join(found) if found else ""


def _extract_salary(text: str) -> str:
    """提取薪资范围"""
    patterns = [
        r'(?:薪资|薪酬|工资|待遇)[：:]\s*(.+?)(?:[，,。\n]|$)',
        r'(\d+[kK千]-?\d*[kK千](?:/月)?)',
        r'(\d+k?\s*[-–—至]\s*\d+k?)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _split_jd_sections(text: str) -> dict:
    """将 JD 文本切分板块（容忍 OCR 噪声）"""
    # 清理明显的 OCR 噪声行
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过纯噪声行：全是大写英文无意义的、全是符号的
        if re.match(r'^[A-Z\s:]+$', stripped) and len(stripped) > 5 and not any(
            kw in stripped.lower() for kw in ['it', 'pc', 'oa', 'help', 'desk', 'sla']):
            continue
        # 跳过纯符号行
        if re.match(r'^[\s,;:]+$', stripped):
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines)

    section_map = {
        "responsibility": [
            r'【?\s*(?:岗位|工作)\s*(?:职责|内容|描述|说明)\s*】?',
            r'(?:工作)(?:范围|任务)',
            r'(?:你的?|您)?(?:需要做|工作内容|负责)',
        ],
        "requirement": [
            r'【?\s*(?:任职|岗位|职位|招聘|我们)\s*(?:要求|资格|条件|门槛)\s*】?[;；:：]?',
            r'(?:我们)(?:希望(?:你|您))',
            r'(?:需要(?:你|您))',
            r'(?:必备|必须)(?:条件|技能|要求)',
        ],
        "nice_to_have": [
            r'【?\s*加分\s*(?:项|条件|要求)?\s*】?',
            r'(?:优先|更好|额外)(?:项|条件|要求)?',
            r'(?:符合以下|以下)(?:条件|要求)?(?:优先|加分)',
        ],
        "benefit": [
            r'【?\s*(?:福利|薪资|待遇|我们提供|你将获得)\s*】?',
            r'(?:六险|五险|公积金|年终|股票|期权|假期)',
        ],
    }

    positions = []
    for section_name, patterns in section_map.items():
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                positions.append((m.start(), section_name))

    if not positions:
        return {"_first_block": text}

    positions.sort()
    sections = {}
    for i, (pos, name) in enumerate(positions):
        start = pos
        if i + 1 < len(positions):
            end = positions[i + 1][0]
        else:
            end = len(text)
        sections[name] = text[start:end].strip()

    # 第一个板块前的内容
    if positions and positions[0][0] > 10:
        prefix = text[:positions[0][0]].strip()
        if prefix:
            sections["_first_block"] = prefix

    return sections


def _extract_list_items(text: str) -> List[str]:
    """从文本中提取列表项（容忍 OCR 数字识别错误）"""
    items = []

    # 预处理：OCR 常把数字识别为相似汉字
    # "人、" → "1、"  "入、" → "1、"  "了、" → "3、" 等
    ocr_fixes = {
        "人、": "1、", "入、": "1、", "了、": "3、",
        "人.": "1.", "入.": "1.",
    }
    for wrong, right in ocr_fixes.items():
        text = text.replace(wrong, right)

    # 按编号/项目符号拆
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        # 匹配 1. 2) ① · - * 等开头（加 "人" 兼容 OCR 错误）
        m = re.match(r'^(?:\d+[\.\)、]\s*|[·•\-\*\+①②③④⑤⑥⑦⑧⑨⑩]\s*|[（(]\d+[）)]\s*)', line)
        if m:
            item = line[m.end():].strip()
            if len(item) > 2:
                items.append(item)

    # 如果没提取到，尝试按句子拆
    if not items:
        sentences = re.split(r'[。；;]', text)
        for s in sentences:
            s = s.strip()
            if 3 < len(s) < 200:
                items.append(s)

    return items


def _extract_requirements(text: str) -> List[dict]:
    """提取任职要求，分类"""
    items = _extract_list_items(text)
    if not items and text.strip():
        items = [text.strip()]

    requirements = []
    for item in items:
        cat, years = _classify_requirement(item)
        requirements.append({
            "category": cat,
            "content": item,
            "required": True,
            "years": years,
        })

    # 如果没有任何要求项（无编号列表的纯文本），把整个文本作为一项
    if not requirements and text.strip():
        requirements.append({
            "category": "other",
            "content": text.strip(),
            "required": True,
            "years": None,
        })

    return requirements


def _classify_requirement(text: str) -> Tuple[str, float]:
    """分类一条要求"""
    text_lower = text.lower()

    # 年限
    years = None
    year_m = re.search(r'(\d+)[-\s]*年(?:以上|经验|工作经验|相关经验)?', text)
    if year_m:
        try:
            years = float(year_m.group(1))
        except:
            pass

    # 分类
    if any(kw in text_lower for kw in ["本科", "硕士", "博士", "学历", "毕业", "学位",
                                         "985", "211", "全日制", "统招", "计算机相关",
                                         "计算机专业", "相关专业"]):
        return "education", years

    if any(kw in text_lower for kw in ["英语", "日语", "韩语", "外语", "CET", "雅思", "托福",
                                         "口语", "读写", "翻译"]):
        return "language", years

    if any(kw in text_lower for kw in ["沟通", "团队", "协作", "领导", "管理",
                                         "抗压", "责任", "主动", "学习能力", "逻辑",
                                         "表达", "执行", "学习甬力"]):
        return "soft_skill", years

    # 年限/经验类要在硬技能之前检查
    if any(kw in text_lower for kw in ["年以上", "年经验", "相关工作", "行业经验",
                                         "工作经验", "从业", "年限", "项目背景",
                                         "helpdesk", "桌面运维经验", "it 运维经验"]):
        return "experience", years

    if any(kw in text_lower for kw in ["python", "java", "javascript", "react", "vue",
                                         "golang", "docker", "kubernetes", "k8s", "sql",
                                         "aws", "azure", "linux", "git", "c++", "typescript",
                                         "spring", "django", "fastapi",
                                         "框架", "数据库", "前端", "后端", "全栈",
                                         # IT 运维相关
                                         "计算机软硬件", "软硬件", "硬件故障", "硬件排错",
                                         "网络基础", "网络设备", "网络配置",
                                         "桌面运维", "helpdesk", "help desk",
                                         "打印机", "复印机", "办公设备", "办公软件",
                                         "ad域", "域控", "active directory",
                                         "office 365", "windows", "macos",
                                         "tcp/ip", "dns", "dhcp", "vpn",
                                         "itil", "itsm", "itam",
                                         ]):
        return "hard_skill", years

    return "other", years


def _detect_industry(text: str) -> List[str]:
    """检测行业标签"""
    industries = {
        "互联网/科技": ["互联网", "科技", "软件", "SaaS", "IT", "信息", "数字化", "计算机"],
        "金融": ["金融", "银行", "证券", "保险", "基金", "投资", "支付", "信贷", "理财", "风控"],
        "电商": ["电商", "电子商务", "零售", "O2O", "新零售", "供应链"],
        "教育": ["教育", "培训", "在线教育", "K12", "知识付费"],
        "医疗/健康": ["医疗", "医药", "健康", "医院", "生物", "制药", "诊所", "体检"],
        "游戏": ["游戏", "手游", "页游", "电竞", "休闲游戏"],
        "AI/人工智能": ["AI", "人工智能", "深度学习", "机器学习", "大模型", "NLP", "CV", "LLM"],
        "汽车/出行": ["汽车", "新能源", "自动驾驶", "出行", "车联网", "智能驾驶"],
        "房产/建筑": ["房产", "地产", "建筑", "物业", "装修"],
        "广告/营销": ["广告", "营销", "传媒", "新媒体", "MCN", "短视频", "直播"],
        "企业服务": ["企业服务", "B2B", "ERP", "CRM", "协同办公"],
        "硬件/芯片": ["芯片", "半导体", "硬件", "IoT", "物联网", "嵌入式"],
        "物流/供应链": ["物流", "快递", "仓储", "运输", "供应链"],
        "区块链/Web3": ["区块链", "Web3", "加密货币", "DeFi", "NFT", "数字货币"],
    }

    tags = []
    for name, keywords in industries.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                tags.append(name)
                break
    return tags if tags else ["通用"]
