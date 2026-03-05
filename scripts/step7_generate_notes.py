#!/usr/bin/env python3
"""
生成投资研究笔记 - 从验证后的信号 + 润色转录生成 Markdown 报告
"""

import json
import re
import sys
import os
from google.genai import types
from gemini_utils import get_gemini_client, DEFAULT_MODEL

POLISH_MODEL = "gemini-2.5-flash"
POLISH_LOCATION = "us-central1"

_gemini_clients = {}

def _get_client(location="global"):
    if location not in _gemini_clients:
        _gemini_clients[location] = get_gemini_client(location=location)
    return _gemini_clients[location]

# =============================================================================
# 公司名映射
# =============================================================================

CN_EN_MAP = {
    'NVIDIA': '英伟达', 'AMD': '超微半导体', 'Intel': '英特尔',
    'Microsoft': '微软', 'Apple': '苹果', 'Google': '谷歌', 'Alphabet': '谷歌',
    'Meta': 'Meta', 'Amazon': '亚马逊', 'Tesla': '特斯拉',
    'Oracle': '甲骨文', 'Broadcom': '博通', 'Qualcomm': '高通',
    'Alibaba': '阿里巴巴', 'Tencent': '腾讯', 'ByteDance': '字节跳动',
    'Baidu': '百度', 'IBM': 'IBM', 'Samsung': '三星', 'TSMC': '台积电',
    'Huawei': '华为', 'Xiaomi': '小米', 'Netflix': '奈飞',
    'Uber': 'Uber', 'Airbnb': 'Airbnb', 'Salesforce': 'Salesforce',
    'ServiceNow': 'ServiceNow', 'Palantir': 'Palantir', 'Snowflake': 'Snowflake',
    'Spotify': 'Spotify', 'Zoom': 'Zoom', 'SpaceX': 'SpaceX',
    'OpenAI': 'OpenAI', 'Anthropic': 'Anthropic', 'CoreWeave': 'CoreWeave',
    'Cerebras': 'Cerebras', 'Groq': 'Groq', 'Stripe': 'Stripe',
    'Snap': 'Snap', 'Pinterest': 'Pinterest',
}


def build_company_map(featured_companies_file):
    """构建标准化公司信息映射表"""
    companies_from_file = {}
    if featured_companies_file and os.path.exists(featured_companies_file):
        try:
            with open(featured_companies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for company in data.get('featured_companies', []):
                    en_name = company.get('company', '').strip()
                    ticker = company.get('ticker')
                    if '/' in en_name:
                        names = [n.strip() for n in en_name.split('/')]
                        main_name = names[0]
                    else:
                        main_name = en_name
                        names = [en_name]
                    cn_name = next((CN_EN_MAP[n] for n in names if n in CN_EN_MAP), main_name)
                    companies_from_file[main_name] = {
                        'cn': cn_name, 'en': main_name, 'ticker': ticker, 'aliases': names
                    }
        except Exception:
            pass

    company_map = {}
    for en_name, info in companies_from_file.items():
        cn_name, ticker = info['cn'], info['ticker']
        display = f"{cn_name}（{info['en']} ${ticker}）" if ticker else f"{cn_name}（{info['en']}）"
        search_keys = set([en_name, cn_name, info['en']])
        search_keys.update(info.get('aliases', []))
        if ticker:
            search_keys.update([ticker, f'${ticker}'])
        for key in list(search_keys):
            if key and key[0].isascii():
                search_keys.add(key.lower())
        for key in search_keys:
            if key:
                company_map[key] = {'cn': cn_name, 'en': info['en'], 'ticker': ticker, 'display': display}
    return company_map


def build_ticker_map(featured_companies_file):
    company_map = build_company_map(featured_companies_file)
    return {k: v['ticker'] for k, v in company_map.items() if v['ticker']}


def add_tickers_to_text(text, ticker_map=None, featured_companies_file=None):
    """规范化文本中的公司名称"""
    company_map = build_company_map(featured_companies_file)
    sorted_companies = sorted(company_map.items(), key=lambda x: -len(x[0]))

    for search_key, info in sorted_companies:
        display = info['display']
        if display in text:
            continue
        pattern = rf'(?<!\$)(?<![a-zA-Z]){re.escape(search_key)}(?!\s*[（(][^）)]*\$[A-Z]+[）)])(?![a-zA-Z])'
        replaced_ranges = []

        def replace_if_not_overlapping(match):
            start, end = match.span()
            for r_start, r_end in replaced_ranges:
                if not (end <= r_start or start >= r_end):
                    return match.group(0)
            replaced_ranges.append((start, start + len(display)))
            return display

        text = re.sub(pattern, replace_if_not_overlapping, text)
    return text


# =============================================================================
# 辅助函数
# =============================================================================

def timestamp_to_seconds(ts):
    """HH:MM:SS 转秒"""
    if not ts:
        return 0.0
    parts = [float(x) for x in ts.split(':')]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


# NOTE: Reserved for cross-podcast aggregation. Not called within this file.
def generate_investment_strategy(signals, ticker_map=None):
    """使用 Gemini 分析所有信号，生成综合投资建议（保留供跨播客聚合使用）"""
    try:
        client = _get_client()
    except Exception:
        return None

    signal_summaries = []
    for i, sig in enumerate(signals, 1):
        companies = ', '.join([e['name'] for e in sig.get('entities', [])][:3])
        claim = sig.get('claim', '')
        conf = sig.get('confidence', 'low')
        nov = sig.get('novelty', 'low')
        act = sig.get('actionability', 'low')
        summary = f"## 信号 {i}: {companies}\n**判断**: {claim}\n**三维度**: 置信度={conf} | 新颖度={nov} | 可行动性={act}\n"
        if 'verification' in sig:
            ver = sig['verification']
            if 'verified_claim' in ver:
                summary += f"**验证后判断**: {ver['verified_claim']}\n"
        signal_summaries.append(summary)

    combined = '\n'.join(signal_summaries)
    prompt = f"基于以下投资信号，生成综合投资建议：\n\n{combined}"

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=65536)
        )
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return None
    except Exception:
        return None


def load_episode_metadata(transcript_file):
    """从转录文件所在目录加载元数据"""
    episode_dir = os.path.dirname(os.path.abspath(transcript_file))
    for filename in os.listdir(episode_dir):
        if filename.endswith('_metadata.json'):
            try:
                with open(os.path.join(episode_dir, filename), 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return {'podcast_name': '投资播客', 'episode_id': 'unknown', 'url': '', 'hosts': []}


def merge_segments_into_paragraphs(segments, start_sec, end_sec, context_sec=15):
    """将碎片化的转录片段合并成完整段落"""
    context_start = start_sec - context_sec
    context_end = end_sec + context_sec

    relevant = []
    for seg in segments:
        if seg['end_seconds'] >= context_start and seg['start_seconds'] <= context_end:
            is_key = (seg['end_seconds'] >= start_sec and seg['start_seconds'] <= end_sec)
            relevant.append({
                'time': seg['start'], 'text': seg['text'].strip(),
                'speaker': seg.get('speaker', 'Unknown'), 'is_key': is_key,
                'seconds': seg['start_seconds']
            })

    if not relevant:
        return None

    paragraphs = []
    current_para = []
    current_speaker = None

    for seg in relevant:
        if seg['speaker'] != current_speaker and current_para:
            paragraphs.append({
                'text': ''.join([s['text'] for s in current_para]),
                'speaker': current_speaker,
                'is_key': any(s['is_key'] for s in current_para),
            })
            current_para = []
        current_para.append(seg)
        current_speaker = seg['speaker']

    if current_para:
        paragraphs.append({
            'text': ''.join([s['text'] for s in current_para]),
            'speaker': current_speaker,
            'is_key': any(s['is_key'] for s in current_para),
        })
    return paragraphs


def polish_excerpt_with_llm(paragraphs, ticker_map=None):
    """使用 Gemini 润色原文摘录"""
    try:
        client = _get_client(location=POLISH_LOCATION)
    except Exception:
        return None

    full_text = []
    for para in paragraphs:
        speaker = para.get('speaker', 'Unknown')
        full_text.append(f"[{speaker}]: {para['text']}")
    combined = '\n'.join(full_text)

    system_prompt = """你是专业的文本编辑，负责将播客转录的原文摘录改写为紧凑、书面化的研究笔记格式。

核心要求：保持紧凑，不要过度拆分
- 同一个说话人的连续发言合并为一段（3-6句话）
- 只在说话人切换时换段

具体要求：
1. 去除口语化：删除"就是说"、"这个"、"那个"、"然后"等填充词
2. 格式：**说话人**: 内容
3. 保持完整：不删减核心观点、数据、专业术语
4. 重点突出：识别每段最关键的1-2句完整陈述，用 **加粗整句** 突出
5. 断句：长句（>50字）拆分为短句

直接输出润色后的文本，不要添加任何解释。"""

    try:
        response = client.models.generate_content(
            model=POLISH_MODEL,
            contents=f"{system_prompt}\n\n{combined}",
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=65536)
        )
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"   ⚠️ LLM润色失败: {e}")
        return None


# =============================================================================
# 主函数：生成投资研究笔记
# =============================================================================

def generate_research_notes(transcript_file, signals_file, featured_companies_file=None, verified_signals_file=None):
    """生成投资研究笔记"""

    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    # 优先读取验证后的信号
    if verified_signals_file and os.path.exists(verified_signals_file):
        print(f"   ✓ 使用验证后的信号: {verified_signals_file}")
        with open(verified_signals_file, 'r', encoding='utf-8') as f:
            signals = json.load(f)['signals']
    else:
        print(f"   ⚠️ 未找到验证文件，使用原始信号: {signals_file}")
        with open(signals_file, 'r', encoding='utf-8') as f:
            signals = json.load(f)['signals']

    # 加载元数据
    metadata = load_episode_metadata(transcript_file)
    podcast_name = metadata.get('podcast_name', '投资播客')
    episode_id = metadata.get('episode_id', 'unknown')
    episode_url = metadata.get('url', '')
    hosts = metadata.get('hosts', [])

    # 获取 episode 标题
    episode_dir = os.path.dirname(transcript_file)
    episode_title = ""
    participants_info = ""
    for filename in os.listdir(episode_dir):
        if filename.endswith('_participants.json'):
            try:
                with open(os.path.join(episode_dir, filename), 'r', encoding='utf-8') as f:
                    pdata = json.load(f)
                    episode_title = pdata.get('episode_info', '')
                    guests = pdata.get('guests', [])
                    if guests:
                        participants_info = ', '.join(guests)
            except Exception:
                pass
            break
    if not participants_info and hosts:
        participants_info = ', '.join(hosts)

    # 构建公司映射（在循环外）
    company_map = build_company_map(featured_companies_file)
    ticker_map = build_ticker_map(featured_companies_file)

    # 加载嘉宾画像
    guest_profiles = {}
    for filename in os.listdir(episode_dir):
        if filename.endswith('_guest_profiles.json'):
            try:
                with open(os.path.join(episode_dir, filename), 'r', encoding='utf-8') as f:
                    guest_profiles = json.load(f).get('guests', {})
            except Exception:
                pass
            break

    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')

    # ── 生成笔记 ──
    notes = []

    # 标题
    if episode_title:
        notes.append(f"# {episode_title}\n\n")
    else:
        notes.append(f"# {podcast_name} EP{episode_id}\n\n")

    notes.append(f"**日期**: {today}\n")
    if participants_info:
        notes.append(f"**来源**: {participants_info}\n")
    if episode_url:
        notes.append(f"**链接**: {episode_url}\n")
    notes.append(f"**信号数量**: {len(signals)} 个\n\n")

    # 嘉宾画像
    if guest_profiles:
        notes.append("## 嘉宾画像\n\n")
        for guest_name, profile in guest_profiles.items():
            notes.append(f"### {guest_name}\n\n")
            style = profile.get('investment_style', {})
            if style:
                style_type = style.get('primary_type', 'N/A')
                style_desc = style.get('description', '')
                notes.append(f"**投资风格**: {style_type}\n")
                if style_desc:
                    notes.append(f"> {style_desc}\n\n")
            risk = profile.get('risk_preference', {})
            if risk:
                risk_level = risk.get('level', 'N/A')
                risk_desc = risk.get('description', '')
                notes.append(f"**风险偏好**: {risk_level}\n")
                if risk_desc:
                    notes.append(f"> {risk_desc}\n\n")
            expertise = profile.get('expertise_areas', [])
            if expertise:
                notes.append(f"**专业领域**: {', '.join(expertise)}\n\n")
            philosophy = profile.get('investment_philosophy', '')
            if philosophy:
                notes.append(f"**投资理念**\n> {philosophy}\n\n")
        notes.append("---\n\n")

    # 逐条信号
    for i, signal in enumerate(signals, 1):
        start_sec = timestamp_to_seconds(signal.get('time_start', '00:00:00'))
        end_sec = timestamp_to_seconds(signal.get('time_end', '00:00:00'))
        if abs(end_sec - start_sec) < 2:
            start_sec = max(0, start_sec - 15)
            end_sec = end_sec + 15

        paragraphs = merge_segments_into_paragraphs(
            transcript['segments'], start_sec, end_sec, context_sec=10
        )

        # 格式化公司名
        if 'entities' in signal:
            company_parts = []
            for entity in signal['entities']:
                name = entity.get('name', 'Unknown')
                if name in company_map:
                    company_parts.append(company_map[name]['display'])
                else:
                    ticker = entity.get('ticker')
                    if ticker and ticker.lower() != 'none':
                        company_parts.append(f"{name} (${ticker})")
                    else:
                        company_parts.append(name)
            company_header = " vs ".join(company_parts)
        else:
            company_name = signal.get('company', 'Unknown')
            if company_name in company_map:
                company_header = company_map[company_name]['display']
            else:
                ticker = signal.get('ticker')
                company_header = f"{company_name} (${ticker})" if ticker and ticker.lower() != 'none' else company_name

        notes.append(f"## {i}. {company_header}\n\n")

        # Claim
        theme = signal.get('claim', signal.get('theme', '无主题'))
        theme = add_tickers_to_text(theme, featured_companies_file=featured_companies_file)
        notes.append(f"### {theme}\n\n")

        # 三维度
        confidence = signal.get('confidence', 'low').upper()
        novelty = signal.get('novelty', 'low').upper()
        actionability = signal.get('actionability', 'low').upper()
        notes.append(f"**置信度**: {confidence} | **新颖度**: {novelty} | **可行动性**: {actionability}\n\n")

        # 验证数据
        if 'verification' in signal:
            verification = signal['verification']
            status_map = {
                'verified': '✅ 已验证', 'partially_verified': '⚠️ 部分验证',
                'unverified': '❌ 未验证', 'contradicted': '❌ 与事实矛盾'
            }
            status_text = status_map.get(verification.get('verification_status'), '未知')
            notes.append(f"**验证状态**: {status_text} ({verification.get('verification_date', 'N/A')})\n\n")

            if 'verified_claim' in verification:
                vc = add_tickers_to_text(verification['verified_claim'], featured_companies_file=featured_companies_file)
                notes.append(f"**验证后判断**: {vc}\n\n")

            if 'verified_impact_path' in verification and verification['verified_impact_path']:
                notes.append("**真实影响路径**（基于Web搜索）\n")
                for path_item in verification['verified_impact_path']:
                    pi = add_tickers_to_text(path_item, featured_companies_file=featured_companies_file)
                    notes.append(f"> {pi}\n")
                notes.append("\n")

            if 'verified_data' in verification:
                notes.append("**验证来源**\n")
                for data in verification['verified_data']:
                    source_name = data.get('source', '').lower()
                    if any(x in source_name for x in ['bloomberg', 'reuters', 'wsj', 'financial times', 'forbes', 'cnbc']):
                        label = '[T1媒体][高可信]'
                    elif any(x in source_name for x in ['trendforce', 'gartner', 'idc']):
                        label = '[T1媒体][高可信]'
                    else:
                        label = '[T2媒体][中可信]'
                    notes.append(f"- {label} **{data.get('source', 'N/A')}**: {data.get('finding', '')}\n")
                    if 'url' in data:
                        notes.append(f"  - [链接]({data['url']})\n")
                notes.append("\n")

            if 'verification_notes' in verification:
                notes.append(f"**验证备注**: {verification['verification_notes']}\n\n")

        else:
            # 未验证信号
            if 'impact_path' in signal:
                notes.append("**影响路径**（未验证）\n")
                for path_item in signal['impact_path']:
                    notes.append(f"> {path_item}\n")
                notes.append("\n")
            if 'verification_steps' in signal:
                notes.append("**建议验证步骤**（未执行）\n")
                for step in signal['verification_steps']:
                    notes.append(f"- {step}\n")
                notes.append("\n")

        # 原文摘录
        notes.append(f"**原文摘录** `[{signal.get('time_start', '00:00:00')} - {signal.get('time_end', '00:00:00')}]`\n\n")

        if paragraphs:
            polished_excerpt = polish_excerpt_with_llm(paragraphs, ticker_map)
            if polished_excerpt:
                notes.append(f"{polished_excerpt}\n\n")
            else:
                for para in paragraphs:
                    text = para['text'].strip()
                    if len(text) < 15:
                        continue
                    speaker = para.get('speaker', 'Unknown')
                    notes.append(f"**{speaker}**: {text}\n\n")

        # 音频跳转
        audio_link_seconds = int(signal.get('start_seconds', timestamp_to_seconds(signal.get('time_start', '00:00:00'))))
        if episode_url:
            separator = '&' if '?' in episode_url else '?'
            notes.append(f"[跳转音频]({episode_url}{separator}t={audio_link_seconds})\n\n")
        notes.append("---\n\n")

    notes.append("*以上内容基于播客转录自动提取，仅供研究参考。*\n")

    return ''.join(notes)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python step7_generate_notes.py <transcript_json> <signals_json> [verified_signals_json] [featured_companies_json] [output_md]")
        sys.exit(1)

    transcript_file = sys.argv[1]
    signals_file = sys.argv[2]
    verified_signals_file = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].endswith('.json') else None

    # Determine featured_companies_file and output_file from remaining args
    featured_companies_file = None
    output_file = 'investment_research_notes.md'

    start_idx = 4 if verified_signals_file else 3
    for i in range(start_idx, len(sys.argv)):
        arg = sys.argv[i]
        if arg.endswith('.json'):
            featured_companies_file = arg
        elif arg.endswith('.md'):
            output_file = arg

    print("正在生成投资研究笔记...")
    notes = generate_research_notes(transcript_file, signals_file, featured_companies_file, verified_signals_file)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(notes)

    with open(signals_file, 'r', encoding='utf-8') as f:
        extracted = json.load(f)
        signal_count = len(extracted['signals'])
        company_count = len(extracted.get('metadata', {}).get('companies_mentioned', []))

    print(f"✅ 投资研究笔记已生成: {output_file}")
    print(f"   - {signal_count} 个自动提取的信号")
    print(f"   - 涉及 {company_count} 家公司")
    print("   - 完整段落 + 清晰标记")
    print("   - 包含洞察和风险点")
