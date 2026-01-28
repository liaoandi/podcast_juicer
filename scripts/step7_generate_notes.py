#!/usr/bin/env python3
"""
生成投资研究笔记风格的信号报告
- 完整句子和段落
- 清晰的重点标记
- 适合人类阅读
"""

import json
import re
import sys
import os
from openai import AzureOpenAI
from google import genai
from google.genai import types

def get_sa_key_path():
    """从环境变量或 .env 获取 service account key 路径"""
    key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path and os.path.exists(key_path):
        return key_path

    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GOOGLE_APPLICATION_CREDENTIALS='):
                    key_path = line.split('=', 1)[1].strip()
                    if os.path.exists(key_path):
                        return key_path
    return None

def get_project_id():
    """获取 Google Cloud Project ID"""
    sa_key_path = get_sa_key_path()
    if sa_key_path and os.path.exists(sa_key_path):
        try:
            with open(sa_key_path, 'r') as f:
                data = json.load(f)
                project_id = data.get('project_id')
                if project_id:
                    return project_id
        except:
            pass

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id

    return None

def get_gemini_client():
    """获取 Gemini 客户端"""
    sa_key_path = get_sa_key_path()
    if sa_key_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path

    project_id = get_project_id()
    if not project_id:
        return None

    try:
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location="global"
        )
        return client
    except:
        return None

def get_openai_client():
    """获取 Azure OpenAI 客户端"""
    api_key = os.environ.get('AZURE_OPENAI_API_KEY')

    if not api_key:
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('AZURE_OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        return None

    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint="https://aigc-japan-east.openai.azure.com/",
        api_version="2025-04-01-preview",
        max_retries=1,
        timeout=30.0,
    )

def build_company_map(watchlist_file):
    """
    构建标准化公司信息映射表
    1. 硬编码常见公司的中英文映射
    2. 从 watchlist 读取所有公司
    3. 合并数据

    Returns:
        字典：{
            'search_name': {
                'cn': '中文名',
                'en': '英文简称',
                'ticker': 'TICKER',
                'display': '中文名（英文 $TICKER）'
            }
        }
    """
    # 常见公司的中英文映射表
    CN_EN_MAP = {
        'NVIDIA': '英伟达',
        'AMD': '超微半导体',
        'Intel': '英特尔',
        'Microsoft': '微软',
        'Apple': '苹果',
        'Google': '谷歌',
        'Alphabet': '谷歌',
        'Meta': 'Meta',
        'Amazon': '亚马逊',
        'Tesla': '特斯拉',
        'Oracle': '甲骨文',
        'Broadcom': '博通',
        'Qualcomm': '高通',
        'Alibaba': '阿里巴巴',
        'Tencent': '腾讯',
        'ByteDance': '字节跳动',
        'Baidu': '百度',
        'IBM': 'IBM',
        'Samsung': '三星',
        'TSMC': '台积电',
        'Huawei': '华为',
        'Xiaomi': '小米',
        'Netflix': '奈飞',
        'Uber': 'Uber',
        'Airbnb': 'Airbnb',
        'Snap': 'Snap',
        'Twitter': '推特',
        'X': 'X',
        'Pinterest': 'Pinterest',
        'Spotify': 'Spotify',
        'Zoom': 'Zoom',
        'Salesforce': 'Salesforce',
        'ServiceNow': 'ServiceNow',
        'Palantir': 'Palantir',
        'Snowflake': 'Snowflake',
        'Databricks': 'Databricks',
        'Stripe': 'Stripe',
        'SpaceX': 'SpaceX',
        'OpenAI': 'OpenAI',
        'Anthropic': 'Anthropic',
        'Mistral': 'Mistral',
        'Cohere': 'Cohere',
        'Stability AI': 'Stability AI',
        'Midjourney': 'Midjourney',
        'CoreWeave': 'CoreWeave',
        'Lambda Labs': 'Lambda Labs',
        'Together AI': 'Together AI',
        'Cerebras': 'Cerebras',
        'SambaNova': 'SambaNova',
        'Groq': 'Groq',
    }

    # 从 watchlist 读取公司信息
    companies_from_watchlist = {}
    if watchlist_file and os.path.exists(watchlist_file):
        try:
            with open(watchlist_file, 'r', encoding='utf-8') as f:
                watchlist = json.load(f)
                for company in watchlist.get('watchlist', []):
                    en_name = company.get('company', '').strip()
                    ticker = company.get('ticker')

                    # 处理 "Google / Alphabet" 这种格式
                    if '/' in en_name:
                        names = [n.strip() for n in en_name.split('/')]
                        main_name = names[0]
                    else:
                        main_name = en_name
                        names = [en_name]

                    # 查找中文名
                    cn_name = None
                    for name in names:
                        if name in CN_EN_MAP:
                            cn_name = CN_EN_MAP[name]
                            break

                    # 如果没有中文名，使用英文名
                    if not cn_name:
                        cn_name = main_name

                    companies_from_watchlist[main_name] = {
                        'cn': cn_name,
                        'en': main_name,
                        'ticker': ticker,
                        'aliases': names
                    }
        except Exception as e:
            print(f"⚠️ 加载 watchlist 失败: {e}")

    # 合并所有公司信息
    company_map = {}

    # 添加 watchlist 中的公司
    for en_name, info in companies_from_watchlist.items():
        cn_name = info['cn']
        ticker = info['ticker']

        # 生成标准显示格式
        if ticker:
            display = f"{cn_name}（{info['en']} ${ticker}）"
        else:
            display = f"{cn_name}（{info['en']}）"

        # 创建所有可能的搜索关键词
        search_keys = set([en_name, cn_name, info['en']])

        # 添加所有别名
        if 'aliases' in info:
            search_keys.update(info['aliases'])

        # 添加 ticker
        if ticker:
            search_keys.add(ticker)
            search_keys.add(f'${ticker}')

        # 添加小写版本（仅英文）
        for key in list(search_keys):
            if key and key[0].isascii():
                search_keys.add(key.lower())

        # 去重并存储
        for key in search_keys:
            if key:  # 跳过空字符串
                company_map[key] = {
                    'cn': cn_name,
                    'en': info['en'],
                    'ticker': ticker,
                    'display': display
                }

    return company_map

def build_ticker_map(watchlist_file):
    """
    保留原函数签名以兼容，实际调用 build_company_map
    """
    company_map = build_company_map(watchlist_file)
    # 转换为旧格式以保持兼容
    ticker_map = {}
    for key, info in company_map.items():
        if info['ticker']:
            ticker_map[key] = info['ticker']
    return ticker_map

def add_tickers_to_text(text, ticker_map=None):
    """
    统一规范化文本中的公司名称：中文名（英文 $TICKER）

    Args:
        text: 原始文本
        ticker_map: 兼容参数（已废弃）

    Returns:
        规范化后的文本
    """
    company_map = build_company_map(None)

    # 按搜索关键词长度排序（先替换长的，避免部分匹配）
    sorted_companies = sorted(company_map.items(), key=lambda x: -len(x[0]))

    # 记录已替换的位置，避免重复替换
    replaced_ranges = []

    for search_key, info in sorted_companies:
        display = info['display']

        # 跳过已经是标准格式的
        if display in text:
            continue

        # 匹配规则：
        # 1. 不在 $ 符号后（避免匹配 $AMD）
        # 2. 不在 word 字符中间（避免部分匹配）
        # 3. 后面没有已经添加的 ticker（避免重复）
        # 4. 匹配中英文边界
        pattern = rf'(?<!\$)(?<![a-zA-Z]){re.escape(search_key)}(?!\s*[（(][^）)]*\$[A-Z]+[）)])(?![a-zA-Z])'

        def replace_if_not_overlapping(match):
            # 检查是否与已替换范围重叠
            start, end = match.span()
            for r_start, r_end in replaced_ranges:
                if not (end <= r_start or start >= r_end):
                    return match.group(0)  # 重叠，不替换

            replaced_ranges.append((start, start + len(display)))
            return display

        text = re.sub(pattern, display, text)

    return text

def force_split_long_paragraphs(text, speaker, max_sentences=3):
    """
    强制拆分长段落：每 max_sentences 句话断开

    Args:
        text: 段落文本
        speaker: 说话人
        max_sentences: 每段最多句子数

    Returns:
        拆分后的段落列表
    """
    # 按句号拆分（保留句号）
    sentences = []
    current = ""
    for char in text:
        current += char
        if char == '。':
            sentences.append(current.strip())
            current = ""

    if current.strip():
        sentences.append(current.strip())

    # 按 max_sentences 分组
    result = []
    for i in range(0, len(sentences), max_sentences):
        chunk = ''.join(sentences[i:i+max_sentences])
        if chunk:
            result.append(f"**{speaker}**: {chunk}")

    return result

def generate_investment_strategy(signals, ticker_map=None):
    """
    使用 Gemini 3 Pro 分析所有信号，生成综合投资建议

    Args:
        signals: 所有信号列表
        ticker_map: 公司名到 ticker 的映射
    """
    client = get_gemini_client()
    if not client:
        return None

    # 整理信号完整信息（包含验证数据）
    signal_summaries = []
    for i, sig in enumerate(signals, 1):
        companies = ', '.join([e['name'] for e in sig.get('entities', [])][:3])
        claim = sig.get('claim', '')
        conf = sig.get('confidence', 'low')
        nov = sig.get('novelty', 'low')
        act = sig.get('actionability', 'low')

        summary = f"""
## 信号 {i}: {companies}
**原始判断**: {claim}
**三维度**: 置信度={conf} | 新颖度={nov} | 可行动性={act}
"""

        # 添加验证信息（如果有）
        if 'verification' in sig:
            ver = sig['verification']

            # 验证后的判断
            if 'verified_claim' in ver:
                summary += f"\n**验证后判断**: {ver['verified_claim']}\n"

            # 真实影响路径
            if 'verified_impact_path' in ver and ver['verified_impact_path']:
                summary += "\n**真实影响路径**:\n"
                for path in ver['verified_impact_path'][:3]:  # 只取前3条
                    summary += f"- {path}\n"

            # 验证来源（简化版）
            if 'verified_data' in ver and ver['verified_data']:
                summary += "\n**关键证据**:\n"
                for data in ver['verified_data'][:2]:  # 只取前2个来源
                    summary += f"- {data.get('source', 'N/A')}: {data.get('finding', '')[:100]}...\n"

            # 验证备注
            if 'verification_notes' in ver:
                summary += f"\n**验证总结**: {ver['verification_notes'][:150]}...\n"

        signal_summaries.append(summary)

    combined_signals = '\n'.join(signal_summaries)

    # 构建 ticker 映射说明
    ticker_instruction = ""
    if ticker_map:
        ticker_list = ', '.join([f"{name} → ${ticker}" for name, ticker in sorted(ticker_map.items(), key=lambda x: -len(x[0]))[:15]])
        ticker_instruction = f"\n\n上市公司使用 $TICKER 格式: {ticker_list}"

    system_prompt = f"""你是资深买方分析师，给客户写一页纸操作备忘录。基于 6 个投资信号，直接给出当下可执行的配置方案。

# 核心要求
- **观点鲜明**：明确说买/卖/等待，不要"可能"、"或许"、"建议关注"
- **无废话**：删除所有套话（"随着...的发展"、"综合考虑"、"值得关注"）
- **可执行**：每个标的都要有具体仓位数字和入场条件
- **优先级清晰**：分核心/卫星/观察三档，说清楚为什么分这个档
- **不要模糊两可**：避免"取决于"、"根据情况"、"视情况而定"

# 输出格式（严格遵守）

## 核心持仓（40-50%）
**$TICKER1 (15-20%)** - [信号X显示的核心逻辑，为什么是确定性机会]
- 入场：当前价分批建仓 或 回调至[技术位/估值]
- 催化剂：[Q几财报/X月事件]
- 止损：破位[技术位]或[基本面条件]

**$TICKER2 (10-15%)** - [信号Y的核心逻辑]
- 入场：当前价 或 [具体等什么]
- 催化剂：[时间/事件]
- 止损：[条件]

## 卫星仓位（20-30%）
**$TICKER3 (10-15%)** - 高Beta，赌[什么]
- 入场：[2月/3月/等IPO/等调整]
- 跟踪：[季度收入/市占率/某个具体KPI]

## 不碰
- **$TICKER4**: 看空，[信号Z显示的致命问题]
  - 看空理由：[1、2、3具体原因]
  - 什么情况下转多：如果[具体条件A]且[具体条件B]，重新评估
- **$TICKER5**: 逻辑不清晰
  - 不碰理由：[为什么逻辑不清]
  - 什么情况下关注：等[具体数据/事件]验证后再看

## 风险控制
- 总仓位不超过 X%
- 单票止损 X%
- 如果[宏观条件]，全部减仓

## 关键时间点
- [日期]: [公司]财报
- [日期]: [事件]{ticker_instruction}

# 禁止用语
- "建议关注" "值得配置" "可以考虑" "根据风险偏好" "有潜在机会"
- "随着...发展" "在...背景下" "综合来看" "进一步明朗化"
- "可能" "或许" "取决于" "视情况而定"
- 不要使用emoji
- 不要编造价格，用"当前价"或"回调至XX倍PE"

# 必须做到
- 每个标的明确引用是哪个信号支持的
- "不碰"列表必须说清楚看空理由
- 催化剂必须是具体的时间/事件
- 直接说"买" "卖" "等待" "不碰"

直接输出markdown，不加任何解释。"""

    try:
        # 使用 Gemini 3 Pro
        prompt = f"""{system_prompt}

请分析以下信号，生成综合投资建议：

{combined_signals}"""

        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,  # 增加到最大值
                tools=[types.Tool(google_search=types.GoogleSearch())],  # 启用 Google Search
                thinking_config=types.ThinkingConfig(thinking_budget=4096)  # 启用推理增强
            )
        )

        # Gemini响应格式处理
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()

        print(f"   Gemini响应为空")
        return None

    except Exception as e:
        import traceback
        print(f"   生成投资策略失败: {e}")
        print(f"   详细错误: {traceback.format_exc()}")
        return None

def polish_excerpt_with_llm(paragraphs, ticker_map=None):
    """
    使用 GPT-4o 润色原文摘录

    将多个段落合并，按说话人分段，去除口语化，生成书面化文本

    Args:
        paragraphs: 段落列表
        ticker_map: 公司名到 ticker 的映射（用于 $TICKER 格式）
    """
    client = get_openai_client()
    if not client:
        # 如果没有API key，回退到硬规则
        return None

    # 合并所有段落文本（保留说话人信息）
    full_text = []
    for para in paragraphs:
        speaker = para.get('speaker', 'Unknown')
        text = para['text']
        full_text.append(f"[{speaker}]: {text}")

    combined = '\n'.join(full_text)

    # 构建 ticker 映射说明
    ticker_instruction = ""
    if ticker_map:
        ticker_list = ', '.join([f"{name} → ${ticker}" for name, ticker in sorted(ticker_map.items(), key=lambda x: -len(x[0]))[:15]])
        ticker_instruction = f"""

7. **重要格式要求**：上市公司必须使用 $TICKER 格式
   - 示例：$GOOGL、$NVDA、$MSFT、$AAPL、$META
   - 映射表（部分）：{ticker_list}
   - 未上市公司保持原名（如 OpenAI、SpaceX、Anthropic）
   - 第一次提及可以写"Google ($GOOGL)"，后续只用 $GOOGL"""

    system_prompt = f"""你是专业的文本编辑，负责将播客转录的原文摘录改写为书面化、按语义清晰分段的研究笔记格式。

核心要求：按语义/主题拆分段落
- 识别不同的观点、论据、主题，每个独立成段
- 即使是同一个说话人连续说的话，也要按语义拆分
- 每段只讲一个小主题/观点，2-4句话
- 不要把多个观点挤在一段里

具体要求：
1. 语义拆分（最重要）：
   主题1 → 独立段落
   主题2 → 独立段落
   主题3 → 独立段落

2. 去除口语化：
   删除"我觉得"、"就是说"、"这个"、"那个"、"然后"等

3. 格式：**说话人**: 内容
   - 相同说话人连续多段也要重复标识

4. 断句：长句（>30字）拆分为短句

5. 保持完整：不删减核心观点、数据、专业术语

6. 重点突出（重要）：
   - 识别每段最关键的1-2句完整陈述，用 **加粗整句** 突出
   - 关键句包括：核心论点、重要判断、关键数据、转折观点、结论
   - 不要加粗零散的专有名词或单个词语，而是加粗完整的重要句子
   - 每段只加粗最重要的句子，不是所有句子
   - 示例：**SpaceX 计划在 2026 年上市，目标估值为 1.5 万亿至 2 万亿。**
{ticker_instruction}

错误示例（不要这样 - 加粗零散词语）：
**Bruce**: **SpaceX** 计划在 **2026 年**上市，目标估值为 **1.5 万亿**。这是一个巨大的独角兽公司。

正确示例（要这样 - 加粗关键句子）：
**Bruce**: **SpaceX 计划在 2026 年上市，目标估值为 1.5 万亿。** 这是一个巨大的独角兽公司。

**Bruce**: 华尔街会考虑技术可行性和市场需求。商业太空领域的技术进步，比如更低的发射成本，会影响估值。

**Bruce**: 政策和法规环境也会影响投资决策。政府支持可能加速发展，监管障碍可能成为挑战。

**Bruce**: **从国家安全的角度来看，SpaceX 具有很强的国家安全属性，是稀缺资产，难以用普通商业标准衡量。**

直接输出润色后的文本，不要添加任何解释。"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        polished = response.choices[0].message.content.strip()
        return polished

    except Exception as e:
        print(f"   ⚠️ LLM润色失败: {e}")
        return None

def simplify_oral_text(text):
    """
    激进地精简口语化表达，转为书面化风格
    """
    # 去除填充词和口头禅
    text = re.sub(r'我觉得|我会觉得|会觉得|觉得', '', text)
    text = re.sub(r'就是说|说白了|怎么说呢|怎么讲|这么来讲|这么说', '', text)
    text = re.sub(r'其实呢|然后呢|那么呢|那个呢', '', text)
    text = re.sub(r'啊|呀|吧(?=[，。！？])', '', text)  # 保留"吧"如果在句中

    # 去除冗余的指示代词和连接词
    text = re.sub(r'这个(?![一-龥])|那个(?![一-龥])', '', text)  # "这个"后面如果不是汉字就删除
    text = re.sub(r'这样|那样|这种|那种', '', text)
    text = re.sub(r'这里面|那里面', '', text)
    text = re.sub(r'这边|那边', '', text)

    # 简化重复的连接词
    text = re.sub(r'然后[，、]?然后', '然后', text)
    text = re.sub(r'然后，', '。', text)  # 句首的"然后"变句号
    text = re.sub(r'，然后', '。', text)  # 句中的"然后"变句号

    # 简化冗余表达
    text = re.sub(r'相对来说|相对而言|相对', '', text)
    text = re.sub(r'从[^，。]{1,8}角度来说|从[^，。]{1,8}角度来看|从[^，。]{1,8}角度', '', text)
    text = re.sub(r'比较|一定程度上', '', text)
    text = re.sub(r'可能|也许(?=[会是])', '', text)
    text = re.sub(r'所有这些花了很多钱的', '这些昂贵的', text)
    text = re.sub(r'你们觉得|大家觉得|我们觉得', '', text)
    text = re.sub(r'[对对]{2,}[，。]?', '。', text)  # "对对对"

    # 清理连续的逗号和句号
    text = re.sub(r'[，、]{2,}', '，', text)
    text = re.sub(r'。{2,}', '。', text)
    text = re.sub(r'，。|。，', '。', text)
    text = re.sub(r'，(?=。)', '', text)  # 逗号后面紧跟句号，删除逗号

    # 修复断句：长句子中间加句号
    text = re.sub(r'([^。]{60,}?)，([^，。]{30,})', r'\1。\2', text)

    # 清理多余空格
    text = re.sub(r'\s+', '', text)  # 中文中删除所有空格
    text = re.sub(r'([a-zA-Z0-9])(?=[一-龥])', r'\1 ', text)  # 英文和数字后加空格

    # 清理开头和结尾的标点
    text = re.sub(r'^[，。、]+|[，。、]+$', '', text)

    return text.strip()

def merge_segments_into_paragraphs(segments, start_sec, end_sec, context_sec=15):
    """
    将碎片化的转录片段合并成完整段落

    Args:
        segments: 转录片段列表
        start_sec: 关键内容开始时间（秒）
        end_sec: 关键内容结束时间（秒）
        context_sec: 前后上下文时长（秒）
    """
    # 扩展时间范围包含上下文
    context_start = start_sec - context_sec
    context_end = end_sec + context_sec

    # 收集所有相关片段（使用重叠判断，避免漏掉部分重叠的段落）
    relevant_segments = []
    for seg in segments:
        # 重叠判断：seg 的结束时间 >= context 开始时间 且 seg 的开始时间 <= context 结束时间
        if seg['end_seconds'] >= context_start and seg['start_seconds'] <= context_end:
            # 判断是否是关键片段（完全在核心时间范围内或部分重叠）
            is_key = (seg['end_seconds'] >= start_sec and seg['start_seconds'] <= end_sec)
            relevant_segments.append({
                'time': seg['start'],
                'text': seg['text'].strip(),
                'speaker': seg.get('speaker', 'Unknown'),
                'is_key': is_key,
                'seconds': seg['start_seconds']
            })

    if not relevant_segments:
        return None

    # 按说话人分段（每次说话人变化时断开）
    paragraphs = []
    current_para = []
    current_speaker = None
    current_is_key = False

    for i, seg in enumerate(relevant_segments):
        # 如果说话人变化或关键性变化，开始新段落
        if (seg['speaker'] != current_speaker or seg['is_key'] != current_is_key) and current_para:
            paragraphs.append({
                'text': ''.join([s['text'] for s in current_para]),
                'speaker': current_speaker,
                'is_key': current_is_key,
                'time_range': f"{current_para[0]['time']} - {current_para[-1]['time']}"
            })
            current_para = []

        current_para.append(seg)
        current_speaker = seg['speaker']
        current_is_key = seg['is_key']

    # 添加最后一段
    if current_para:
        paragraphs.append({
            'text': ''.join([s['text'] for s in current_para]),
            'speaker': current_speaker,
            'is_key': current_is_key,
            'time_range': f"{current_para[0]['time']} - {current_para[-1]['time']}"
        })

    # 文本已在全文润色阶段处理过，无需再次润色
    return paragraphs

def timestamp_to_seconds(ts):
    """HH:MM:SS 转秒"""
    parts = [float(x) for x in ts.split(':')]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]

def generate_research_notes(transcript_file, signals_file, watchlist_file=None):
    """生成投资研究笔记

    Args:
        transcript_file: 转录文件路径
        signals_file: 信号文件路径
        watchlist_file: watchlist 文件路径（可选，用于 $TICKER 格式化）
    """

    # 使用润色后的转录文件
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    # 读取自动提取的信号
    with open(signals_file, 'r', encoding='utf-8') as f:
        extracted = json.load(f)
        signals = extracted['signals']

    # 构建 ticker 映射
    ticker_map = build_ticker_map(watchlist_file)
    if ticker_map:
        print(f"   ✓ 加载 {len(ticker_map)} 个公司的 ticker 映射")

    # 生成笔记
    notes = []
    notes.append("# 投资研究笔记（自动提取）\n\n")
    notes.append("**节目**: 硅谷101 #233 - 华尔街视角下的AI泡沫、芯片及黑天鹅\n")
    notes.append("**日期**: 2026-01-14\n")
    notes.append("**来源**: Bruce Liu & Ren Yang (Esoterica Capital - 济容投资)\n")
    notes.append(f"**信号数量**: {len(signals)} 个\n\n")
    notes.append("---\n\n")

    for i, signal in enumerate(signals, 1):
        # 提取并合并段落
        start_sec = timestamp_to_seconds(signal['time_start'])
        end_sec = timestamp_to_seconds(signal['time_end'])

        # 如果时间范围为0或太小（start == end），扩展到 ±15 秒
        if abs(end_sec - start_sec) < 2:
            start_sec = max(0, start_sec - 15)
            end_sec = end_sec + 15

        paragraphs = merge_segments_into_paragraphs(
            transcript['segments'],
            start_sec,
            end_sec,
            context_sec=10
        )

        # 格式化公司名 - 使用统一的标准格式
        company_map = build_company_map(watchlist_file)

        if 'entities' in signal:
            # 新格式：多实体
            company_parts = []
            for entity in signal['entities']:
                name = entity.get('name', 'Unknown')

                # 尝试从 company_map 获取标准格式
                if name in company_map:
                    company_parts.append(company_map[name]['display'])
                else:
                    # 未知公司，保持原名
                    ticker = entity.get('ticker')
                    if ticker and ticker.lower() != 'none':
                        company_parts.append(f"{name} (${ticker})")
                    else:
                        company_parts.append(name)

            company_header = " vs ".join(company_parts)
        else:
            # 旧格式：单公司
            company_name = signal.get('company', 'Unknown')

            # 尝试从 company_map 获取标准格式
            if company_name in company_map:
                company_header = company_map[company_name]['display']
            else:
                # 未知公司，使用原格式
                ticker = signal.get('ticker')
                if ticker and ticker.lower() != 'none':
                    company_header = f"{company_name} (${ticker})"
                else:
                    company_header = company_name

        notes.append(f"## {i}. {company_header}\n\n")

        # Theme 字段（新格式用 claim，旧格式用 theme）
        theme = signal.get('claim', signal.get('theme', '无主题'))
        # 替换 theme 中的公司名为 $TICKER
        theme = add_tickers_to_text(theme, ticker_map)
        notes.append(f"### {theme}\n\n")

        # 三维度评估（并排显示）
        confidence = signal.get('confidence', 'low').upper()
        novelty = signal.get('novelty', 'low').upper()
        actionability = signal.get('actionability', 'low').upper()
        notes.append(f"**置信度**: {confidence} | **新颖度**: {novelty} | **可行动性**: {actionability}\n\n")

        # 如果有验证数据，优先显示验证结果
        if 'verification' in signal:
            verification = signal['verification']

            # 验证状态
            status_map = {
                'verified': '✅ 已验证',
                'partially_verified': '⚠️ 部分验证',
                'unverified': '❌ 未验证',
                'contradicted': '❌ 与事实矛盾'
            }
            status_text = status_map.get(verification.get('verification_status'), '未知')
            notes.append(f"**验证状态**: {status_text} ({verification.get('verification_date', 'N/A')})\n\n")

            # 验证后的判断（如果不同于原始claim）
            if 'verified_claim' in verification:
                verified_claim = add_tickers_to_text(verification['verified_claim'], ticker_map)
                notes.append(f"**验证后判断**: {verified_claim}\n\n")

            # 真实影响路径
            if 'verified_impact_path' in verification:
                notes.append(f"**真实影响路径**（基于Web搜索）\n")
                for path_item in verification['verified_impact_path']:
                    path_item_formatted = add_tickers_to_text(path_item, ticker_map)
                    notes.append(f"> {path_item_formatted}\n")
                notes.append("\n")

            # 验证数据来源（带信源分类和可信度）
            if 'verified_data' in verification:
                notes.append(f"**验证来源**\n")
                for data in verification['verified_data']:
                    # 智能判断信源类型和可信度（如果字段不存在）
                    source_type = data.get('source_type')
                    credibility = data.get('credibility')

                    if not source_type or not credibility:
                        # 根据来源名称自动判断
                        source_name = data.get('source', '').lower()

                        # 判断信源类型
                        if any(x in source_name for x in ['bloomberg', 'reuters', 'wsj', 'wall street journal', 'financial times', 'ft ', 'forbes', 'cnbc']):
                            source_type = 'tier1_media'
                            credibility = 'high'
                        elif any(x in source_name for x in ['techcrunch', 'verge', 'business insider', 'nikkei', 'ars technica']):
                            source_type = 'tier2_media'
                            credibility = 'medium'
                        elif any(x in source_name for x in ['sec filing', '10-k', '8-k', 's-1', 'investor relations', '公司公告']):
                            source_type = 'company_filing'
                            credibility = 'high'
                        elif any(x in source_name for x in ['trendforce', 'gartner', 'idc', 'omdia', 'lightcounting']):
                            source_type = 'tier1_media'  # 行业研究机构按T1处理
                            credibility = 'high'
                        else:
                            source_type = 'tier2_media'  # 默认按T2媒体处理
                            credibility = 'medium'

                    # 信源标签（文字版）
                    type_labels = {
                        'primary': '[一手]',
                        'tier1_media': '[T1媒体]',
                        'tier2_media': '[T2媒体]',
                        'company_filing': '[监管文件]',
                        'unknown': '[来源未知]'
                    }

                    credibility_labels = {
                        'high': '[高可信]',
                        'medium': '[中可信]',
                        'low': '[低可信]'
                    }

                    type_label = type_labels.get(source_type, '')
                    cred_label = credibility_labels.get(credibility, '')

                    notes.append(f"- {type_label}{cred_label} **{data['source']}**: {data['finding']}\n")
                    if 'url' in data:
                        notes.append(f"  - [链接]({data['url']})\n")
                notes.append("\n")

            # 验证备注
            if 'verification_notes' in verification:
                notes.append(f"**验证备注**: {verification['verification_notes']}\n\n")


        # 如果没有验证数据，显示原始的impact_path（标注为未验证）
        if 'verification' not in signal:
            if 'impact_path' in signal:
                notes.append(f"**影响路径**（未验证）\n")
                for path_item in signal['impact_path']:
                    notes.append(f"> {path_item}\n")
                notes.append("\n")
            elif 'insight' in signal:
                notes.append(f"**核心洞察**\n")
                notes.append(f"> {signal['insight']}\n\n")

            # 验证步骤（新格式）或风险点（旧格式）
            if 'verification_steps' in signal:
                notes.append(f"**建议验证步骤**（未执行）\n")
                for step in signal['verification_steps']:
                    notes.append(f"- {step}\n")
                notes.append("\n")
            elif 'risk' in signal:
                notes.append(f"**风险/验证点**\n")
                notes.append(f"> {signal['risk']}\n\n")
        notes.append(f"**原文摘录** `[{signal['time_start']} - {signal['time_end']}]`\n\n")

        if paragraphs:
            # 使用 LLM 润色原文摘录（传递 ticker_map）
            polished_excerpt = polish_excerpt_with_llm(paragraphs, ticker_map)

            if polished_excerpt:
                # LLM润色成功，强制按语义拆分长段落
                lines = polished_excerpt.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 检查是否是说话人格式
                    if line.startswith('**') and '**:' in line:
                        # 提取说话人和文本
                        parts = line.split('**:', 1)
                        if len(parts) == 2:
                            speaker = parts[0].replace('**', '').strip()
                            text = parts[1].strip()

                            # 如果段落太长（>150字），强制拆分
                            if len(text) > 150:
                                split_paras = force_split_long_paragraphs(text, speaker, max_sentences=3)
                                for sp in split_paras:
                                    notes.append(f"{sp}\n\n")
                            else:
                                notes.append(f"**{speaker}**: {text}\n\n")
                        else:
                            notes.append(f"{line}\n\n")
                    else:
                        # 不是说话人格式，直接输出
                        notes.append(f"{line}\n\n")
            else:
                # LLM润色失败，回退：直接使用 step3 文本
                for para in paragraphs:
                    text = para['text'].strip()
                    if len(text) < 15:
                        continue

                    speaker = para.get('speaker', 'Unknown')

                    # 长段落强制拆分
                    if len(text) > 150:
                        split_paras = force_split_long_paragraphs(text, speaker, max_sentences=3)
                        for sp in split_paras:
                            if para['is_key']:
                                notes.append(f"{sp}\n\n")
                            else:
                                notes.append(f"{sp}\n\n")
                    else:
                        if para['is_key']:
                            notes.append(f"**{speaker}**: {text}\n\n")
                        else:
                            notes.append(f"**{speaker}**: {text}\n\n")

        # 修复：使用秒数格式而不是时间戳
        audio_link_seconds = int(signal.get('start_seconds', timestamp_to_seconds(signal['time_start'])))
        notes.append(f"[跳转音频](https://sv101.fireside.fm/233?t={audio_link_seconds})\n\n")
        notes.append("---\n\n")

    # 生成综合投资建议（在所有信号之后）
    print("   正在生成综合投资策略...")
    investment_strategy = generate_investment_strategy(signals, ticker_map)
    if investment_strategy:
        notes.append("# 综合投资建议\n\n")
        notes.append(investment_strategy)
        notes.append("\n\n---\n\n")
        notes.append("*以上建议基于播客内容自动生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*\n")
    else:
        print("   未能生成综合投资策略")

    return ''.join(notes)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python step5_investment_notes.py <transcript_json> <signals_json> [watchlist_json] [output_md]")
        print("")
        print("参数:")
        print("  transcript_json : 润色后的转录 JSON")
        print("  signals_json    : 提取的信号 JSON")
        print("  watchlist_json  : watchlist JSON（可选，用于 $TICKER 格式化）")
        print("  output_md       : 输出的 Markdown 文件（可选，默认 investment_research_notes.md）")
        print("")
        print("示例:")
        print("  python step5_investment_notes.py transcript.json signals.json")
        print("  python step5_investment_notes.py transcript.json signals.json config/watchlist.json")
        print("  python step5_investment_notes.py transcript.json signals.json config/watchlist.json output.md")
        sys.exit(1)

    transcript_file = sys.argv[1]
    signals_file = sys.argv[2]

    # 判断第3个参数是 watchlist 还是 output
    watchlist_file = None
    output_file = 'investment_research_notes.md'

    if len(sys.argv) > 3:
        # 如果第3个参数是 .json，认为是 watchlist
        if sys.argv[3].endswith('.json'):
            watchlist_file = sys.argv[3]
            if len(sys.argv) > 4:
                output_file = sys.argv[4]
        else:
            # 否则认为是 output
            output_file = sys.argv[3]

    print("正在生成投资研究笔记...")
    notes = generate_research_notes(transcript_file, signals_file, watchlist_file)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(notes)

    # 统计信号数量
    with open(signals_file, 'r', encoding='utf-8') as f:
        extracted = json.load(f)
        signal_count = len(extracted['signals'])
        company_count = len(extracted['metadata']['companies_mentioned'])

    print(f"✅ 投资研究笔记已生成: {output_file}")
    print(f"   - {signal_count} 个自动提取的信号")
    print(f"   - 涉及 {company_count} 家公司")
    print("   - 完整段落 + 清晰标记")
    print("   - 包含洞察和风险点")
