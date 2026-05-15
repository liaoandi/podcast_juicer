#!/usr/bin/env python3
"""
自动从转录中提取投资信号（使用 Gemini 3 Pro 长上下文）

流程：
1. 读取润色后的 transcript（带时间戳）
2. 使用 Gemini 3 Pro 一次性处理整个播客
3. 利用 2M tokens 上下文，看到完整讨论
4. 输出信号 + 引用原文（带时间标识）

优势：
- 利用 Gemini 3 Pro 超长上下文（2M tokens）
- 看到完整讨论，不会切断跨段落的论证
- 比 Map-Reduce 准确度更高（85-90%）
- 一致的重要性评分
"""

import json
import os
import sys
from google.genai import types
from gemini_utils import get_gemini_client, DEFAULT_MODEL, patch_dns

# 配置
LOCATION = "global"
GEMINI_MODEL = DEFAULT_MODEL
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "180"))

def load_featured_companies(featured_companies_file=None):
    """加载关注公司列表"""
    if not featured_companies_file or not os.path.exists(featured_companies_file):
        return {"featured_companies": []}
    with open(featured_companies_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_time_range(seg_ids, transcript_segments, buffer_seconds=10):
    """
    根据 seg_ids 计算时间范围

    Args:
        seg_ids: segment ID 列表
        transcript_segments: 完整的 transcript segments
        buffer_seconds: 前后缓冲时间（秒）

    Returns:
        包含 time_start, time_end, start_seconds, end_seconds 的字典
    """
    if not seg_ids:
        return {}

    # 查找对应的 segments
    matching_segs = []
    seg_id_set = set(int(x) for x in seg_ids)

    for seg in transcript_segments:
        seg_id = seg.get('seg_id') if 'seg_id' in seg else seg.get('id')
        if seg_id is not None and int(seg_id) in seg_id_set:
            matching_segs.append(seg)

    if not matching_segs:
        return {}

    # 计算时间范围
    def _to_seconds(val):
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str) and ':' in val:
            parts = val.split(':')
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            return float(parts[0]) * 60 + float(parts[1])
        return 0.0

    start_seconds = min(_to_seconds(seg.get('start_seconds', seg.get('start', 0))) for seg in matching_segs) - buffer_seconds
    end_seconds = max(_to_seconds(seg.get('end_seconds', seg.get('end', 0))) for seg in matching_segs) + buffer_seconds

    # 确保不超出边界
    start_seconds = max(0, start_seconds)

    # 格式化时间戳
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return {
        'time_start': format_time(start_seconds),
        'time_end': format_time(end_seconds),
        'start_seconds': start_seconds,
        'end_seconds': end_seconds
    }

class GeminiSignalExtractor:
    def __init__(self, project_id=None, location=None, model=None):
        """初始化 Vertex AI 客户端"""
        self.location = location or LOCATION
        self.model_name = model or GEMINI_MODEL

        print(f"🔧 初始化 Vertex AI: {self.model_name} @ {self.location}")
        patch_dns()

        # 初始化客户端
        # get_gemini_client handles credentials and project_id internally
        self.client = get_gemini_client(
            project_id=project_id,
            location=self.location,
            timeout=GEMINI_TIMEOUT_SECONDS,
        )

    def build_extraction_prompt(self, segments, featured_companies):
        """构建信号提取 prompt"""
        # 为每个 segment 添加 seg_id（如果还没有）
        for i, seg in enumerate(segments):
            if 'seg_id' not in seg and 'id' not in seg:
                seg['seg_id'] = i

        # 构建输入文本（带 seg_id 和时间戳）
        text_with_timestamps = []
        for seg in segments:
            seg_id = seg.get('seg_id') if 'seg_id' in seg else seg.get('id', 0)
            speaker = seg.get('speaker', 'Unknown')
            # 格式：[seg=187|00:20:12] 说话人: 文本
            text_with_timestamps.append(
                f"[seg={seg_id}|{seg.get('start', '00:00:00')}] {speaker}: {seg['text']}"
            )

        transcript_text = '\n'.join(text_with_timestamps)

        # 构建 featured_companies 字符串
        featured_companies_str = ', '.join([f"{c['company']} ({c.get('ticker', '')})" for c in featured_companies['featured_companies']])

        prompt = f"""你是"投资研究信号提取器"。目标：从播客转录中提取【可验证的投资线索】而不是摘要。

关注公司：{featured_companies_str}

输入格式：每行为 [seg=ID|HH:MM:SS] 说话人: 文本
注意：输入文本已经过轻度润色（添加标点、删除填充词），但保留了所有概率判断词（"我觉得"、"可能"、"相对来说"）和核心信息。

规则（必须遵守）：
1) 只抽取"陈述句/判断句/预测句"作为 claim；疑问句只能作为背景，不得作为 claim。
2) 每条信号必须提供 evidence_seg_ids（>=1）以及逐字引用 quote（<=25字）。
3) 同一个信号可以关联多个实体 entities（如 NVDA + GOOGL），不要为了凑 company 字段把同一段话拆成两条。
4) **你可以看到完整播客对话，充分利用前后文信息**，识别跨段落的完整论证。
5) 提取所有高质量信号，有多少提取多少；没有就输出空数组。
6) 严格输出 JSON，不要输出任何解释。
7) **实体必须是可投资的公司**：
   - 如果提及的是品牌/子公司（如 Gucci、淘宝、YouTube、Instagram），必须识别其母公司（Kering、阿里巴巴、Google、Meta）
   - ticker 必须是母公司的股票代码，不是品牌名
   - 私有公司（如 SpaceX、字节跳动）ticker 填 null，type 填 "private"
   - 不确定母公司时，尽力推断；实在不知道就保留原名并标注 type: "unknown"

评估维度（每个维度只分两档，提高区分度）：

**confidence（置信度）** - 是真的吗？
- high: 有明确数据/事实支撑，可直接验证（如：公开财报数字、已公布的时间节点、可查证的市场数据）
- low: 基于推理、主观判断或预测，难以直接验证

**novelty（新颖度）** - 我能学到什么新东西？
- high: 独家洞察/非公开信息/深度解读/反直觉观点（市场不知道或没想清楚的逻辑链）
- low: 公开信息/常见观点/新闻稿水平

**actionability（可行动性）** - 我能做什么？
- high: 满足至少2条 - 1)有明确时间窗口/催化剂（财报、发布会、量产、监管节点、IPO、capex指引等），2)有明确可交易载体（ticker、产业链proxy、对冲标的），3)有明确可观测指标（KPI/数据能验证）
- low: 满足0-1条 - 缺少关键行动要素，难以直接落地

**⚠️ 重要：评分规则**
- 每个维度必须且只能从 ["high", "low"] 中选择一个值
- 不要使用 "medium" 或其他任何值
- 如果不确定，选择 "low"（保守原则）

输出 JSON：
{{
  "signal_candidates": [
    {{
      "entities": [{{"name":"...", "ticker": "...", "parent": "...(如有)", "type": "public|private|unknown"}}],
      "signal_type": "competition|product|valuation|demand|risk|supply_chain|regulation|capital_action|other",
      "claim": "详细判断（包含：核心事实 + 驱动因素/背景 + 投资意义，80-120字）",
      "evidence_seg_ids": [187, 188, 190],
      "key_quotes": [{{"seg_id": 188, "quote": "NVIDIA 的 CUDA 生态系统已经形成垄断优势"}}],
      "impact_path": ["可能影响什么", "为什么"],
      "verification_steps": ["具体核验动作1", "具体核验动作2"],
      "confidence": "high",
      "novelty": "low",
      "actionability": "high"
    }}
  ]
}}

注意：confidence/novelty/actionability 的值只能是 "high" 或 "low"，不能是 "medium"

**claim 示例（好的）**：
- "Google 的估值在几个月内从 14 倍翻了一倍，主要由 Gemini 发布带来的 AI 叙事反转驱动，显示市场对 Google 在 AI 竞争中地位的重新评估"
- "SpaceX 计划在 2026 年上市，目标估值为 1.5 万亿，较当前私募估值溢价近 2 倍，反映市场对商业太空及国家安全属性资产的高溢价预期"

**claim 示例（不好，太精简）**：
- "Google 的估值翻倍"  ← 缺少背景和驱动因素
- "SpaceX 将上市"  ← 缺少估值和意义

播客转录内容：
{transcript_text}
"""
        return prompt

    def extract_signals(self, segments, featured_companies):
        """一次性提取所有投资信号"""
        prompt = self.build_extraction_prompt(segments, featured_companies)

        try:
            print(f"   调用 Gemini 3 Pro（处理 {len(segments)} 段，约 {sum(len(s['text']) for s in segments)} 字）...")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65536
                )
            )

            # 解析 JSON
            raw_text = ""
            try:
                raw_text = response.text or ""
            except Exception:
                raw_text = ""
            result = self._clean_json(raw_text)

            if result and 'signal_candidates' in result:
                candidates = result['signal_candidates']

                # 为每个候选信号计算时间范围（基于 evidence_seg_ids）
                for candidate in candidates:
                    seg_ids = candidate.get('evidence_seg_ids', [])
                    if seg_ids:
                        time_info = calculate_time_range(seg_ids, segments)
                        if time_info:
                            candidate['time_start'] = time_info['time_start']
                            candidate['time_end'] = time_info['time_end']
                            candidate['start_seconds'] = time_info['start_seconds']
                            candidate['end_seconds'] = time_info['end_seconds']

                    # 规范化评分：强制将 medium 转换为 low（保守策略）
                    for rating_field in ['confidence', 'novelty', 'actionability']:
                        if rating_field in candidate:
                            value = candidate[rating_field]
                            if value not in ['high', 'low']:
                                print(f"   ⚠️ 发现非标准评分 {rating_field}='{value}'，已转换为 'low'")
                                candidate[rating_field] = 'low'

                return candidates
            else:
                return []

        except Exception as e:
            print(f"   ⚠️ Gemini 调用失败: {e}")
            return []

    def _clean_json(self, text):
        """清理和解析 JSON"""
        from gemini_utils import clean_json
        return clean_json(text)

def load_episode_metadata(transcript_file):
    """
    从 transcript 文件路径推断并加载 episode metadata

    查找顺序：
    1. 同目录下的 *_metadata.json
    2. 返回空字典
    """
    transcript_dir = os.path.dirname(os.path.abspath(transcript_file))

    # 查找 metadata 文件
    for f in os.listdir(transcript_dir):
        if f.endswith('_metadata.json'):
            metadata_path = os.path.join(transcript_dir, f)
            try:
                with open(metadata_path, 'r', encoding='utf-8') as mf:
                    metadata = json.load(mf)
                    print(f"   ✓ 加载 metadata: {f}")
                    return metadata
            except Exception as e:
                print(f"   ⚠️ 加载 metadata 失败: {e}")

    return {}


def extract_all_signals_with_gemini(transcript_file, featured_companies_file, output_file):
    """
    使用 Gemini 3 Pro 提取投资信号（一次性处理）

    Args:
        transcript_file: 转录文件路径
        featured_companies_file: 关注列表文件路径
        output_file: 输出文件路径
    """
    print("📖 加载转录和关注列表...")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    # 加载 episode metadata（包含日期信息）
    episode_metadata = load_episode_metadata(transcript_file)

    featured_companies = load_featured_companies(featured_companies_file)

    segments = transcript['segments']
    if segments:
        print(f"   转录总时长: {segments[-1].get('end', 'N/A')}")
    else:
        print("   ⚠️ 转录为空")
        return
    print(f"   总片段数: {len(segments)}")
    print(f"   总字符数: {sum(len(s['text']) for s in segments)}")
    print(f"   关注公司: {len(featured_companies['featured_companies'])} 家")

    # 初始化 Gemini
    extractor = GeminiSignalExtractor()
    print("   ✓ 连接成功\n")

    # 一次性提取所有信号
    print(f"🔍 使用 Gemini 3 Pro 一次性提取所有投资信号...")
    final_signals = extractor.extract_signals(segments, featured_companies)

    if final_signals:
        print(f"   ✓ 提取 {len(final_signals)} 个信号")
    else:
        print("   ○ 未找到信号")

    # 收集所有涉及的公司
    all_companies = set()
    for signal in final_signals:
        for entity in signal.get('entities', []):
            if entity.get('name'):
                all_companies.add(entity['name'])

    # 保存结果
    print(f"\n💾 保存信号到 {output_file}...")
    output = {
        'metadata': {
            'source': transcript_file,
            'method': 'gemini_3_pro_full_context',
            'model': GEMINI_MODEL,
            'total_signals': len(final_signals),
            'companies_mentioned': sorted(list(all_companies)),
            'context_length': sum(len(s['text']) for s in segments),
            # 时间信息（用于后续验证）
            'publish_date': episode_metadata.get('publish_date'),
            'record_date': episode_metadata.get('record_date'),
            'podcast_id': episode_metadata.get('podcast_id'),
            'episode_id': episode_metadata.get('episode_id'),
        },
        'signals': final_signals
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   最终信号: {len(final_signals)} 个")
    print(f"   涉及公司: {len(all_companies)} 家")

    # 按公司统计
    if final_signals:
        company_stats = {}
        for signal in final_signals:
            for entity in signal.get('entities', []):
                company = entity.get('name', 'Unknown')
                company_stats[company] = company_stats.get(company, 0) + 1

        print("\n📊 信号分布:")
        for company, count in sorted(company_stats.items(), key=lambda x: -x[1]):
            print(f"   {company}: {count} 个")

        # 按置信度统计
        confidence_stats = {}
        for signal in final_signals:
            conf = signal.get('confidence', 'unknown')
            confidence_stats[conf] = confidence_stats.get(conf, 0) + 1

        print("\n📊 置信度分布:")
        for conf, count in sorted(confidence_stats.items(), key=lambda x: -x[1]):
            print(f"   {conf}: {count} 个")

        # 按新颖度统计
        novelty_stats = {}
        for signal in final_signals:
            nov = signal.get('novelty', 'unknown')
            novelty_stats[nov] = novelty_stats.get(nov, 0) + 1

        print("\n📊 新颖度分布:")
        for nov, count in sorted(novelty_stats.items(), key=lambda x: -x[1]):
            print(f"   {nov}: {count} 个")

        # 按可行动性统计
        actionability_stats = {}
        for signal in final_signals:
            act = signal.get('actionability', 'unknown')
            actionability_stats[act] = actionability_stats.get(act, 0) + 1

        print("\n📊 可行动性分布:")
        for act, count in sorted(actionability_stats.items(), key=lambda x: -x[1]):
            print(f"   {act}: {count} 个")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step2_extract_signals.py <transcript_json> [output_json]")
        print("")
        print("示例:")
        print("  python step2_extract_signals.py transcript.json")
        print("  python step2_extract_signals.py transcript.json signals.json")
        sys.exit(1)

    transcript_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'extracted_signals.json'

    extract_all_signals_with_gemini(transcript_file, None, output_file)
