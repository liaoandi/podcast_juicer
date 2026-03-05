#!/usr/bin/env python3
"""
分析嘉宾画像 - 从转录中提取嘉宾的投资风格、风险偏好等

功能：
1. 分析每位嘉宾的发言内容
2. 提取投资风格（成长型/价值型/趋势型）
3. 分析风险偏好（激进/稳健/保守）
4. 识别专业领域和关注话题
5. 更新嘉宾数据库

使用方法：
    python step2b_analyze_guests.py <transcript_with_speakers.json> <participants.json> [output.json]

示例：
    python step2b_analyze_guests.py transcript_speakers.json participants.json guest_profiles.json
"""

import os
import sys
import json
from collections import defaultdict
from gemini_utils import get_gemini_client, DEFAULT_MODEL, clean_json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
GUESTS_DB_FILE = os.path.join(CONFIG_DIR, 'guests.json')

# 嘉宾画像用 pro 模型（需要深度分析投资风格和背景）
GEMINI_MODEL = DEFAULT_MODEL
GUEST_LOCATION = "global"

def call_gemini(client, system_prompt, user_content, max_tokens=65536):
    """Gemini API调用辅助函数"""
    from google.genai import types

    full_prompt = f"{system_prompt}\n\n{user_content}"

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens
        )
    )

    response_text = response.text or ""
    result = clean_json(response_text)
    if result is None:
        raise ValueError(f"Failed to parse JSON from response: {response_text[:200]}")
    return result


def get_llm_client():
    """获取 Gemini 客户端"""
    return get_gemini_client(location="global")


def load_guests_db():
    """加载嘉宾数据库"""
    if os.path.exists(GUESTS_DB_FILE):
        with open(GUESTS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"guests": {}}


def save_guests_db(db):
    """保存嘉宾数据库"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(GUESTS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def normalize_guest_id(name):
    """生成标准化的嘉宾 ID"""
    # 去除空格，转小写，用下划线连接
    return name.lower().replace(' ', '_').replace('-', '_')


def generate_guest_background(guest_name, known_background, client):
    """
    搜索嘉宾的背景资料

    Args:
        guest_name: 嘉宾姓名
        known_background: 已知背景信息（来自 participants.json）
        client: LLM 客户端

    Returns:
        dict: 嘉宾背景资料
    """
    if not client:
        return known_background or {}

    # 构建搜索查询
    search_query = f"{guest_name}"
    if known_background:
        # 添加已知信息帮助搜索
        if isinstance(known_background, str):
            search_query += f" {known_background}"
        elif isinstance(known_background, dict):
            company = known_background.get('company', '')
            if company:
                search_query += f" {company}"

    print(f"      🔍 搜索背景: {search_query}")

    try:
        # 使用 LLM 的知识库 + 搜索能力
        prompt = f"""搜索并整理以下人物的背景资料：

姓名：{guest_name}
已知信息：{json.dumps(known_background, ensure_ascii=False) if known_background else '无'}

请搜索并提供以下信息（如果能找到）：

1. **基本信息**：当前职位、公司、所在地
2. **职业背景**：教育背景、职业经历、曾任职公司
3. **投资经历**：管理的基金、投资风格、知名投资案例
4. **专业领域**：擅长的行业或领域
5. **公开观点**：过往公开发表的重要观点或预测
6. **社交媒体**：Twitter/LinkedIn 等（如有）

输出 JSON 格式：
{{
  "name": "姓名",
  "current_role": "当前职位",
  "company": "公司",
  "education": ["学历1", "学历2"],
  "career_history": ["经历1", "经历2"],
  "investment_track_record": ["案例1", "案例2"],
  "expertise_domains": ["领域1", "领域2"],
  "known_views": ["观点1", "观点2"],
  "social_media": {{"twitter": "", "linkedin": ""}},
  "credibility_notes": "可信度说明",
  "search_confidence": "high/medium/low"
}}

如果信息不确定，标注 search_confidence 为 low。
严格输出 JSON。
"""

        result = call_gemini(client, "", prompt, max_tokens=65536)

        # 打印关键信息
        if result.get('current_role'):
            print(f"      ✓ 职位: {result.get('current_role')}")
        if result.get('company'):
            print(f"      ✓ 公司: {result.get('company')}")
        if result.get('expertise_domains'):
            print(f"      ✓ 专业: {', '.join(result.get('expertise_domains', [])[:3])}")

        return result

    except Exception as e:
        print(f"      ⚠️ 搜索失败: {e}")
        return known_background or {}


def extract_guest_speeches(transcript, speaker_mapping=None):
    """
    从转录中提取每位嘉宾的发言

    支持两种模式：
    1. 有 speaker_mapping（来自声纹分离）：直接用映射后的 speaker 标签
    2. 无 speaker_mapping：尝试模糊匹配

    Args:
        transcript: 转录数据
        speaker_mapping: speaker 映射表（来自 step2）

    Returns:
        dict: {speaker_name: [speech1, speech2, ...]}
    """
    guest_speeches = defaultdict(list)

    for seg in transcript.get('segments', []):
        speaker = seg.get('speaker', '')
        text = seg.get('text', '')

        if not speaker or speaker == 'Unknown':
            continue

        # 直接用 speaker 标签分组（step2 已经映射过了）
        guest_speeches[speaker].append({
            'text': text,
            'start': seg.get('start', ''),
            'end': seg.get('end', ''),
            'role': seg.get('speaker_role', 'unknown')
        })

    return dict(guest_speeches)


def analyze_guest_profile(guest_name, speeches, background_info, client):
    """
    用 LLM 分析嘉宾画像

    Args:
        guest_name: 嘉宾姓名
        speeches: 发言列表
        background_info: 搜索到的背景资料
        client: LLM 客户端

    Returns:
        dict: 嘉宾画像
    """
    if not client or not speeches:
        return None

    # 合并发言（最多取 5000 字）
    all_text = '\n'.join([s['text'] for s in speeches])
    if len(all_text) > 5000:
        all_text = all_text[:5000] + '...'

    # 构建详细的背景信息
    background_str = ""
    if background_info:
        # background_info 可能是字符串（来自 participants.json 的 guest_background）
        if isinstance(background_info, str):
            background_str = f"已知背景：{background_info}\n\n"
        elif isinstance(background_info, dict):
            pass  # fall through to dict handling below
        else:
            background_info = {}

    if background_info and isinstance(background_info, dict):
        bg_parts = []

        if background_info.get('current_role'):
            bg_parts.append(f"职位: {background_info['current_role']}")
        if background_info.get('company'):
            bg_parts.append(f"公司: {background_info['company']}")
        if background_info.get('education'):
            bg_parts.append(f"学历: {', '.join(background_info['education'][:2])}")
        if background_info.get('career_history'):
            bg_parts.append(f"经历: {', '.join(background_info['career_history'][:3])}")
        if background_info.get('expertise_domains'):
            bg_parts.append(f"专业领域: {', '.join(background_info['expertise_domains'])}")
        if background_info.get('investment_track_record'):
            bg_parts.append(f"投资案例: {', '.join(background_info['investment_track_record'][:3])}")
        if background_info.get('known_views'):
            bg_parts.append(f"已知观点: {', '.join(background_info['known_views'][:2])}")

        if bg_parts:
            background_str = "已知背景：\n" + '\n'.join(f"- {p}" for p in bg_parts) + "\n\n"
        else:
            background_str = f"已知背景：{json.dumps(background_info, ensure_ascii=False)}\n\n"

    prompt = f"""分析以下嘉宾在播客中的发言，结合其背景资料，提取其投资画像。

嘉宾：{guest_name}
{background_str}
发言内容：
{all_text}

请分析并输出 JSON：
{{
  "investment_style": {{
    "primary_type": "growth/value/trend/contrarian/macro",
    "description": "一句话描述投资风格",
    "evidence": ["支撑判断的原话摘录1", "原话摘录2"]
  }},
  "risk_preference": {{
    "level": "aggressive/moderate/conservative",
    "description": "一句话描述风险偏好",
    "evidence": ["支撑判断的原话摘录"]
  }},
  "expertise_areas": ["专业领域1", "专业领域2"],
  "focus_topics": ["关注话题1", "关注话题2"],
  "speech_characteristics": {{
    "confidence_level": "high/medium/low",
    "hedging_frequency": "high/medium/low",
    "data_driven": true/false,
    "typical_phrases": ["口头禅或常用表达"]
  }},
  "investment_philosophy": "用 2-3 句话总结其投资理念"
}}

严格输出 JSON。
"""

    try:
        return call_gemini(client, "", prompt, max_tokens=65536)

    except Exception as e:
        print(f"   ⚠️ 分析失败: {e}")
        return None


def update_guest_in_db(db, guest_id, guest_name, profile, episode_id, topics, background=None):
    """更新嘉宾数据库中的记录"""

    if guest_id not in db['guests']:
        # 新嘉宾
        db['guests'][guest_id] = {
            'id': guest_id,
            'name': guest_name,
            'background': {},
            'profiles': [],
            'appearances': [],
            'aggregated_profile': None
        }

    guest = db['guests'][guest_id]

    # 更新背景资料（合并新信息）
    if background and isinstance(background, dict):
        if not guest.get('background'):
            guest['background'] = {}
        # 合并背景信息，新信息覆盖旧信息
        for key, value in background.items():
            if value and key != 'search_confidence':
                guest['background'][key] = value

    # 添加本次画像
    if profile:
        # 从 profile 中移除 background（已单独存储）
        profile_copy = {k: v for k, v in profile.items() if k != 'background'}
        guest['profiles'].append({
            'episode': episode_id,
            'profile': profile_copy
        })

    # 添加出场记录
    if not any(a['episode'] == episode_id for a in guest['appearances']):
        guest['appearances'].append({
            'episode': episode_id,
            'topics': topics
        })

    # 聚合多次画像（如果有多次）
    if len(guest['profiles']) >= 2:
        guest['aggregated_profile'] = aggregate_profiles(guest['profiles'])
    elif len(guest['profiles']) == 1:
        guest['aggregated_profile'] = guest['profiles'][0]['profile']

    return guest


def aggregate_profiles(profiles):
    """聚合多次画像，取最常见的特征"""
    if not profiles:
        return None

    # 简单聚合：取最新的，但保留所有证据
    latest = profiles[-1]['profile']

    # 合并所有证据
    all_evidence = []
    for p in profiles:
        prof = p['profile']
        if prof.get('investment_style', {}).get('evidence'):
            all_evidence.extend(prof['investment_style']['evidence'])
        if prof.get('risk_preference', {}).get('evidence'):
            all_evidence.extend(prof['risk_preference']['evidence'])

    # 合并所有专业领域
    all_expertise = set()
    for p in profiles:
        prof = p['profile']
        if prof.get('expertise_areas'):
            all_expertise.update(prof['expertise_areas'])

    # 合并所有关注话题
    all_topics = set()
    for p in profiles:
        prof = p['profile']
        if prof.get('focus_topics'):
            all_topics.update(prof['focus_topics'])

    aggregated = latest.copy()
    aggregated['expertise_areas'] = list(all_expertise)
    aggregated['focus_topics'] = list(all_topics)
    aggregated['evidence_count'] = len(all_evidence)
    aggregated['episode_count'] = len(profiles)

    return aggregated


def extract_topics_from_signals(signals_file):
    """从信号文件提取话题"""
    topics = set()

    if os.path.exists(signals_file):
        try:
            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for sig in data.get('signals', []):
                    for entity in sig.get('entities', []):
                        topics.add(entity.get('name', ''))
        except Exception:
            pass

    return list(topics)


def analyze_guests(transcript_file, participants_file, output_file=None, episode_id=None):
    """
    分析播客中所有嘉宾的画像

    Args:
        transcript_file: 带说话人的转录文件
        participants_file: 参与者信息文件
        output_file: 输出文件（可选）
        episode_id: 集数 ID（可选，用于数据库）
    """
    print(f"📖 加载转录: {transcript_file}")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    # 加载参与者信息
    participants = {}
    if os.path.exists(participants_file):
        print(f"📖 加载参与者: {participants_file}")
        with open(participants_file, 'r', encoding='utf-8') as f:
            participants = json.load(f)

    # 检查是否有声纹映射
    speaker_mapping = transcript.get('speaker_mapping', {})
    has_diarization = transcript.get('metadata', {}).get('has_diarization', False)

    if speaker_mapping:
        print(f"   ✓ 发现 speaker_mapping: {len(speaker_mapping)} 个映射")
        for orig, info in speaker_mapping.items():
            print(f"      {orig} → {info.get('name', '?')} ({info.get('role', '?')})")

    # 从转录中直接获取所有说话人（step2 已经标注过）
    speaker_stats = defaultdict(lambda: {'count': 0, 'chars': 0, 'role': 'unknown'})
    for seg in transcript.get('segments', []):
        speaker = seg.get('speaker', '')
        if speaker and speaker != 'Unknown':
            speaker_stats[speaker]['count'] += 1
            speaker_stats[speaker]['chars'] += len(seg.get('text', ''))
            speaker_stats[speaker]['role'] = seg.get('speaker_role', 'unknown')

    # 区分主持人和嘉宾
    hosts = []
    guests = []
    for speaker, stats in speaker_stats.items():
        if stats['role'] == 'host':
            hosts.append(speaker)
        else:
            guests.append(speaker)

    print(f"\n   说话人统计:")
    print(f"   主持人: {hosts}")
    print(f"   嘉宾: {guests}")
    for speaker, stats in sorted(speaker_stats.items(), key=lambda x: -x[1]['count']):
        print(f"      {speaker}: {stats['count']} 段, {stats['chars']} 字 ({stats['role']})")

    # 只分析嘉宾（不分析主持人）
    all_speakers = guests if guests else list(speaker_stats.keys())

    print(f"\n   ✓ 待分析嘉宾: {len(all_speakers)} 位")

    # 提取每位嘉宾的发言
    print(f"\n🎤 提取发言...")
    guest_speeches = extract_guest_speeches(transcript, speaker_mapping=speaker_mapping)

    for name, speeches in guest_speeches.items():
        role = speeches[0].get('role', 'unknown') if speeches else 'unknown'
        print(f"   {name} ({role}): {len(speeches)} 段发言")

    # 初始化 LLM
    print(f"\n🤖 初始化 LLM...")
    try:
        client = get_llm_client()
    except Exception as e:
        print(f"   ⚠️ 无法获取 LLM 客户端: {e}")
        client = None
    if not client:
        print("   ⚠️ 无 LLM，跳过画像分析")
        return None

    # 加载嘉宾数据库
    db = load_guests_db()

    # 分析每位嘉宾
    print(f"\n📊 分析嘉宾画像...")
    profiles = {}

    # 尝试获取话题
    topics = []
    if episode_id:
        # 尝试从信号文件获取话题
        possible_signals = [
            os.path.join(os.path.dirname(transcript_file), f'{episode_id}_signals.json'),
            os.path.join(os.path.dirname(transcript_file), f'{episode_id}_verified_signals.json'),
        ]
        for sf in possible_signals:
            if os.path.exists(sf):
                topics = extract_topics_from_signals(sf)
                break

    # 如果没有可分析的嘉宾发言
    if not guest_speeches:
        # 检查是否有任何非 Unknown 的说话人
        all_segments_unknown = all(
            seg.get('speaker', 'Unknown') == 'Unknown'
            for seg in transcript.get('segments', [])
        )

        if all_segments_unknown:
            print("   ⚠️ 说话人未识别（全部为 Unknown）")
            print("   💡 提示: 配置 HUGGINGFACE_TOKEN 并重新运行 step1 启用声纹识别")
            print("   跳过嘉宾画像分析...")
            return None
        else:
            print("   ⚠️ 嘉宾发言提取失败，但有说话人标签")
            print("   可能原因: speaker 标签与 participants 不匹配")

    # 只分析有足够发言的嘉宾
    speakers_to_analyze = [s for s in guest_speeches.keys() if s not in hosts]

    for guest_name in speakers_to_analyze:
        speeches = guest_speeches.get(guest_name, [])

        if len(speeches) < 3:
            print(f"   ⏭️ {guest_name}: 发言太少（{len(speeches)} 段），跳过")
            continue

        print(f"   → 分析: {guest_name} ({len(speeches)} 段发言)...")

        # 获取已知背景（尝试多种匹配方式）
        known_background = participants.get('guest_background', {}).get(guest_name, {})

        # 如果没找到，尝试模糊匹配
        if not known_background:
            for bg_name, bg_info in participants.get('guest_background', {}).items():
                if bg_name.lower() in guest_name.lower() or guest_name.lower() in bg_name.lower():
                    known_background = bg_info
                    print(f"      ✓ 匹配背景: {bg_name}")
                    break

        # 搜索更多背景资料
        print(f"      📡 搜索嘉宾背景...")
        background = generate_guest_background(guest_name, known_background, client)

        # 分析画像（结合背景和发言）
        profile = analyze_guest_profile(guest_name, speeches, background, client)

        if profile:
            # 把背景资料也加入画像
            profile['background'] = background
            profiles[guest_name] = profile

            print(f"      风格: {profile.get('investment_style', {}).get('primary_type', 'N/A')}")
            print(f"      风险: {profile.get('risk_preference', {}).get('level', 'N/A')}")

            # 更新数据库
            guest_id = normalize_guest_id(guest_name)
            update_guest_in_db(db, guest_id, guest_name, profile, episode_id or 'unknown', topics, background)

    # 保存数据库
    save_guests_db(db)
    print(f"\n💾 更新嘉宾数据库: {GUESTS_DB_FILE}")

    # 保存本集画像
    result = {
        'episode': episode_id,
        'guests': profiles,
        'participants': participants
    }

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 保存画像: {output_file}")

    print(f"\n✅ 分析完成！")
    print(f"   分析嘉宾: {len(profiles)} 位")
    print(f"   数据库总嘉宾: {len(db['guests'])} 位")

    return result


def main():
    if len(sys.argv) < 3:
        print("用法: python step2b_analyze_guests.py <transcript_speakers.json> <participants.json> [output.json] [episode_id]")
        print("")
        print("示例:")
        print("  python step2b_analyze_guests.py transcript_speakers.json participants.json")
        print("  python step2b_analyze_guests.py transcript_speakers.json participants.json guest_profiles.json sv101_ep233")
        sys.exit(1)

    transcript_file = sys.argv[1]
    participants_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    episode_id = sys.argv[4] if len(sys.argv) > 4 else None

    # 尝试从文件名提取 episode_id
    if not episode_id:
        import re
        match = re.search(r'(sv101_ep\d+|ep\d+)', transcript_file)
        if match:
            episode_id = match.group(1)

    analyze_guests(transcript_file, participants_file, output_file, episode_id)


if __name__ == "__main__":
    main()
