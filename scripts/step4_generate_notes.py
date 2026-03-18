#!/usr/bin/env python3
"""
生成投资研究笔记 - 从验证后的信号 + 转录生成 Markdown 报告
"""

import json
import re
import sys
import os
from datetime import datetime

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

    today = datetime.now().strftime('%Y-%m-%d')

    # ── 生成笔记 ──
    notes = []

    # 标题 + 元信息
    if episode_title:
        notes.append(f"# {episode_title}\n\n")
    else:
        notes.append(f"# {podcast_name} EP{episode_id}\n\n")

    meta_parts = [f"日期: {today}"]
    if participants_info:
        meta_parts.append(f"来源: {participants_info}")
    if episode_url:
        meta_parts.append(f"[收听链接]({episode_url})")
    notes.append(" | ".join(meta_parts) + "\n\n")
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

        # 格式化公司名（英文名 + $TICKER，不加中文）
        if 'entities' in signal:
            company_parts = []
            for entity in signal['entities']:
                name = entity.get('name', 'Unknown')
                ticker = entity.get('ticker')
                if not ticker and name in company_map:
                    ticker = company_map[name].get('ticker')
                if ticker and ticker.lower() != 'none':
                    company_parts.append(f"{name} (${ticker})")
                else:
                    company_parts.append(name)
            company_header = " vs ".join(company_parts)
        else:
            company_name = signal.get('company', 'Unknown')
            ticker = signal.get('ticker')
            if not ticker and company_name in company_map:
                ticker = company_map[company_name].get('ticker')
            company_header = f"{company_name} (${ticker})" if ticker and ticker.lower() != 'none' else company_name

        notes.append(f"## {i}. {company_header}\n\n")

        # Claim（不做公司名替换，避免和标题重复冗长）
        theme = signal.get('claim', signal.get('theme', '无主题'))
        notes.append(f"> {theme}\n\n")

        # 三维度
        confidence = signal.get('confidence', 'low').upper()
        novelty = signal.get('novelty', 'low').upper()
        actionability = signal.get('actionability', 'low').upper()
        notes.append(f"置信度: {confidence} | 新颖度: {novelty} | 可行动性: {actionability}\n\n")

        # 验证
        if 'verification' in signal:
            verification = signal['verification']
            status_map = {
                'verified': '✅ 已验证', 'partially_verified': '⚠️ 部分验证',
                'unverified': '❌ 未验证', 'contradicted': '❌ 与事实矛盾'
            }
            status_text = status_map.get(verification.get('verification_status'), '未知')
            notes.append(f"**验证**: {status_text} ({verification.get('verification_date', 'N/A')})\n\n")

            if 'verified_impact_path' in verification and verification['verified_impact_path']:
                notes.append("**影响路径**\n\n")
                for path_item in verification['verified_impact_path']:
                    # 去掉 LLM 返回的前缀如 "影响路径1：" "影响路径2："
                    cleaned = re.sub(r'^影响路径\d+[：:]\s*', '', path_item)
                    notes.append(f"- {cleaned}\n")
                notes.append("\n")

            if 'verified_data' in verification and verification['verified_data']:
                notes.append("**来源**\n\n")
                for data in verification['verified_data']:
                    finding = data.get('finding', '')
                    if len(finding) > 150:
                        finding = finding[:150] + '...'
                    source_name = data.get('source', 'N/A')
                    if 'url' in data and data['url']:
                        notes.append(f"- [{source_name}]({data['url']}): {finding}\n")
                    else:
                        notes.append(f"- {source_name}: {finding}\n")
                notes.append("\n")

        else:
            if 'impact_path' in signal:
                notes.append("**影响路径**（未验证）\n\n")
                for path_item in signal['impact_path']:
                    notes.append(f"- {path_item}\n")
                notes.append("\n")

        # 原文摘录：优先用 evidence_seg_ids 精准定位，过滤过渡语
        audio_link_seconds = int(signal.get('start_seconds', timestamp_to_seconds(signal.get('time_start', '00:00:00'))))
        time_range = f"{signal.get('time_start', '00:00:00')} - {signal.get('time_end', '00:00:00')}"
        audio_link = ""
        if episode_url:
            separator = '&' if '?' in episode_url else '?'
            audio_link = f" · [跳转音频]({episode_url}{separator}t={audio_link_seconds})"

        notes.append(f"**原文摘录** [{time_range}]{audio_link}\n\n")

        # 用 evidence_seg_ids 精准提取关键段落（只取核心段，不取上下文）
        evidence_ids = set(signal.get('evidence_seg_ids', []))
        segments = transcript.get('segments', [])

        def _format_excerpt(speaker, text):
            """格式化原文摘录：长段落按句号分段，保持引用格式"""
            text = text.strip()
            if len(text) < 15:
                return ""
            # 长段落按句号分成多个短段（每段2-3句）
            if len(text) > 100:
                sentences = [s.strip() for s in text.replace('。', '。\n').split('\n') if s.strip()]
                chunks = []
                current = []
                for sent in sentences:
                    current.append(sent)
                    if len(''.join(current)) > 80:
                        chunks.append(''.join(current))
                        current = []
                if current:
                    chunks.append(''.join(current))
                lines = [f"> **{speaker}**: {chunks[0]}"]
                for chunk in chunks[1:]:
                    lines.append(f"> {chunk}")
                return '\n>\n'.join(lines) + '\n>\n'
            else:
                return f"> **{speaker}**: {text}\n>\n"

        if evidence_ids:
            for seg in segments:
                if seg.get('id') in evidence_ids:
                    notes.append(_format_excerpt(seg.get('speaker', 'Unknown'), seg.get('text', '')))
        elif paragraphs:
            for para in paragraphs:
                notes.append(_format_excerpt(para.get('speaker', 'Unknown'), para.get('text', '')))

        notes.append("\n")

        notes.append("---\n\n")

    return ''.join(notes)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python step4_generate_notes.py <transcript_json> <signals_json> [verified_signals_json] [featured_companies_json] [output_md]")
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
