#!/usr/bin/env python3
"""
从转录中自动提取动态 watchlist（关注公司列表）

策略：
1. 分析转录文本，识别所有提到的公司
2. 根据提及频率、上下文重要性评分
3. 自动查找 ticker 符号
4. 生成或合并到 watchlist

使用方法：
    python step3b_extract_watchlist.py <transcript_json> [existing_watchlist]
"""

import json
import sys
import os
from openai import AzureOpenAI

# Azure OpenAI 客户端
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
    print("⚠️  未找到 AZURE_OPENAI_API_KEY")
    print("   请在 .env 文件中配置或设置环境变量")
    sys.exit(1)

client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint="https://aigc-japan-east.openai.azure.com/",
    api_version="2025-04-01-preview",
    max_retries=2,
    timeout=120.0,
)

def segment_transcript(segments, max_chars=8000):
    """
    将转录分段（避免超过 LLM token 限制）

    Args:
        segments: 转录片段列表
        max_chars: 每段最大字符数

    Returns:
        分段列表
    """
    chunks = []
    current_chunk = []
    current_length = 0

    for seg in segments:
        text = seg['text']
        if current_length + len(text) > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [seg]
            current_length = len(text)
        else:
            current_chunk.append(seg)
            current_length += len(text)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def extract_companies_from_chunk(chunk_segments):
    """
    从一段转录中提取公司列表

    Returns:
        公司列表（带重要性评分）
    """
    # 合并文本
    text = '\n'.join([seg['text'] for seg in chunk_segments])

    system_prompt = """你是公司信息提取专家，负责从播客转录中识别所有提到的公司。

任务：提取所有公司名称，并评估其重要性

提取规则：
1. **公司类型**：
   - 上市公司（有 ticker 的）
   - 未上市公司（如 OpenAI, SpaceX, Anthropic）
   - 科技巨头（FAANG, 芯片厂商等）
   - 创业公司、投资机构

2. **重要性评分**（1-10）：
   - 10分：核心话题，深度讨论（估值、业绩、战略）
   - 7-9分：重要提及（产品、竞争、市场地位）
   - 4-6分：一般提及（对比、举例）
   - 1-3分：轻微提及（一笔带过）

3. **上下文分类**：
   - "investment" - 投资机会、估值、财务
   - "technology" - 技术突破、产品发布
   - "competition" - 竞争关系、市场份额
   - "general" - 一般性提及

输出 JSON 格式：
{
  "companies": [
    {
      "name": "公司名称",
      "ticker": "股票代码（如果已知）",
      "importance": 8,
      "context": "investment",
      "reason": "讨论了 IPO 计划和估值"
    }
  ]
}

注意：
- 公司名称尽量使用官方名称（如 "Alphabet" 而不是 "Google"，但可以在 reason 中说明）
- ticker 如果不确定就留空（null）
- 去重（同一公司只提取一次，取最高重要性）
- 严格输出 JSON，不要添加其他说明
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('companies', [])

    except Exception as e:
        print(f"   ⚠️ LLM 提取失败: {e}")
        return []

def merge_companies(all_companies):
    """
    合并多个分段提取的公司，去重并聚合评分

    Args:
        all_companies: 所有公司列表（来自不同分段）

    Returns:
        合并后的公司列表
    """
    # 按公司名称分组
    company_map = {}

    for company in all_companies:
        name = company['name'].lower().strip()

        if name in company_map:
            # 已存在，更新信息
            existing = company_map[name]
            # 取最高重要性
            existing['importance'] = max(existing['importance'], company['importance'])
            # 合并原因
            if company['reason'] not in existing['reason']:
                existing['reason'] += f"; {company['reason']}"
            # 更新 ticker（如果有）
            if company.get('ticker') and not existing.get('ticker'):
                existing['ticker'] = company['ticker']
        else:
            # 新公司
            company_map[name] = {
                'name': company['name'],  # 保留原始大小写
                'ticker': company.get('ticker'),
                'importance': company['importance'],
                'context': company['context'],
                'reason': company['reason']
            }

    # 按重要性排序
    merged = sorted(company_map.values(), key=lambda x: -x['importance'])
    return merged

def enrich_with_ticker_lookup(companies):
    """
    为没有 ticker 的公司自动查找股票代码

    使用 LLM 知识库 + 推理
    """
    companies_without_ticker = [c for c in companies if not c.get('ticker')]

    if not companies_without_ticker:
        return companies

    print(f"\n🔍 查找 {len(companies_without_ticker)} 家公司的 ticker...")

    # 批量查询
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

严格输出 JSON，不要添加其他说明。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"公司列表: {names_str}"}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        ticker_map = result.get('tickers', {})

        # 更新 companies
        for company in companies_without_ticker:
            ticker = ticker_map.get(company['name'])
            if ticker:
                company['ticker'] = ticker
                print(f"   ✓ {company['name']}: {ticker}")

    except Exception as e:
        print(f"   ⚠️ Ticker 查找失败: {e}")

    return companies

def extract_watchlist(transcript_file, existing_watchlist_file=None, output_file='watchlist.json', min_importance=5):
    """
    从转录中提取动态 watchlist

    Args:
        transcript_file: 转录文件
        existing_watchlist_file: 现有 watchlist（可选，用于合并）
        output_file: 输出文件
        min_importance: 最低重要性阈值（默认 5）
    """
    print(f"📖 读取转录: {transcript_file}")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    segments = transcript['segments']
    print(f"   总片段数: {len(segments)}")

    # 加载现有 watchlist
    existing_companies = []
    if existing_watchlist_file and os.path.exists(existing_watchlist_file):
        print(f"\n📖 加载现有 watchlist: {existing_watchlist_file}")
        with open(existing_watchlist_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_companies = existing_data.get('watchlist', [])
            print(f"   现有公司: {len(existing_companies)} 家")

    # 分段处理
    print(f"\n🔗 分段转录（每段约 8000 字符）...")
    chunks = segment_transcript(segments, max_chars=8000)
    print(f"   分为 {len(chunks)} 段")

    # 提取公司
    print(f"\n🤖 使用 GPT-4o 提取公司...")
    all_companies = []

    for i, chunk in enumerate(chunks, 1):
        print(f"   [{i}/{len(chunks)}] 处理中...", end=' ')
        companies = extract_companies_from_chunk(chunk)
        if companies:
            print(f"✓ 找到 {len(companies)} 家公司")
            all_companies.extend(companies)
        else:
            print("✗ 未找到")

    # 合并去重
    print(f"\n🔄 合并公司（去重、聚合评分）...")
    merged_companies = merge_companies(all_companies)
    print(f"   合并后: {len(merged_companies)} 家公司")

    # 过滤低重要性
    filtered_companies = [c for c in merged_companies if c['importance'] >= min_importance]
    print(f"   过滤后（重要性 >= {min_importance}）: {len(filtered_companies)} 家公司")

    # 查找 ticker
    enriched_companies = enrich_with_ticker_lookup(filtered_companies)

    # 合并现有 watchlist
    if existing_companies:
        print(f"\n🔄 合并现有 watchlist...")
        existing_names = {c['company'].lower(): c for c in existing_companies}

        for new_company in enriched_companies:
            name_lower = new_company['name'].lower()
            if name_lower not in existing_names:
                # 新公司，添加到现有列表
                existing_companies.append({
                    'company': new_company['name'],
                    'ticker': new_company.get('ticker'),
                    'reason': new_company['reason'],
                    'importance': new_company['importance'],
                    'context': new_company['context']
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
        final_watchlist = existing_companies
    else:
        # 转换格式
        final_watchlist = [
            {
                'company': c['name'],
                'ticker': c.get('ticker'),
                'reason': c['reason'],
                'importance': c['importance'],
                'context': c['context']
            }
            for c in enriched_companies
        ]

    # 保存结果
    output_data = {
        'watchlist': final_watchlist,
        'metadata': {
            'source': transcript_file,
            'total_companies': len(final_watchlist),
            'min_importance': min_importance,
            'extraction_method': 'dynamic_llm'
        }
    }

    print(f"\n💾 保存 watchlist: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 显示结果
    print(f"\n✅ 完成！")
    print(f"\n📊 Watchlist 统计:")
    print(f"   总公司数: {len(final_watchlist)}")
    print(f"   有 ticker: {len([c for c in final_watchlist if c.get('ticker')])} 家")
    print(f"   无 ticker: {len([c for c in final_watchlist if not c.get('ticker')])} 家")

    print(f"\n🏆 Top 10 重要公司:")
    for i, company in enumerate(final_watchlist[:10], 1):
        ticker_str = f"({company.get('ticker')})" if company.get('ticker') else "(未上市)"
        print(f"   {i}. {company['company']} {ticker_str} - 重要性: {company.get('importance', 'N/A')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step3b_extract_watchlist.py <transcript_json> [existing_watchlist] [output] [min_importance]")
        print("")
        print("参数:")
        print("  transcript_json     : 输入的转录 JSON 文件")
        print("  existing_watchlist  : 现有 watchlist JSON（可选，用于合并）")
        print("  output              : 输出的 watchlist JSON（可选，默认 watchlist.json）")
        print("  min_importance      : 最低重要性阈值（可选，默认 5）")
        print("")
        print("示例:")
        print("  # 从转录提取新 watchlist")
        print("  python step3b_extract_watchlist.py transcript.json")
        print("")
        print("  # 合并到现有 watchlist")
        print("  python step3b_extract_watchlist.py transcript.json config/default_watchlist.json")
        print("")
        print("  # 指定输出文件和最低重要性")
        print("  python step3b_extract_watchlist.py transcript.json existing.json new_watchlist.json 7")
        sys.exit(1)

    transcript_file = sys.argv[1]
    existing_watchlist = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'watchlist.json'
    min_importance = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    extract_watchlist(transcript_file, existing_watchlist, output_file, min_importance)
