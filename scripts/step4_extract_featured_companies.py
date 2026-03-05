#!/usr/bin/env python3
"""
从转录中自动提取动态 featured_companies（关注公司列表）

策略：
1. 分析转录文本，识别所有提到的公司
2. 根据讨论时长、讨论深度评分
3. 自动查找 ticker 符号
4. 生成或合并到 featured_companies

使用方法：
    python step4_extract_featured_companies.py <transcript_json> [existing_featured_companies]
"""

import json
import sys
import os
from google.genai import types
import re
from gemini_utils import get_gemini_client, get_project_id, DEFAULT_MODEL

# 配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATION = "global"
GEMINI_MODEL = DEFAULT_MODEL

# Lazy client initialization
client = None

def _get_client():
    global client
    if client is None:
        client = get_gemini_client(location=LOCATION)
        project_id = get_project_id()
        print(f"🔧 初始化 Vertex AI: {GEMINI_MODEL} @ {LOCATION} ({project_id})")
    return client

def extract_companies_from_full_transcript(segments):
    """
    从完整转录中提取公司列表（使用 Gemini 3 Pro 长上下文）

    Args:
        segments: 完整的转录片段列表（带时间戳）

    Returns:
        公司列表（带重要性评分）
    """
    c = _get_client()
    if not c:
        print("⚠️  Gemini 客户端未初始化")
        return []

    # 构建带时间戳的转录文本
    transcript_text = ""
    for seg in segments:
        time_start = seg.get('start', seg.get('time_start', '00:00:00'))
        text = seg.get('text', '')
        transcript_text += f"[{time_start}] {text}\n"

    system_prompt = """你是公司信息提取专家，从播客转录中识别公司并评分。

评分规则（三维度，总分1-10）：
**最终评分 = 时长分(1-4) + 深度分(0-3) + 观点强度(0-3)**

1. **讨论时长**（1-4分）：
   - 10+分钟 → 4分
   - 5-10分钟 → 3分
   - 2-5分钟 → 2分
   - <2分钟 → 1分

2. **讨论深度**（0-3分）：
   - 深度分析（估值/财务/战略/详细机制）→ 3分
   - 中等分析（产品特性/竞争格局/市场）→ 2分
   - 一般提及（举例/对比）→ 1分
   - 背景提及（一笔带过）→ 0分

3. **观点强度**（0-3分）⭐ 关键：只要观点鲜明就给高分，不论看多看空
   - 强烈观点（"我很喜欢"/"强烈看好" 或 "强烈质疑"/"避免"）→ 3分
   - 明确观点（"值得关注" 或 "担忧风险"/"质疑"）→ 2分
   - 轻微观点（"可以看看" 或 "不太看好"）→ 1分
   - 无明确观点（仅客观分析，无立场）→ 0分

4. **观点方向**（sentiment）：
   - "bullish": 看多/推荐/看好
   - "bearish": 看空/质疑/担忧
   - "neutral": 中性分析/无明确立场

**评分示例**：
- Synopsys: 1+2+3=6, bullish（强烈推荐）
- OpenAI: 2+3+3=8, bearish（强烈质疑商业模式）
- NVIDIA: 4+3+0=7, neutral（深度分析无立场）

输出 JSON格式（**严格要求**）：
{
  "companies": [
    {
      "name": "公司名",
      "ticker": "GOOGL",
      "importance": 8,
      "sentiment": "bullish",
      "context": "investment",
      "reason": "3+3+2=8，深度分析且明确看好"
    },
    {
      "name": "OpenAI",
      "ticker": null,
      "importance": 8,
      "sentiment": "bearish",
      "context": "concern",
      "reason": "3+3+2=8，质疑商业模式"
    },
    {
      "name": "NVIDIA",
      "ticker": "NVDA",
      "importance": 7,
      "sentiment": "neutral",
      "context": "analysis",
      "reason": "4+3+0=7，深度分析无明确立场"
    }
  ]
}

**关键要求（必须严格遵守）**：
1. sentiment字段**必须输出**，不可省略
2. sentiment只能是: "bullish", "bearish", "neutral" 三选一
3. reason必须包含评分公式（如"3+3+2=8"）
4. reason<30字
5. 每个公司都必须有完整的所有字段
6. 纯JSON格式，不要任何额外内容"""

    user_prompt = f"""从以下播客转录中提取公司并评分（基于讨论时长+深度）：

{transcript_text}"""

    try:
        response = c.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=65536,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )

        response_text = response.text or ""

        # 清理可能的格式问题
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as je:
            print(f"   ⚠️ JSON 解析失败: {je}")
            print(f"   Response preview: {response_text[:200]}")
            return []

        companies = result.get('companies', [])

        # 后处理：确保 importance 在 1-10 范围内
        for company in companies:
            importance = company.get('importance', 5)
            company['importance'] = max(1, min(10, importance))

            # 如果 sentiment 缺失或为null，根据 reason 自动推断
            sentiment_value = company.get('sentiment')
            if sentiment_value is None or sentiment_value == 'null' or sentiment_value == '':
                reason = company.get('reason', '').lower()

                # 看多关键词
                bullish_keywords = ['看好', '推荐', '喜欢', '强烈', '买入', '机会', '优势', '壁垒', '增长', '受益', '超预期', '主导', '稳固']
                # 看空关键词
                bearish_keywords = ['质疑', '看空', '担忧', '风险', '脆弱', '避免', '尴尬', '失去', '挤压', '威胁', '落后', '缺乏', '弱']

                bullish_count = sum(1 for kw in bullish_keywords if kw in reason)
                bearish_count = sum(1 for kw in bearish_keywords if kw in reason)

                if bullish_count > bearish_count:
                    inferred_sentiment = 'bullish'
                elif bearish_count > bullish_count:
                    inferred_sentiment = 'bearish'
                else:
                    inferred_sentiment = 'neutral'

                company['sentiment'] = inferred_sentiment
                print(f"   → {company.get('name')}: {inferred_sentiment} (看多:{bullish_count}, 看空:{bearish_count})")

        return companies

    except Exception as e:
        print(f"   ⚠️ Gemini 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def enrich_with_ticker_lookup(companies):
    """
    为没有 ticker 的公司自动查找股票代码（使用 Gemini）
    """
    c = _get_client()
    if not c:
        return companies

    companies_without_ticker = [c for c in companies if not c.get('ticker')]

    if not companies_without_ticker:
        return companies

    print(f"\n🔍 查找 {len(companies_without_ticker)} 家公司的 ticker...")

    names_list = [c['name'] for c in companies_without_ticker]
    names_str = ', '.join(names_list)

    system_prompt = """你是股票代码专家，负责查找公司的股票代码。

任务：为每个公司提供准确的股票代码（ticker）

规则：
1. 上市公司：提供准确的 ticker（如 AAPL, GOOGL, NVDA）
2. 未上市公司：返回 null
3. 不确定时：返回 null（不要猜测）

输出 JSON 格式：
{
  "tickers": {
    "Apple": "AAPL",
    "Google": "GOOGL",
    "OpenAI": null,
    "SpaceX": null
  }
}

严格输出 JSON，不要添加其他说明。"""

    try:
        response = c.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"公司列表: {names_str}",
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=65536,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )

        raw = ""
        try:
            raw = response.text or ""
        except Exception:
            raw = ""
        result = json.loads(raw) if raw else {}
        ticker_map = result.get('tickers', {})

        for company in companies_without_ticker:
            ticker = ticker_map.get(company['name'])
            if ticker:
                company['ticker'] = ticker
                print(f"   ✓ {company['name']}: {ticker}")

    except Exception as e:
        print(f"   ⚠️ Ticker 查找失败: {e}")

    return companies

def extract_featured_companies(transcript_file, existing_featured_companies_file=None, output_file='featured_companies.json', min_importance=5):
    """
    从转录中提取动态 featured_companies

    Args:
        transcript_file: 转录文件
        existing_featured_companies_file: 现有 featured_companies（可选，用于合并）
        output_file: 输出文件
        min_importance: 最低重要性阈值（默认 5）
    """
    print(f"📖 读取转录: {transcript_file}")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    segments = transcript['segments']
    print(f"   总片段数: {len(segments)}")

    # 加载现有 featured_companies
    existing_companies = []
    if existing_featured_companies_file and os.path.exists(existing_featured_companies_file):
        print(f"\n📖 加载现有 featured_companies: {existing_featured_companies_file}")
        with open(existing_featured_companies_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_companies = existing_data.get('featured_companies', [])
            print(f"   现有公司: {len(existing_companies)} 家")

    # 使用 Gemini 3 Pro 一次性处理完整转录（利用 2M tokens 上下文）
    print(f"\n🤖 使用 Gemini 3 Pro 提取公司（完整上下文）...")
    all_companies = extract_companies_from_full_transcript(segments)

    if all_companies:
        print(f"   ✓ 找到 {len(all_companies)} 家公司")
    else:
        print("   ✗ 未找到公司")

    merged_companies = all_companies  # Gemini 已经在内部去重了

    # 过滤低重要性
    filtered_companies = [c for c in merged_companies if c['importance'] >= min_importance]
    print(f"   过滤后（重要性 >= {min_importance}）: {len(filtered_companies)} 家公司")

    # 查找 ticker
    enriched_companies = enrich_with_ticker_lookup(filtered_companies)

    # 合并现有 featured_companies
    if existing_companies:
        print(f"\n🔄 合并现有 featured_companies...")
        existing_names = {c['company'].lower(): c for c in existing_companies}

        for new_company in enriched_companies:
            name_lower = new_company['name'].lower()
            if name_lower not in existing_names:
                # 新公司，添加到现有列表
                existing_companies.append({
                    'company': new_company['name'],
                    'ticker': new_company.get('ticker'),
                    'reason': new_company.get('reason', ''),
                    'importance': new_company['importance'],
                    'sentiment': new_company.get('sentiment', 'neutral'),
                    'context': new_company.get('context', 'analysis')
                })
                print(f"   + 新增: {new_company['name']} (重要性: {new_company['importance']})")
            else:
                # 已存在，更新重要性
                existing = existing_names[name_lower]
                old_importance = existing.get('importance', 5)
                new_importance = max(old_importance, new_company['importance'])
                if new_importance > old_importance:
                    existing['importance'] = new_importance
                    print(f"   ↑ 更新: {new_company['name']} (重要性: {old_importance} → {new_importance})")

        # 按重要性排序
        existing_companies.sort(key=lambda x: -x.get('importance', 5))
        final_featured_companies = existing_companies
    else:
        # 转换格式
        final_featured_companies = [
            {
                'company': c['name'],
                'ticker': c.get('ticker'),
                'reason': c['reason'],
                'importance': c['importance'],
                'sentiment': c.get('sentiment', 'neutral'),
                'context': c['context']
            }
            for c in enriched_companies
        ]

    # 从文件路径提取 podcast_id 和 episode_id
    podcast_id = None
    episode_id = None

    # 尝试从路径提取: output/sv101_ep233/233_transcript_polished.json
    path_match = re.search(r'/([^/]+)_ep(\d+)/', transcript_file)
    if path_match:
        podcast_id = path_match.group(1)
        episode_id = path_match.group(2)

    # 保存结果
    output_data = {
        'featured_companies': final_featured_companies,
        'metadata': {
            'source': transcript_file,
            'podcast_id': podcast_id,
            'episode_id': episode_id,
            'total_companies': len(final_featured_companies),
            'min_importance': min_importance,
            'extraction_method': 'gemini_3_pro_full_context',
            'scoring_criteria': 'discussion_duration + discussion_depth'
        }
    }

    print(f"\n💾 保存 featured_companies: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 显示结果
    print(f"\n✅ 完成！")
    print(f"\n📊 Featured Companies 统计:")
    print(f"   总公司数: {len(final_featured_companies)}")
    print(f"   有 ticker: {len([c for c in final_featured_companies if c.get('ticker')])} 家")
    print(f"   无 ticker: {len([c for c in final_featured_companies if not c.get('ticker')])} 家")

    print(f"\n🏆 Top 10 重要公司:")
    for i, company in enumerate(final_featured_companies[:10], 1):
        ticker_str = f"({company.get('ticker')})" if company.get('ticker') else "(未上市)"
        print(f"   {i}. {company['company']} {ticker_str} - 重要性: {company.get('importance', 'N/A')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step4_extract_featured_companies.py <transcript_json> [existing_featured_companies] [output] [min_importance]")
        print("")
        print("参数:")
        print("  transcript_json     : 输入的转录 JSON 文件")
        print("  existing_featured_companies  : 现有 featured_companies JSON（可选，用于合并）")
        print("  output              : 输出的 featured_companies JSON（可选，默认 featured_companies.json）")
        print("  min_importance      : 最低重要性阈值（可选，默认 5）")
        print("")
        print("示例:")
        print("  # 从转录提取新 featured_companies")
        print("  python step4_extract_featured_companies.py transcript.json")
        print("")
        print("  # 合并到现有 featured_companies")
        print("  python step4_extract_featured_companies.py transcript.json config/default_featured_companies.json")
        print("")
        print("  # 指定输出文件和最低重要性")
        print("  python step4_extract_featured_companies.py transcript.json existing.json new_featured_companies.json 7")
        sys.exit(1)

    transcript_file = sys.argv[1]
    existing_featured_companies = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'featured_companies.json'
    min_importance = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    extract_featured_companies(transcript_file, existing_featured_companies, output_file, min_importance)
