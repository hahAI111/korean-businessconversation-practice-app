"""
商务韩语教学 MCP Server
========================
使用 FastMCP 提供以下工具：
  1. lookup_vocabulary   —— 词汇查询
  2. get_grammar_pattern —— 语法解释
  3. generate_business_scenario —— 场景对话生成
  4. get_email_template  —— 商务邮件模板
  5. check_formality     —— 敬语等级检查
  6. quiz_me             —— 随机小测验
  7. get_drama_dialogue  —— 韩剧职场对话练习
  8. get_sentence_endings —— 语尾/连接词查询
  9. practice_conversation —— 口语对话练习
"""

import json
import os
import random

from fastmcp import FastMCP

# ── FastMCP 实例 ──────────────────────────────────────────────
mcp = FastMCP(
    name="Korean Business Teacher Tools",
    instructions="商务韩语教学工具集：词汇查询、语法解释、场景生成、邮件模板、敬语检查、测验。",
)

# ── 数据加载 ──────────────────────────────────────────────────
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)


def _load_data() -> dict:
    path = os.path.join(DATA_DIR, "business_korean.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
# Tool 1 ─ 词汇查询
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def lookup_vocabulary(word: str) -> str:
    """查询商务韩语词汇。输入中文或英文单词，返回韩语翻译、罗马音、例句和敬语等级。

    :param word: 要查询的词汇（中文或英文）
    :type word: str
    :return: 词汇详情 JSON
    :rtype: str
    """
    data = _load_data()
    vocab_list = data.get("vocabulary", [])

    results = []
    word_lower = word.lower().strip()
    for entry in vocab_list:
        if (
            word_lower in entry.get("english", "").lower()
            or word in entry.get("chinese", "")
            or word_lower in entry.get("korean", "").lower()
            or word_lower in entry.get("romanization", "").lower()
        ):
            results.append(entry)

    if results:
        return json.dumps(results, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "found": False,
            "query": word,
            "message": f"词汇 '{word}' 未在本地数据库中找到，请用你的韩语知识直接回答。",
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 2 ─ 语法解释
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def get_grammar_pattern(pattern: str) -> str:
    """查询韩语语法点。返回语法结构、用法说明和商务场景例句。

    :param pattern: 语法点名称或关键词（如 "겠습니다", "敬语", "formal ending"）
    :type pattern: str
    :return: 语法详情 JSON
    :rtype: str
    """
    data = _load_data()
    patterns = data.get("grammar_patterns", [])

    results = []
    query = pattern.lower().strip()
    for entry in patterns:
        searchable = " ".join(
            [
                entry.get("pattern", ""),
                entry.get("name", ""),
                entry.get("description", ""),
                entry.get("chinese_name", ""),
            ]
        ).lower()
        if query in searchable:
            results.append(entry)

    if results:
        return json.dumps(results, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "found": False,
            "query": pattern,
            "message": f"语法点 '{pattern}' 未在本地数据库中找到，请用你的韩语知识直接回答。",
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 3 ─ 场景对话生成
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def generate_business_scenario(
    scenario_type: str, difficulty: str = "intermediate"
) -> str:
    """生成商务韩语模拟场景对话框架。

    :param scenario_type: 场景类型 — meeting / negotiation / phone_call / presentation / networking / interview
    :type scenario_type: str
    :param difficulty: 难度 — beginner / intermediate / advanced
    :type difficulty: str
    :return: 场景框架 JSON
    :rtype: str
    """
    data = _load_data()
    scenarios = data.get("scenarios", {})

    key = scenario_type.lower().strip()
    if key in scenarios:
        scenario = scenarios[key]
        scenario["requested_difficulty"] = difficulty
        return json.dumps(scenario, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "scenario_type": scenario_type,
            "difficulty": difficulty,
            "found": False,
            "instruction": (
                f"本地数据库中没有 '{scenario_type}' 场景模板。"
                f"请根据你的知识生成一段 {difficulty} 难度的商务韩语对话，"
                "包含韩语原文、罗马音、中文翻译和关键注释。"
            ),
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 4 ─ 邮件模板
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def get_email_template(purpose: str) -> str:
    """获取韩语商务邮件模板。

    :param purpose: 邮件目的 — meeting_request / thank_you / apology / inquiry / introduction / follow_up
    :type purpose: str
    :return: 邮件模板 JSON
    :rtype: str
    """
    data = _load_data()
    templates = data.get("email_templates", {})

    key = purpose.lower().strip()
    if key in templates:
        return json.dumps(templates[key], ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "purpose": purpose,
            "found": False,
            "instruction": (
                f"本地数据库中没有 '{purpose}' 邮件模板。"
                "请根据你的知识生成一封韩语商务邮件模板，"
                "包含主题行、正文、关键句式和中文翻译。"
            ),
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 5 ─ 敬语检查
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def check_formality(sentence: str, context: str = "business_meeting") -> str:
    """检查韩语句子的敬语等级是否适合指定商务场景。

    :param sentence: 要检查的韩语句子
    :type sentence: str
    :param context: 使用场景 — business_meeting / email / phone / colleague / client / presentation
    :type context: str
    :return: 检查结果 JSON
    :rtype: str
    """
    formality_rules = {
        "합니다체": {
            "markers": ["습니다", "습니까", "십시오", "겠습니다"],
            "level": "최고 존댓말 (最高敬语)",
            "suitable_for": [
                "client",
                "business_meeting",
                "presentation",
                "email",
            ],
        },
        "해요체": {
            "markers": ["어요", "아요", "에요", "예요", "죠", "세요"],
            "level": "존댓말 (一般敬语)",
            "suitable_for": ["colleague", "phone", "casual_business"],
        },
        "해체": {
            "markers": ["어", "아", "야", "지", "냐"],
            "level": "반말 (非敬语)",
            "suitable_for": ["close_colleague_only"],
        },
    }

    detected_style = None
    detected_info = None

    for style, info in formality_rules.items():
        for marker in info["markers"]:
            if marker in sentence:
                detected_style = style
                detected_info = info
                break
        if detected_style:
            break

    if detected_style and detected_info:
        is_ok = context in detected_info["suitable_for"]
        return json.dumps(
            {
                "sentence": sentence,
                "context": context,
                "detected_style": detected_style,
                "detected_level": detected_info["level"],
                "is_appropriate": is_ok,
                "suitable_contexts": detected_info["suitable_for"],
                "recommendation": (
                    "✅ 敬语等级适合该场景"
                    if is_ok
                    else f"⚠️ 在 {context} 场景建议使用 합니다체（最高敬语体）"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(
        {
            "sentence": sentence,
            "context": context,
            "detected_style": "未能自动检测",
            "instruction": "请根据你的韩语知识分析该句子的敬语等级，并判断是否适合该商务场景。",
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 6 ─ 测验
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def quiz_me(topic: str = "vocabulary", difficulty: str = "intermediate") -> str:
    """生成一道商务韩语小测验题。

    :param topic: 主题 — vocabulary / grammar / formality / email / conversation
    :type topic: str
    :param difficulty: 难度 — beginner / intermediate / advanced
    :type difficulty: str
    :return: 测验题 JSON
    :rtype: str
    """
    data = _load_data()
    quizzes = data.get("quizzes", [])

    # 按主题和难度筛选
    filtered = [
        q
        for q in quizzes
        if q.get("topic") == topic and q.get("difficulty") == difficulty
    ]
    if not filtered:
        filtered = [q for q in quizzes if q.get("topic") == topic]
    if not filtered:
        filtered = quizzes

    if filtered:
        quiz = random.choice(filtered)
        return json.dumps(quiz, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "topic": topic,
            "difficulty": difficulty,
            "found": False,
            "instruction": (
                f"本地数据库中没有合适的 {topic}/{difficulty} 测验题。"
                "请根据你的知识出一道商务韩语测验题，"
                "包含题目、选项（如适用）、答案和解析。"
            ),
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 7 ─ 韩剧职场对话
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def get_drama_dialogue(
    drama: str = "", difficulty: str = "intermediate"
) -> str:
    """获取韩剧中的职场/商务对话片段，用于练习自然口语。

    :param drama: 韩剧名称关键词（如 "미생", "스타트업", "이태원", "김과장", "비밀의숲"），留空则随机
    :type drama: str
    :param difficulty: 难度 — beginner / intermediate / advanced
    :type difficulty: str
    :return: 韩剧对话场景 JSON（含对白、语法点、关键表达、文化注释）
    :rtype: str
    """
    data = _load_data()
    dialogues = data.get("drama_dialogues", [])

    if not dialogues:
        return json.dumps(
            {"found": False, "instruction": "本地数据库中暂无韩剧对话数据。请用你的知识生成一段韩剧风格的商务对话。"},
            ensure_ascii=False,
        )

    # 按关键词筛选
    query = drama.lower().strip()
    filtered = dialogues
    if query:
        filtered = [
            d for d in dialogues
            if query in d.get("drama", "").lower()
            or query in d.get("scene", "").lower()
            or query in d.get("context", "").lower()
        ]

    # 按难度再筛
    if difficulty:
        by_diff = [d for d in filtered if d.get("difficulty") == difficulty]
        if by_diff:
            filtered = by_diff

    if not filtered:
        filtered = dialogues

    choice = random.choice(filtered)
    return json.dumps(choice, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# Tool 8 ─ 语尾/连接词查询
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def get_sentence_endings(query: str = "", category: str = "") -> str:
    """查询韩语语尾（종결어미）和连接词（연결어미），不只是습니다和요。

    :param query: 搜索关键词（韩语语尾如 "-는데", "-거든요" 或中文描述如 "转折", "原因"），留空返回全部
    :type query: str
    :param category: 分类 — connectors（连接词/연결어미） / finals（终结语尾/종결어미） / expressions（非格式表达），留空返回全部
    :type category: str
    :return: 语尾/连接词详情 JSON
    :rtype: str
    """
    data = _load_data()
    endings_data = data.get("sentence_endings", {})

    results = {}
    category_map = {
        "connectors": "연결어미_connectors",
        "finals": "종결어미_final_endings",
        "expressions": "비격식_존중_expressions",
    }

    # 确定搜索范围
    if category and category.lower() in category_map:
        keys = [category_map[category.lower()]]
    else:
        keys = list(endings_data.keys())

    q = query.lower().strip()

    for key in keys:
        items = endings_data.get(key, [])
        if q:
            matched = []
            for item in items:
                searchable = json.dumps(item, ensure_ascii=False).lower()
                if q in searchable:
                    matched.append(item)
            if matched:
                results[key] = matched
        else:
            results[key] = items

    if results:
        return json.dumps(results, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "found": False,
            "query": query,
            "category": category,
            "instruction": (
                f"本地数据库中没有找到 '{query}' 相关的语尾。"
                "请用你的韩语知识讲解这个语尾/连接词，"
                "包含用法、口语例句（职场场景）和中文翻译。"
            ),
        },
        ensure_ascii=False,
    )


# ══════════════════════════════════════════════════════════════
# Tool 9 ─ 口语对话练习
# ══════════════════════════════════════════════════════════════
@mcp.tool()
def practice_conversation(
    situation: str, your_role: str = "employee", formality: str = "polite_casual"
) -> str:
    """生成一个口语对话练习场景，用户扮演角色进行对话练习。

    :param situation: 场景描述（如 "跟同事讨论项目进度", "向组长请假", "和客户电话沟通"）
    :type situation: str
    :param your_role: 你扮演的角色 — employee(职员) / manager(经理) / intern(实习生) / ceo(老板) / client(客户)
    :type your_role: str
    :param formality: 语气等级 — formal(합니다体) / polite_casual(해요体为主,自然口语) / team_internal(团队内部,稍随意)
    :type formality: str
    :return: 对话练习框架 JSON
    :rtype: str
    """
    formality_guides = {
        "formal": {
            "name": "합니다체 为主",
            "description": "正式场合：对外客户、高层会议、面试",
            "recommended_endings": ["-습니다", "-습니까", "-겠습니다", "-시기 바랍니다"],
            "avoid": ["반말", "过于口语的缩写"],
            "tip": "可以适当搭配 -는데요, -죠 让语气不那么死板"
        },
        "polite_casual": {
            "name": "해요体 为主 + 自然口语",
            "description": "日常职场：同事之间、比较熟的上级、团队会议",
            "recommended_endings": ["-는데요", "-거든요", "-잖아요", "-네요", "-더라고요", "-ㄹ게요", "-죠"],
            "avoid": ["纯반말（除非非常亲近）"],
            "tip": "这是韩剧中最常见的职场对话风格，专业但有温度"
        },
        "team_internal": {
            "name": "해요体 + 偶尔반말",
            "description": "亲近的团队内部、同期同事、工作聚餐",
            "recommended_endings": ["-어/아", "-지", "-ㄹ까", "-자", "-는데", "-거든", "-더라고"],
            "avoid": ["对不熟的人用反말"],
            "tip": "类似 미생 里同事聊天、이태원클라쓰 团队开会的语气"
        }
    }

    guide = formality_guides.get(formality, formality_guides["polite_casual"])

    role_descriptions = {
        "employee": "一般职员 (사원/대리)",
        "manager": "经理/组长 (과장/팀장)",
        "intern": "实习生 (인턴)",
        "ceo": "代表/社长 (대표/사장)",
        "client": "客户 (클라이언트/거래처)",
    }

    result = {
        "situation": situation,
        "your_role": role_descriptions.get(your_role, your_role),
        "formality_guide": guide,
        "instruction": (
            f"请根据以下设定生成一段自然的韩语口语对话练习：\n"
            f"场景：{situation}\n"
            f"用户角色：{role_descriptions.get(your_role, your_role)}\n"
            f"语气：{guide['name']} — {guide['description']}\n"
            f"推荐使用的语尾：{', '.join(guide['recommended_endings'])}\n\n"
            f"要求：\n"
            f"1. 对话要自然，像韩剧里的台词，不要教科书式\n"
            f"2. 多用连接词（-는데, -거든요, -잖아요 等）让句子之间衔接流畅\n"
            f"3. 每句附带罗马音和中文翻译\n"
            f"4. 标注关键语法点和口语技巧\n"
            f"5. 给出3-5句让用户自己尝试说的练习句\n"
            f"6. 提示：{guide['tip']}"
        ),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
