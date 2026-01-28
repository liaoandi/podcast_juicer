#!/usr/bin/env python3
"""
润色转录文本：添加标点符号 + 轻度书面化
使用 GPT-4o 进行智能润色（无硬编码规则）
"""

import re
import os
import sys
import json
from openai import AzureOpenAI

# 初始化 Azure OpenAI 客户端
client = None

def get_client():
    """获取或初始化 Azure OpenAI 客户端"""
    global client
    if client is None:
        api_key = os.environ.get('AZURE_OPENAI_API_KEY')

        # 如果环境变量没有，尝试从 .env 文件读取
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
            max_retries=1,
            timeout=60.0,
        )
    return client

def polish_with_llm(text, max_retries=3):
    """
    使用 GPT-4o 添加标点符号和轻度书面化

    Args:
        text: 待润色的文本
        max_retries: 最大重试次数

    Returns:
        润色后的文本
    """
    system_prompt = """你是专业的播客转录润色专家，负责为转录添加标点并轻度书面化。

任务：添加标点、适当断句、删除口头禅

**关键要求**：
1. 添加标点符号（逗号、句号、问号等），适当断句

2. 轻度书面化（删除明显口头禅）：
   - 删除纯填充词："就是说"、"那个"、"这个"（当作填充词时）、"怎么讲"、"说白了"
   - 删除语气词："啊"、"呀"、句末的"吧"、"呢"
   - 简化连接词："然后" 可适当删除或改为句号

3. **必须保留概率词和观点表达**（这些是分析的核心）：
   - 保留："我觉得"、"我认为"、"我会觉得"
   - 保留："相对来说"、"比较"、"一定程度上"、"可能"、"大概"、"应该"
   - 保留："有点"、"略微"、"稍微"
   - 这些词表达了说话人的不确定性判断，必须保留

4. 适当断句：
   - 长句（>50字）拆分为短句
   - 用句号代替过多的逗号

5. 保持核心信息完整：
   - 所有数字、数据必须保留（如：14 倍、27 倍、90%）
   - 核心观点和逻辑不变
   - 专业术语和生动比喻保留

6. 数字和英文专有名词后加空格

7. 直接输出润色后的文本，不要解释

示例：
输入：我会觉得其实Google其实是对我来说一个被市场教育的过程吧因为我们相对来说一直都比较对Google偏悲观
输出：我会觉得 Google 对我来说是一个被市场教育的过程，因为我们相对来说一直都比较对 Google 偏悲观。"""

    for attempt in range(max_retries):
        try:
            response = get_client().chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # 降低随机性，保持一致性
                max_tokens=2000
            )

            polished = response.choices[0].message.content.strip()

            # 清理可能的说明性文字（如果 LLM 没遵守指令）
            if polished.startswith('润色后') or polished.startswith('以下是'):
                lines = polished.split('\n')
                polished = '\n'.join([l for l in lines if l and not l.startswith(('润色', '以下', '原文'))])

            return polished

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️ API 调用失败，使用原文: {e}")
                return text
            print(f"⚠️ API 调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
            continue

    return text

def merge_segments_for_polishing(segments, merge_count=8):
    """
    将相邻 segments 合并成段落

    Args:
        segments: 原始 segments 列表
        merge_count: 每几个 segments 合并一次

    Returns:
        合并后的段落列表
    """
    merged = []
    for i in range(0, len(segments), merge_count):
        chunk = segments[i:i + merge_count]

        # 合并文本
        combined_text = ''.join([seg['text'].strip() for seg in chunk])

        # 保留说话人信息（取 chunk 中最常见的 speaker，或第一个）
        speakers = [seg.get('speaker', 'Unknown') for seg in chunk]
        # 如果所有 speaker 相同，使用该 speaker；否则使用第一个
        unique_speakers = list(set(speakers))
        if len(unique_speakers) == 1:
            speaker = unique_speakers[0]
        else:
            # 如果有多个说话人，取第一个（或者可以标记为 "Multiple"）
            speaker = speakers[0]

        merged.append({
            'id': len(merged),
            'start': chunk[0]['start'],
            'end': chunk[-1]['end'],
            'start_seconds': chunk[0]['start_seconds'],
            'end_seconds': chunk[-1]['end_seconds'],
            'text': combined_text,
            'speaker': speaker,
            'original_ids': [seg['id'] for seg in chunk]  # 保留原始 ID
        })

    return merged

def polish_full_transcript(input_file, output_file, merge_count=8):
    """
    润色整个转录文件（完整流程）

    Args:
        input_file: 输入的原始 JSON 文件
        output_file: 输出的润色后 JSON 文件
        merge_count: 每几个 segments 合并一次
    """
    print(f"📖 读取原始转录: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    segments = transcript['segments']
    print(f"   总片段数: {len(segments)}")

    # 合并 segments
    print(f"\n🔗 合并 segments (每 {merge_count} 个合并)")
    merged = merge_segments_for_polishing(segments, merge_count)
    print(f"   合并后段落数: {len(merged)}")

    # 润色每个段落
    print(f"\n✨ 开始润色 (调用 GPT-4o)...")
    polished_segments = []

    for i, seg in enumerate(merged, 1):
        print(f"   [{i}/{len(merged)}] {seg['start']} - {seg['end']} ({len(seg['text'])} 字)", end=' ')

        try:
            # 去除多余空格
            text = re.sub(r'\s+', '', seg['text'])

            # 调用 GPT-4o 润色
            polished_text = polish_with_llm(text)

            polished_segments.append({
                'id': seg['id'],
                'start': seg['start'],
                'end': seg['end'],
                'start_seconds': seg['start_seconds'],
                'end_seconds': seg['end_seconds'],
                'text': polished_text,
                'speaker': seg['speaker']
            })

            print(f"✓ ({len(polished_text)} 字)")

        except Exception as e:
            print(f"✗ 失败: {e}")
            # 失败时保留原文
            polished_segments.append({
                'id': seg['id'],
                'start': seg['start'],
                'end': seg['end'],
                'start_seconds': seg['start_seconds'],
                'end_seconds': seg['end_seconds'],
                'text': seg['text'],
                'speaker': seg['speaker']
            })

    # 保存润色后的 JSON
    output = {
        'language': transcript['language'],
        'segments': polished_segments
    }

    print(f"\n💾 保存润色后文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   原始片段: {len(segments)}")
    print(f"   润色段落: {len(polished_segments)}")
    print(f"   输出文件: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step3_polish_transcript.py <input_json> [output_json] [merge_count]")
        print("")
        print("参数:")
        print("  input_json   : 输入的转录 JSON 文件")
        print("  output_json  : 输出的润色后 JSON 文件（可选，默认为 input_polished.json）")
        print("  merge_count  : 每几个 segments 合并一次（可选，默认 8）")
        print("")
        print("示例:")
        print("  python step3_polish_transcript.py sv101_ep233_transcript_advanced.json")
        print("  python step3_polish_transcript.py input.json output.json 10")
        sys.exit(1)

    input_file = sys.argv[1]

    # 默认输出文件名
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = input_file.rsplit('.', 1)[0]
        output_file = f"{base_name}_polished.json"

    # 默认合并数量
    merge_count = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    polish_full_transcript(input_file, output_file, merge_count)
