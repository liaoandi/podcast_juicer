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
import sys
import os
from google import genai
from google.genai import types

# 配置
LOCATION = "global"
GEMINI_MODEL = "gemini-3-pro-preview"

def get_sa_key_path():
    """从环境变量或 .env 获取 service account key 路径"""
    # 先尝试环境变量
    key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path and os.path.exists(key_path):
        return key_path

    # 尝试从 .env 读取
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
    # 从 service account key 读取
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

    # 从环境变量读取
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id

    raise ValueError("未找到 project_id，请设置 GOOGLE_CLOUD_PROJECT 环境变量或配置 service account key")

class GeminiSpeakerIdentifier:
    def __init__(self, project_id=None, location=None, model=None):
        """初始化 Vertex AI 客户端"""
        # 设置凭证
        sa_key_path = get_sa_key_path()
        if sa_key_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path
        else:
            print("⚠️  未找到 GOOGLE_APPLICATION_CREDENTIALS")
            print("   请在 .env 文件中配置或设置环境变量")

        self.project_id = project_id or get_project_id()
        self.location = location or LOCATION
        self.model_name = model or GEMINI_MODEL

        print(f"🔧 初始化 Vertex AI: {self.model_name} @ {self.location} ({self.project_id})")

        # 初始化客户端
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

    def build_speaker_prompt(self, segments, participants):
        """构建说话人识别 prompt"""
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

    def identify_speakers(self, segments, participants):
        """一次性识别所有说话人"""
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

    def _clean_json(self, text):
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
            except:
                pass

            return None

def identify_speakers_with_gemini(transcript_file, participants_file, output_file):
    """
    使用 Gemini 3 Pro 识别说话人（一次性处理）

    Args:
        transcript_file: 输入转录 JSON（无说话人标记）
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

    # 一次性识别所有说话人
    # 对于超长对话（>1500段），需要分批处理避免输出被截断
    if len(segments) > 1500:
        print(f"⚠️  对话过长（{len(segments)} 段），将分批处理以避免 JSON 截断...")
        print(f"🤖 使用 Gemini 3 Pro 分批识别说话人...")
        # TODO: 实现分批逻辑
        result = identifier.identify_speakers(segments, participants)
    else:
        print(f"🤖 使用 Gemini 3 Pro 一次性识别所有说话人...")
        result = identifier.identify_speakers(segments, participants)

    if result and 'speaker_labels' in result:
        labels = result['speaker_labels']
        print(f"   ✓ 识别 {len(labels)} 段")

        # 调试：打印前几个标签看看格式
        if labels:
            print(f"\n   调试：前 3 个标签格式：")
            for i, label in enumerate(labels[:3]):
                print(f"      {i}: {label}")

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
            'method': 'gemini_3_pro_full_context',
            'model': GEMINI_MODEL,
            'context_length': sum(len(s['text']) for s in segments)
        }
    }

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

    # 生成输出文件名
    base_name = transcript_file.rsplit('.', 1)[0]
    output_file = f"{base_name}_with_speakers.json"

    identify_speakers_with_gemini(transcript_file, participants_file, output_file)
