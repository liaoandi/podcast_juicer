#!/usr/bin/env python3
"""
说话人识别（使用 Gemini 3 Pro 长上下文）

策略：
1. 使用 Whisper 转录（无说话人标记）
2. 用 Gemini 3 Pro 分析完整对话，识别 host/guest
3. 利用 2M tokens 上下文，一次性处理整个播客
4. 映射到真实姓名

优势：
- 利用 Gemini 3 Pro 超长上下文（2M tokens）
- 看到完整对话，说话人识别更一致
- 比分批处理准确度更高（90-95%）

使用方法：
    python step2_identify_speakers.py <transcript_json> <participants_json>
"""

import json
import os
import sys
from google.genai import types
from gemini_utils import get_gemini_client, get_project_id, ensure_credentials, DEFAULT_MODEL

# 配置 — 说话人识别用 flash 模型（速度快，分类任务不需要 thinking）
LOCATION = "us-central1"
GEMINI_MODEL = "gemini-2.5-flash"

class GeminiSpeakerIdentifier:
    def __init__(self, project_id=None, location=None, model=None):
        """初始化 Vertex AI 客户端"""
        # 设置凭证
        ensure_credentials(verbose=True)
        self.project_id = project_id or get_project_id()
        self.location = location or LOCATION
        self.model_name = model or GEMINI_MODEL

        print(f"🔧 初始化 Vertex AI: {self.model_name} @ {self.location} ({self.project_id})")

        # 初始化客户端（添加超时保护）
        self.client = get_gemini_client(
            project_id=self.project_id,
            location=self.location,
            timeout=600
        )

    def check_has_diarization(self, segments):
        """
        检查 segments 是否已有 pyannote 声纹分离结果

        pyannote 输出格式: SPEAKER_00, SPEAKER_01 等
        """
        speaker_set = set()
        for seg in segments:
            speaker = seg.get('speaker', 'Unknown')
            if speaker and speaker != 'Unknown':
                speaker_set.add(speaker)

        # 如果有多个不同的 speaker 标签，说明有声纹分离
        has_diarization = len(speaker_set) > 1
        return has_diarization, speaker_set

    def group_by_speaker(self, segments):
        """
        按 speaker 分组 segments，提取每个 speaker 的样本发言
        """
        groups = {}
        for i, seg in enumerate(segments):
            speaker = seg.get('speaker', 'Unknown')
            if speaker not in groups:
                groups[speaker] = {
                    'indices': [],
                    'samples': [],
                    'total_chars': 0
                }
            groups[speaker]['indices'].append(i)
            groups[speaker]['total_chars'] += len(seg.get('text', ''))

            # 收集样本（前10条 + 中间5条 + 后5条，每条不超过200字）
            sample_count = len(groups[speaker]['samples'])
            if sample_count < 10 or (sample_count < 15 and i > len(segments) // 2):
                text = seg.get('text', '')[:200]
                groups[speaker]['samples'].append({
                    'index': i,
                    'time': seg.get('start', ''),
                    'text': text
                })

        return groups

    def build_mapping_prompt(self, speaker_groups, participants):
        """
        构建身份映射 prompt（用于有声纹分离的情况）

        Gemini 只需要把 SPEAKER_00/01/02 映射到真实姓名
        """
        hosts = participants.get('host', [])
        guests = participants.get('guests', [])
        guest_background = participants.get('guest_background', {})
        episode_info = participants.get('episode_info', '')

        # 构建参与者信息
        participants_info = f"""
节目信息: {episode_info}
主持人: {', '.join(hosts) if hosts else '未知'}
嘉宾: {', '.join(guests) if guests else '未知'}
"""
        if guest_background:
            participants_info += "\n嘉宾背景:\n"
            for name, bg in guest_background.items():
                participants_info += f"  - {name}: {bg}\n"

        # 构建每个 speaker 的样本
        speaker_samples = ""
        for speaker_id, data in sorted(speaker_groups.items()):
            speaker_samples += f"\n### {speaker_id} ({len(data['indices'])} 段发言，共 {data['total_chars']} 字)\n"
            speaker_samples += "样本发言:\n"
            for sample in data['samples'][:10]:  # 最多10条样本
                speaker_samples += f"  [{sample['time']}] {sample['text']}\n"

        prompt = f"""你是播客对话分析专家。音频已经通过声纹识别（pyannote）区分了不同说话人。

你的任务：将声纹标签（如 SPEAKER_00）映射到真实姓名。

{participants_info}

以下是每个声纹标签的样本发言：
{speaker_samples}

识别规则：
1. **主持人特征**：提问、引导话题、介绍嘉宾、话语较短
2. **嘉宾特征**：回答问题、深度分析、专业见解、话语较长
3. **关键线索**：
   - "我是XXX"、"大家好，我是..."
   - "XXX你觉得呢？"、"请XXX来说说"
   - 专业背景匹配（如金融背景的人谈估值）

输出 JSON：
{{
  "speaker_mapping": {{
    "SPEAKER_00": {{"name": "泓君", "role": "host", "confidence": "high"}},
    "SPEAKER_01": {{"name": "嘉宾A", "role": "guest", "confidence": "medium"}},
    "SPEAKER_02": {{"name": "嘉宾B", "role": "guest", "confidence": "high"}}
  }},
  "reasoning": "判断依据（2-3句话）"
}}

注意：
- 如果能确定真实姓名就用真实姓名
- 如果无法确定具体是哪位嘉宾，用"嘉宾A"、"嘉宾B"区分
- confidence: high（有明确证据）/ medium（推断）/ low（猜测）
"""
        return prompt

    def build_speaker_prompt(self, segments, participants):
        """构建说话人识别 prompt（用于没有声纹分离的情况）"""
        # 构建对话文本
        dialogue = []
        for i, seg in enumerate(segments):
            dialogue.append(f"[{i}] {seg['start']} {seg['text']}")

        dialogue_text = '\n'.join(dialogue)

        # 构建参与者信息
        hosts = participants.get('host', [])
        guests = participants.get('guests', [])
        episode_info = participants.get('episode_info', '')

        participants_str = f"""
主持人: {', '.join(hosts) if hosts else '未知'}
嘉宾: {', '.join(guests) if guests else '未知'}
节目信息: {episode_info}
"""

        prompt = f"""你是播客对话分析专家，擅长识别不同说话人。

参与者信息：
{participants_str}

任务：为以下完整播客对话的每一句标注说话人

识别规则（重要）：
1. **主持人特征**：
   - 提问、引导话题（"我们来聊聊..."、"接下来..."）
   - 话语较短，主要是提问和过渡
   - 介绍嘉宾、总结观点
   - 可能有多个主持人（共同主持）

2. **嘉宾特征**：
   - 回答问题，提供深度分析
   - 话语较长，有专业见解
   - 使用"我觉得..."、"从我们的角度..."
   - 可能有多个嘉宾（不同专业背景）

3. **区分不同说话人**：
   - 说话风格（正式/随意、技术/投资）
   - 观点角度（乐观/悲观、看多/看空）
   - 专业领域（AI/芯片/金融）
   - 自我介绍和被称呼的名字

4. **利用上下文**：
   - "我是XXX"、"XXX，你觉得呢？"
   - 连续的对话通常是同一人
   - 观点的连贯性
   - **你可以看到完整对话，充分利用前后文信息**

输出 JSON 格式：
{{
  "speaker_labels": [
    {{"index": 0, "speaker": "陈茜", "role": "host", "confidence": "high"}},
    {{"index": 1, "speaker": "Bruce Liu", "role": "guest", "confidence": "high"}},
    {{"index": 2, "speaker": "陈茜", "role": "host", "confidence": "high"}}
  ],
  "reasoning": "简要说明判断依据（2-3 句话）"
}}

注意：
- 如果无法确定具体是谁，可以用"主持人1"、"嘉宾A"等
- confidence: high/medium/low（根据判断的把握程度）
- 必须为所有 {len(segments)} 段对话标注说话人
- 严格输出 JSON，不要添加其他说明

对话内容：
{dialogue_text}
"""
        return prompt

    def build_speaker_prompt_for_chunk(self, chunk, participants, known_speakers=None, chunk_note=None):
        """
        构建分块识别 prompt

        chunk: List[Tuple[global_index, segment]]
        known_speakers: Dict[str, str] -> example text
        """
        dialogue = []
        for idx, seg in chunk:
            dialogue.append(f"[{idx}] {seg['start']} {seg['text']}")
        dialogue_text = "\n".join(dialogue)

        hosts = participants.get("host", [])
        guests = participants.get("guests", [])
        episode_info = participants.get("episode_info", "")

        participants_str = f"""
主持人: {', '.join(hosts) if hosts else '未知'}
嘉宾: {', '.join(guests) if guests else '未知'}
节目信息: {episode_info}
"""

        known_str = ""
        if known_speakers:
            known_str = "已识别说话人示例（保持命名一致）：\n"
            for name, sample in known_speakers.items():
                known_str += f"- {name}: {sample}\n"

        note_str = f"\n分块提示：{chunk_note}\n" if chunk_note else ""

        prompt = f"""你是播客对话分析专家，擅长识别不同说话人。

参与者信息：
{participants_str}

{known_str}{note_str}

任务：为以下对话片段的每一句标注说话人（只标注下面给出的索引）

识别规则（重要）：
1. **主持人特征**：
   - 提问、引导话题（"我们来聊聊..."、"接下来..."）
   - 话语较短，主要是提问和过渡
   - 介绍嘉宾、总结观点
   - 可能有多个主持人（共同主持）

2. **嘉宾特征**：
   - 回答问题，提供深度分析
   - 话语较长，有专业见解
   - 使用"我觉得..."、"从我们的角度..."
   - 可能有多个嘉宾（不同专业背景）

3. **区分不同说话人**：
   - 说话风格（正式/随意、技术/投资）
   - 观点角度（乐观/悲观、看多/看空）
   - 专业领域（AI/芯片/金融）
   - 自我介绍和被称呼的名字

4. **利用上下文**：
   - "我是XXX"、"XXX，你觉得呢？"
   - 连续的对话通常是同一人
   - 观点的连贯性

输出 JSON 格式：
{{
  "speaker_labels": [
    {{"index": 0, "speaker": "陈茜", "role": "host", "confidence": "high"}},
    {{"index": 1, "speaker": "Bruce Liu", "role": "guest", "confidence": "high"}}
  ],
  "reasoning": "简要说明判断依据（2-3 句话）"
}}

注意：
- index 必须等于方括号中的数字
- 如果无法确定具体是谁，可以用"主持人1"、"嘉宾A"等
- confidence: high/medium/low
- 必须为本片段中的所有索引标注说话人
- 严格输出 JSON，不要添加其他说明

对话内容：
{dialogue_text}
"""
        return prompt

    def identify_speakers_chunked(self, segments, participants, chunk_size=200, max_chars=40000):
        """
        分块识别说话人，避免超长输出被截断
        """
        label_by_index = {}
        known_speakers = {}
        total_segments = len(segments)
        idx = 0

        def _update_known_speakers(labels):
            for label in labels:
                name = label.get("speaker")
                i = label.get("index")
                if isinstance(i, str) and i.isdigit():
                    i = int(i)
                if name and i is not None and name not in known_speakers and i < len(segments):
                    sample_text = segments[i].get("text", "")[:80]
                    if sample_text:
                        known_speakers[name] = sample_text

        while idx < total_segments:
            attempt_size = chunk_size
            result = None
            chunk = []
            end = idx
            char_count = 0

            while True:
                # 组装分块
                chunk = []
                char_count = 0
                end = idx
                while end < total_segments and len(chunk) < attempt_size:
                    seg_text = segments[end].get("text", "")
                    if chunk and char_count + len(seg_text) > max_chars:
                        break
                    chunk.append((end, segments[end]))
                    char_count += len(seg_text)
                    end += 1

                if end == idx:
                    # 单段超长，仍需处理
                    chunk.append((idx, segments[idx]))
                    end = idx + 1

                chunk_note = f"这是第 {idx + 1}-{end} 段（共 {total_segments} 段）"
                prompt = self.build_speaker_prompt_for_chunk(
                    chunk,
                    participants,
                    known_speakers=known_speakers,
                    chunk_note=chunk_note
                )

                print(f"   调用 Gemini 3 Pro（分块 {idx + 1}-{end}，{len(chunk)} 段，约 {char_count} 字）...")

                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=65536,
                            temperature=0.1
                        )
                    )
                    result = self._clean_json(response.text)
                except Exception as e:
                    print(f"   ⚠️ Gemini 分块调用失败: {e}")
                    import traceback
                    traceback.print_exc()

                if result and "speaker_labels" in result:
                    break

                if attempt_size <= 200:
                    print(f"   ⚠️ 分块失败，返回已收集的 {len(label_by_index)} 个标签")
                    break

                attempt_size = max(200, attempt_size // 2)
                print(f"   ⚠️ 分块结果为空，缩小分块重试为 {attempt_size} 段...")

            if result is None:
                break

            labels = result.get("speaker_labels", [])
            for label in labels:
                if "index" in label:
                    idx_val = label.get("index")
                    if isinstance(idx_val, str) and idx_val.isdigit():
                        idx_val = int(idx_val)
                    if idx_val is not None:
                        label_by_index[idx_val] = label

            _update_known_speakers(labels)

            idx = end

        # 输出排序后的 labels
        merged_labels = [label_by_index[i] for i in sorted(label_by_index.keys())]
        return {
            "speaker_labels": merged_labels,
            "reasoning": "分块识别完成"
        }

    def identify_speakers(self, segments, participants):
        """一次性识别所有说话人（无声纹分离时使用）"""
        prompt = self.build_speaker_prompt(segments, participants)

        try:
            print(f"   调用 Gemini 3 Pro（处理 {len(segments)} 段，约 {sum(len(s['text']) for s in segments)} 字）...")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65536,  # 增加输出限制到最大值
                    temperature=0.1  # 降低随机性，提高 JSON 格式稳定性
                )
            )

            # 解析 JSON
            result = self._clean_json(response.text)

            if result and 'speaker_labels' in result:
                return result
            else:
                return None

        except Exception as e:
            print(f"   ⚠️ Gemini 调用失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def map_speakers(self, segments, participants):
        """
        映射声纹标签到真实姓名（有声纹分离时使用）

        这个方法效率更高，因为：
        1. 不需要为每段话做判断
        2. 利用已有的声纹分组
        3. Gemini 只需要分析样本并做映射
        """
        # 按 speaker 分组
        speaker_groups = self.group_by_speaker(segments)

        print(f"   检测到 {len(speaker_groups)} 个声纹分组:")
        for speaker_id, data in sorted(speaker_groups.items()):
            print(f"      {speaker_id}: {len(data['indices'])} 段，{data['total_chars']} 字")

        # 构建映射 prompt
        prompt = self.build_mapping_prompt(speaker_groups, participants)

        try:
            print(f"\n   调用 Gemini 3 Pro 进行身份映射...")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65536,
                    temperature=0.1
                )
            )

            result = self._clean_json(response.text)

            if result and 'speaker_mapping' in result:
                mapping = result['speaker_mapping']

                print(f"\n   身份映射结果:")
                for speaker_id, info in mapping.items():
                    name = info.get('name', speaker_id)
                    role = info.get('role', 'unknown')
                    confidence = info.get('confidence', 'low')
                    print(f"      {speaker_id} → {name} ({role}, {confidence})")

                if 'reasoning' in result:
                    print(f"\n   推理依据: {result['reasoning']}")

                # 转换为 speaker_labels 格式（兼容后续处理）
                speaker_labels = []
                for i, seg in enumerate(segments):
                    original_speaker = seg.get('speaker', 'Unknown')
                    if original_speaker in mapping:
                        info = mapping[original_speaker]
                        speaker_labels.append({
                            'index': i,
                            'speaker': info.get('name', original_speaker),
                            'role': info.get('role', 'unknown'),
                            'confidence': info.get('confidence', 'medium'),
                            'original_speaker': original_speaker  # 保留原始声纹标签
                        })
                    else:
                        speaker_labels.append({
                            'index': i,
                            'speaker': original_speaker,
                            'role': 'unknown',
                            'confidence': 'low',
                            'original_speaker': original_speaker
                        })

                return {
                    'speaker_labels': speaker_labels,
                    'speaker_mapping': mapping,
                    'reasoning': result.get('reasoning', '')
                }
            else:
                print(f"   ⚠️ 映射失败，返回原始标签")
                return None

        except Exception as e:
            print(f"   ⚠️ Gemini 调用失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _clean_json(text):
        """清理和解析 JSON"""
        if not text:
            return None
        try:
            cleaned = text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 解析错误: {e}")
            print(f"   响应长度: {len(text)} 字符")
            print(f"   原始文本开头: {text[:200]}...")
            print(f"   原始文本结尾: ...{text[-200:]}")

            # 尝试修复常见的 JSON 截断问题
            try:
                # 如果是数组被截断，尝试手动补全
                if '"speaker_labels": [' in cleaned and not cleaned.rstrip().endswith(']'):
                    print("   尝试修复截断的 JSON 数组...")
                    # 找到最后一个完整的对象
                    last_complete = cleaned.rfind('"}')
                    if last_complete > 0:
                        fixed = cleaned[:last_complete+2] + '], "reasoning": "响应被截断"}'
                        return json.loads(fixed)
            except Exception:
                pass

            return None

def identify_speakers_with_gemini(transcript_file, participants_file, output_file):
    """
    使用 Gemini 3 Pro 识别说话人

    两种模式：
    1. 有声纹分离（pyannote）：映射 SPEAKER_00/01 到真实姓名（高效）
    2. 无声纹分离：逐段分析识别说话人（慢但完整）

    Args:
        transcript_file: 输入转录 JSON
        participants_file: 参与者信息 JSON
        output_file: 输出转录 JSON（带说话人标记）
    """
    print(f"📖 读取转录: {transcript_file}")
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    print(f"📖 读取参与者信息: {participants_file}")
    with open(participants_file, 'r', encoding='utf-8') as f:
        participants = json.load(f)

    segments = transcript['segments']
    print(f"   总片段数: {len(segments)}")
    print(f"   总字符数: {sum(len(s['text']) for s in segments)}")

    # 初始化 Gemini
    identifier = GeminiSpeakerIdentifier()
    print("   ✓ 连接成功\n")

    # 检查是否已有声纹分离结果
    has_diarization, speaker_set = identifier.check_has_diarization(segments)

    if has_diarization:
        # 模式 1: 有声纹分离，只需要映射身份
        print(f"✓ 检测到声纹分离结果: {speaker_set}")
        print(f"🤖 使用 Gemini 3 Pro 进行身份映射（高效模式）...")
        result = identifier.map_speakers(segments, participants)
    else:
        # 模式 2: 无声纹分离，需要逐段识别
        print(f"⚠️  未检测到声纹分离结果（所有 speaker 为 Unknown）")
        print(f"   提示：配置 HUGGINGFACE_TOKEN 启用 pyannote 声纹识别可提高准确度")
        print(f"🤖 使用 Gemini 3 Pro 逐段识别说话人（完整模式）...")

        # 对于超长对话（>800段），分批处理避免输出被截断
        if len(segments) > 800:
            print(f"⚠️  对话过长（{len(segments)} 段），将分批处理以避免 JSON 截断...")
            result = identifier.identify_speakers_chunked(segments, participants)
        else:
            result = identifier.identify_speakers(segments, participants)

    if result and 'speaker_labels' in result:
        labels = result['speaker_labels']
        print(f"   ✓ 识别 {len(labels)} 段")

        # 应用标签到 segments
        applied_count = 0
        for label in labels:
            idx = label.get('index', None)
            if idx is None:
                # 尝试其他可能的字段名
                idx = label.get('seg_id', label.get('id', None))

            if idx is not None and idx < len(segments):
                segments[idx]['speaker'] = label.get('speaker', 'Unknown')
                segments[idx]['speaker_role'] = label.get('role', 'unknown')
                segments[idx]['speaker_confidence'] = label.get('confidence', 'medium')
                applied_count += 1

        print(f"   实际应用了 {applied_count} 个标签到 segments")

        # 对于没有标注的段落，标记为 Unknown
        for i, seg in enumerate(segments):
            if 'speaker' not in seg:
                seg['speaker'] = 'Unknown'
                seg['speaker_role'] = 'unknown'
                seg['speaker_confidence'] = 'low'

        # 显示推理依据
        if 'reasoning' in result:
            print(f"\n   推理依据: {result['reasoning']}")
    else:
        print("   ✗ 识别失败，所有段落标记为 Unknown")
        for seg in segments:
            seg['speaker'] = 'Unknown'
            seg['speaker_role'] = 'unknown'
            seg['speaker_confidence'] = 'low'
        print("   ❌ 说话人识别完全失败，退出")
        sys.exit(1)

    # 统计说话人
    speaker_stats = {}
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        speaker_stats[speaker] = speaker_stats.get(speaker, 0) + 1

    print(f"\n📊 说话人分布:")
    for speaker, count in sorted(speaker_stats.items(), key=lambda x: -x[1]):
        print(f"   {speaker}: {count} 段")

    # 保存结果
    output = {
        'language': transcript.get('language', 'zh'),
        'segments': segments,
        'metadata': {
            'method': 'gemini_3_pro_mapping' if has_diarization else 'gemini_3_pro_full_context',
            'model': GEMINI_MODEL,
            'has_diarization': has_diarization,
            'context_length': sum(len(s['text']) for s in segments),
            'chunked': (not has_diarization and len(segments) > 800)
        }
    }

    # 如果有身份映射，保存映射关系
    if result and 'speaker_mapping' in result:
        output['speaker_mapping'] = result['speaker_mapping']

    print(f"\n💾 保存结果: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   输出文件: {output_file}")
    print(f"   识别的说话人: {len(speaker_stats)} 位")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python step2_identify_speakers.py <transcript_json> <participants_json>")
        print("")
        print("示例:")
        print("  python step2_identify_speakers.py sv101_ep233_transcript.json participants.json")
        print("")
        print("participants.json 格式:")
        print("""
{
  "host": ["陈茜"],
  "guests": ["Bruce Liu", "Ren Yang"],
  "episode_info": "华尔街视角下的AI泡沫、芯片及黑天鹅"
}
        """)
        print("")
        print("需要:")
        print("  - Vertex AI Service Account Key")
        print("  - 已安装: pip install google-genai")
        sys.exit(1)

    transcript_file = sys.argv[1]
    participants_file = sys.argv[2]

    # 输出文件名：优先使用第3个参数，否则自动生成
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    else:
        base_name = os.path.splitext(transcript_file)[0]
        output_file = f"{base_name}_with_speakers.json"

    identify_speakers_with_gemini(transcript_file, participants_file, output_file)
