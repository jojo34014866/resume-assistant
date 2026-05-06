#!/bin/bash
# Quick test for resume assistant
API=http://localhost:8000

# JD with both 岗位职责 and 任职要求 sections
JD='【岗位】高级后端工程师
【公司】某知名科技公司
【地点】北京
【薪资】30K-50K·16薪
【岗位职责】
1. 负责公司核心业务系统的架构设计和技术方案落地
2. 参与微服务架构改造，提升系统性能和可维护性
3. 设计和优化数据库结构，保障数据一致性
【任职要求】
1. 5年以上后端开发经验，有大型互联网项目背景
2. 精通Go或Java，熟悉Python，有微服务实际落地经验
3. 深入理解MySQL、Redis等常见数据库和缓存技术
4. 熟悉Docker/Kubernetes等容器化技术
5. 本科及以上学历，计算机相关专业
【加分项】
• 有电商/交易系统经验优先
• 有技术团队管理经验'

RESUME='张三 | 高级后端工程师 | 5年经验 | 北京
个人技能: Python, Go, Django, FastAPI, Docker, Kubernetes, MySQL, Redis, Kafka, Git, Linux
工作经历:
2020-2024 阿里巴巴 | 高级后端工程师
• 负责电商核心交易系统的架构设计与开发，日均处理订单量100万+
• 主导微服务拆分项目，将单体应用拆分为12个独立服务，系统可用性从99.5%提升到99.95%
2018-2020 字节跳动 | 后端开发工程师
• 参与广告投放系统的开发，负责投放策略引擎的后端实现
教育: 2014-2018 清华大学 | 计算机科学 | 本科
语言: 英语 CET-6
自我评价: 5年后端开发经验，擅长高并发系统设计和微服务架构'

sleep 2
curl -s -X POST "$API/api/analyze-once" \
  --data-urlencode "resume_text=$RESUME" \
  --data-urlencode "jd_text=$JD" \
  --data-urlencode "platform=boss" | python3 -c "
import sys, json
d = json.load(sys.stdin)
j = d['job']
m = d['match']
g = d['greeting']
print('=== JD ===')
print(f'公司: {j[\"company\"]}')
print(f'职位: {j[\"title\"]}')
print(f'地点: {j[\"location\"]}')
print(f'薪资: {j[\"salary_range\"]}')
print(f'职责({len(j[\"responsibilities\"])}项):')
for r in j['responsibilities']:
    print(f'  - {r[:60]}')
print(f'要求({len(j[\"requirements\"])}项):')
for r in j['requirements']:
    print(f'  [{r[\"category\"]}] {r[\"content\"][:60]}')
print(f'加分({len(j[\"nice_to_have\"])}项):')
for n in j['nice_to_have']:
    print(f'  - {n}')
print()
print('=== 匹配 ===')
print(f'分数: {m[\"overall_score\"]}')
print(f'匹配: {len(m[\"matches\"])} 部分: {len(m[\"partial_matches\"])} 缺失: {len(m[\"gaps\"])}')
for i in m['matches']:
    print(f'  ✓ {i[\"jd_requirement\"][:50]}')
for i in m['gaps']:
    print(f'  ✗ {i[\"jd_requirement\"][:50]}')
print(f'优势: {m[\"strengths\"]}')
print(f'短板: {m[\"weaknesses\"]}')
print()
print('=== 招呼语 ===')
print(f'短版({len(g[\"short\"])}字): {g[\"short\"]}')
print(f'风险: {g[\"risk_flags\"]}')
"
