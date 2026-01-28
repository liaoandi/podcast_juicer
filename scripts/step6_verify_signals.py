#!/usr/bin/env python3
"""
使用 Vertex AI (Gemini 3 Pro) + Google Search 验证投资信号

基于 medical_ocr 的实现方式
"""

import json
import os
import sys
from datetime import datetime
from google import genai
from google.genai import types

# 配置（从环境变量读取）
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

class VertexVerifier:
    def __init__(self, project_id=None, location=None, model=None):
        """初始化 Vertex AI 客户端"""
        # 设置凭证
        sa_key_path = get_sa_key_path()
        if sa_key_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path
        else:
            print("⚠️  未找到 GOOGLE_APPLICATION_CREDENTIALS")
            print("   请在 .env 文件中配置或设置环境变量")
            print("   例如：GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")

        # 确定 Project ID
        if not project_id:
            # 尝试从 service account key 读取
            if sa_key_path and os.path.exists(sa_key_path):
                try:
                    with open(sa_key_path, 'r') as f:
                        data = json.load(f)
                        project_id = data.get('project_id')
                except:
                    pass

            # 从环境变量读取
            if not project_id:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

            # 最后的兜底
            if not project_id:
                raise ValueError("未找到 project_id，请设置 GOOGLE_CLOUD_PROJECT 环境变量")

        self.project_id = project_id
        self.location = location or LOCATION
        self.model_name = model or GEMINI_MODEL

        print(f"🔧 初始化 Vertex AI: {self.model_name} @ {self.location} ({self.project_id})")

        # 初始化客户端
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

    def build_verification_prompt(self, signal):
        """构建验证 prompt"""
        entities = signal.get('entities', [])
        entity_names = ', '.join([e['name'] for e in entities])
        claim = signal.get('claim', '')
        signal_type = signal.get('signal_type', 'unknown')

        prompt = f"""你是专业的投资研究分析师。请验证以下投资信号的真实性。

**待验证信号**
- 公司：{entity_names}
- 类型：{signal_type}
- 判断：{claim}
- 原始置信度：{signal.get('confidence', 'unknown')}

**验证任务**
使用 Google Search 搜索 2025-2026 年的最新信息：
1. 核查判断是否准确（是否有新闻/财报/数据支持）
2. 分析真实的影响路径（基于实际数据，不是推测）
3. 提供可追溯的信息来源（带 URL）

**输出格式**（严格 JSON，不要输出其他内容）
{{
  "verification_status": "verified|partially_verified|unverified|contradicted",
  "verified_claim": "修正后的判断（如果原判断有误，必须修正；如果准确，重复原判断）",
  "verified_impact_path": [
    "真实影响1（基于搜索到的具体数据）",
    "真实影响2（基于搜索到的具体数据）",
    "真实影响3（如果有）"
  ],
  "verified_data": [
    {{
      "source": "来源名称 + 日期（例：Bloomberg 2025-12-09）",
      "finding": "发现的具体事实（带数据）",
      "url": "链接（如果搜索到）"
    }},
    {{
      "source": "来源2",
      "finding": "事实2",
      "url": "链接2"
    }}
  ],
  "verification_confidence": "high|low",
  "verification_notes": "验证总结（标注哪些准确/不准确/未找到证据）"
}}

**⚠️ 重要：verification_confidence 评分规则**
- high: 找到多个权威来源证实，数据准确可靠
- low: 来源不足、数据不完整、或存在矛盾
- 必须且只能从 ["high", "low"] 中选择一个值，不要使用 "medium"

**重要规则**
- verified_impact_path 必须基于搜索到的真实数据，不能是空泛推测
- verified_data 至少提供 2 个来源
- 如果搜索不到相关信息，verification_status 应为 "unverified"
- 如果原判断与搜索结果矛盾，verification_status 应为 "contradicted"

**信源分类（source_type）**
- **primary**：一手信源（公司公告、监管文件、SEC filings、财报、官方博客）
- **tier1_media**：T1 权威媒体（WSJ, Bloomberg, Reuters, FT, Forbes, CNBC）
- **tier2_media**：T2 主流媒体（TechCrunch, The Verge, Business Insider, Nikkei）
- **company_filing**：监管披露（10-K, 8-K, S-1, proxy statements）
- **unknown**：来源不明或二手转述

**信源可信度评级（credibility）**
- **high**：primary 或 tier1_media，有明确作者和日期
- **medium**：tier2_media，或 tier1 但无明确日期
- **low**：unknown 或社交媒体/论坛转述
"""
        return prompt

    def verify_signal(self, signal):
        """验证单个信号"""
        prompt = self.build_verification_prompt(signal)

        try:
            # 调用 Gemini 3 Pro + Google Search
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    tools=[types.Tool(google_search=types.GoogleSearch())],  # 启用 Google Search
                    thinking_config=types.ThinkingConfig(thinking_budget=4096)  # 启用推理增强
                )
            )

            # 解析 JSON
            verification_data = self._clean_json(response.text)

            if verification_data:
                verification_data['verification_date'] = datetime.now().strftime('%Y-%m-%d')

                # 规范化 verification_confidence：强制将 medium 转换为 low（保守策略）
                if 'verification_confidence' in verification_data:
                    value = verification_data['verification_confidence']
                    if value not in ['high', 'low']:
                        print(f"   ⚠️ 发现非标准验证置信度 '{value}'，已转换为 'low'")
                        verification_data['verification_confidence'] = 'low'

                return verification_data
            else:
                return self._error_verification("JSON 解析失败")

        except Exception as e:
            return self._error_verification(str(e))

    def _clean_json(self, text):
        """清理和解析 JSON"""
        if not text:
            return None
        try:
            cleaned = text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 解析错误: {e}")
            print(f"   原始文本: {text[:200]}...")
            return None

    def _error_verification(self, error_msg):
        """生成错误验证结果"""
        return {
            'verification_status': 'error',
            'verification_date': datetime.now().strftime('%Y-%m-%d'),
            'verification_notes': f'验证失败: {error_msg}',
            'verified_claim': '',
            'verified_impact_path': [],
            'verified_data': [],
            'verification_confidence': 'low'
        }

def verify_all_signals(input_file, output_file, max_signals=None):
    """验证所有信号"""
    print(f"📖 读取信号: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    signals = data['signals']
    if max_signals:
        signals = signals[:max_signals]
        print(f"   只验证前 {max_signals} 个信号")

    print(f"   共 {len(signals)} 个信号需要验证\n")

    # 初始化 Vertex AI
    verifier = VertexVerifier()
    print("   ✓ 连接成功\n")

    verified_signals = []

    for i, signal in enumerate(signals, 1):
        entities = signal.get('entities', [])
        entity_names = ', '.join([e['name'] for e in entities])
        claim = signal.get('claim', '')

        print(f"🔍 [{i}/{len(signals)}] 验证中...")
        print(f"   公司: {entity_names}")
        print(f"   判断: {claim[:70]}...")

        # 调用验证
        verification = verifier.verify_signal(signal)

        # 添加验证结果
        signal['verification'] = verification

        # 显示结果
        status_map = {
            'verified': '✅ 已验证',
            'partially_verified': '⚠️ 部分验证',
            'unverified': '❌ 未验证',
            'contradicted': '❌ 与事实矛盾',
            'error': '⚠️ 验证出错'
        }
        status_text = status_map.get(verification.get('verification_status'), '未知')
        confidence = verification.get('verification_confidence', 'N/A')

        print(f"   结果: {status_text}")
        print(f"   置信度: {confidence}")

        # 显示验证备注
        if 'verification_notes' in verification:
            notes = verification['verification_notes']
            if notes and len(notes) < 100:
                print(f"   备注: {notes}")

        print()

        verified_signals.append(signal)

    # 保存结果
    output_data = {
        'metadata': {
            **data['metadata'],
            'verification_date': datetime.now().strftime('%Y-%m-%d'),
            'verification_method': 'vertex_ai_gemini_3_pro + google_search',
            'verification_status': 'completed',
            'verified_signals_count': len(verified_signals)
        },
        'signals': verified_signals
    }

    print(f"💾 保存验证结果: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 验证完成！")
    print(f"   验证信号: {len(verified_signals)} 个")

    # 统计验证结果
    status_count = {}
    for sig in verified_signals:
        status = sig.get('verification', {}).get('verification_status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1

    print(f"\n📊 验证结果统计:")
    for status, count in status_count.items():
        status_text = {
            'verified': '✅ 已验证',
            'partially_verified': '⚠️ 部分验证',
            'unverified': '❌ 未验证',
            'contradicted': '❌ 与事实矛盾',
            'error': '⚠️ 验证出错'
        }.get(status, status)
        print(f"   {status_text}: {count} 个")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step4b_verify_signals_vertex.py <signals_json> [output_json] [max_signals]")
        print("")
        print("参数:")
        print("  signals_json : 输入的信号 JSON 文件")
        print("  output_json  : 输出的验证后 JSON 文件（可选，默认 signals_verified.json）")
        print("  max_signals  : 最多验证几个信号（可选，默认全部）")
        print("")
        print("示例:")
        print("  python step4b_verify_signals_vertex.py extracted_signals_fast.json")
        print("  python step4b_verify_signals_vertex.py extracted_signals_fast.json verified.json 3")
        print("")
        print("需要:")
        print("  - Vertex AI Service Account Key: /Users/antonio/Desktop/liaoandi-vertex-ai-key.json")
        print("  - 已安装: pip install google-genai")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'extracted_signals_verified.json'
    max_signals = int(sys.argv[3]) if len(sys.argv) > 3 else None

    verify_all_signals(input_file, output_file, max_signals)
