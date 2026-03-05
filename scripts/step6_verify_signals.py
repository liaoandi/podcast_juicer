#!/usr/bin/env python3
"""
使用 Vertex AI (Gemini 3 Pro) + Google Search + 实时数据源 验证投资信号

数据源：
1. Google Search - 新闻和事件验证
2. Yahoo Finance - 股价和财务数据验证
"""

import json
import os
import sys
import time
from datetime import datetime
from google.genai import types
from gemini_utils import get_gemini_client, get_project_id, ensure_credentials, DEFAULT_MODEL

# 导入数据源模块
HAS_DATA_SOURCES = False
try:
    from data_utils import DataSources
    HAS_DATA_SOURCES = True
except ImportError:
    try:
        # 尝试从同目录导入
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from data_utils import DataSources
        HAS_DATA_SOURCES = True
    except ImportError:
        pass

# 配置 — 验证用 pro 模型（需要深度推理判断信号真伪）
LOCATION = "global"
GEMINI_MODEL = DEFAULT_MODEL

class VertexVerifier:
    def __init__(self, project_id=None, location=None, model=None, record_date=None):
        """
        初始化 Vertex AI 客户端

        Args:
            project_id: GCP 项目 ID
            location: Vertex AI 位置
            model: 模型名称
            record_date: 信号发出的日期（用于计算价格变化）
        """
        # 设置凭证
        ensure_credentials(verbose=True)
        self.project_id = project_id or get_project_id()
        self.location = location or LOCATION
        self.model_name = model or GEMINI_MODEL
        self.record_date = record_date

        print(f"🔧 初始化 Vertex AI: {self.model_name} @ {self.location} ({self.project_id})")

        # 初始化客户端（使用默认配置）
        self.client = get_gemini_client(
            project_id=self.project_id,
            location=self.location
        )

        # 初始化数据源
        self.data_sources = None
        if HAS_DATA_SOURCES:
            try:
                self.data_sources = DataSources()
                print("   ✓ 实时数据源已启用 (Yahoo Finance)")
            except Exception as e:
                print(f"   ⚠️ 实时数据源初始化失败: {e}")
        else:
            print("   ⚠️ 实时数据源未启用 (pip install yfinance)")

    def get_market_data_for_signal(self, signal):
        """
        获取信号相关的实时市场数据

        Returns:
            {
                'NVDA': {
                    'current': {'price': 850, 'change_percent': 1.5},
                    'since_signal': {'from_price': 800, 'to_price': 850, 'change_percent': 6.25},
                    'financials': {'pe_ratio': 65, 'market_cap': 2100000000000}
                }
            }
        """
        if not self.data_sources:
            return {}

        market_data = {}
        entities = signal.get('entities', [])

        for entity in entities:
            ticker = entity.get('ticker')
            if not ticker:
                continue

            data = {}

            # 当前价格
            current = self.data_sources.get_stock_price(ticker)
            if current:
                data['current'] = {
                    'price': current['price'],
                    'change_percent': current['change_percent'],
                    'market_cap': current.get('market_cap'),
                    'name': current.get('name')
                }

            # 从信号日期到现在的变化
            if self.record_date:
                change = self.data_sources.get_price_change(ticker, self.record_date)
                if change:
                    data['since_signal'] = {
                        'from_date': change['from_date'],
                        'to_date': change['to_date'],
                        'from_price': change['from_price'],
                        'to_price': change['to_price'],
                        'change': change['change'],
                        'change_percent': change['change_percent'],
                        'trading_days': change['trading_days']
                    }

            # 财务数据
            financials = self.data_sources.get_financials(ticker)
            if financials:
                data['financials'] = {
                    'pe_ratio': financials.get('pe_ratio'),
                    'forward_pe': financials.get('forward_pe'),
                    'profit_margin': financials.get('profit_margin'),
                    'revenue_growth': financials.get('revenue_growth'),
                    '52_week_high': financials.get('52_week_high'),
                    '52_week_low': financials.get('52_week_low')
                }

            if data:
                market_data[ticker] = data

        return market_data

    def verify_signal(self, signal):
        """验证单个信号（使用Gemini + Google Search + 市场数据）"""
        # 获取实时市场数据
        market_data = self.get_market_data_for_signal(signal)

        if market_data:
            tickers = list(market_data.keys())
            print(f"   📊 获取市场数据: {', '.join(tickers)}")

        # 构建 prompt
        prompt = self._build_simple_prompt(signal, market_data)

        # 重试机制（3次，指数退避）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   [尝试 {attempt + 1}/{max_retries}]")

                response = self.client.models.generate_content(
                    model=self.model_name,  # 使用配置的模型
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1,
                        max_output_tokens=65536
                    )
                )

                # 解析 JSON
                verification_data = self._clean_json(response.text)

                if verification_data:
                    verification_data['verification_date'] = datetime.now().strftime('%Y-%m-%d')
                    verification_data['signal_date'] = self.record_date
                    verification_data['market_data'] = market_data

                    # 规范化置信度
                    if 'verification_confidence' in verification_data:
                        value = verification_data['verification_confidence']
                        if value not in ['high', 'low']:
                            verification_data['verification_confidence'] = 'low'

                    return verification_data
                else:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️ JSON解析失败，重试...")
                        continue
                    return self._error_verification("JSON 解析失败")

            except Exception as e:
                error_msg = str(e)
                print(f"   ⚠️ 错误: {error_msg[:100]}")

                # 429错误，等待更长时间
                if '429' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)  # 30秒、60秒、90秒
                        print(f"   ⏳ API配额限制，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                    else:
                        return self._error_verification(error_msg)
                # 其他错误，短时间重试
                else:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"   ⏳ 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        return self._error_verification(error_msg)

        # Safety: should not reach here, but just in case
        return self._error_verification("max retries exhausted")

    def _build_simple_prompt(self, signal, market_data):
        """构建简化prompt（使用Google Search验证）"""
        entities = signal.get('entities', [])
        entity_names = ', '.join([e['name'] for e in entities])
        claim = signal.get('claim', '')

        # 市场数据摘要
        market_summary = ""
        if market_data:
            for ticker, data in market_data.items():
                if 'since_signal' in data:
                    chg = data['since_signal']['change_percent']
                    days = data['since_signal']['trading_days']
                    market_summary += f"{ticker}: {chg:+.1f}% ({days}日); "

        prompt = f"""你是投资研究分析师。使用 Google Search 验证以下投资信号，提供详细的验证报告。

**信号内容**
公司：{entity_names}
判断：{claim}
信号日期：{self.record_date or '未知'}
市场数据：{market_summary or '无'}

**验证要求**
1. 使用 Google Search 搜索最新的新闻、财报、行业报告来验证
2. 每个来源必须提供具体的 URL 链接
3. 分析信号发出后的真实影响路径
4. 详细说明验证依据

**输出JSON格式**：
{{
  "verification_status": "verified|contradicted|unverified",
  "verified_claim": "详细总结验证后的判断（2-3句话）",
  "verified_impact_path": [
    "影响路径1：从X到Y的传导机制",
    "影响路径2：对产业链的具体影响",
    "影响路径3：对投资者的实际意义"
  ],
  "verified_data": [
    {{
      "source": "来源名称（如 Bloomberg, Reuters）",
      "finding": "关键发现（详细描述，100-200字）",
      "url": "https://具体链接"
    }}
  ],
  "verification_confidence": "high|low",
  "verification_notes": "验证总结（2-3句话，包含关键数据）"
}}

规则：
- verified_data 提供 3-4 条来源，每条必须有 url
- verified_impact_path 提供 2-3 条影响路径
- 不要使用 markdown 格式
- 直接返回纯 JSON"""
        return prompt

    def _clean_json(self, text):
        """清理和解析 JSON（增强版，处理各种格式问题）"""
        if not text:
            return None

        # 提取JSON文本
        json_text = None

        # 方法1：尝试找到```json代码块
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                json_text = text[start:end].strip()

        # 方法2：尝试找到第一个{到最后一个}
        if not json_text and '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            json_text = text[start:end].strip()

        # 方法3：直接使用原文本
        if not json_text:
            json_text = text.strip()

        # 清理常见格式问题
        json_text = self._fix_json_format(json_text)

        # 尝试解析
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 解析错误: {e}")
            print(f"   原始文本: {text[:200]}...")
            return None

    def _fix_json_format(self, json_text):
        """修复常见的JSON格式问题"""
        import re

        # 1. 替换中文引号为英文引号
        json_text = json_text.replace('"', '"').replace('"', '"')
        json_text = json_text.replace(''', "'").replace(''', "'")

        # 2. 修复未转义的引号（在字符串值中）
        # 这个比较复杂，暂时跳过，让Gemini自己处理

        # 3. 移除多余的逗号（JSON末尾的逗号）
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

        # 4. 修复换行符
        # JSON字符串中的换行应该是\n而不是实际换行
        # 但这个很难自动修复，因为需要区分字符串内外

        return json_text

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
    metadata = data.get('metadata', {})

    # 获取信号日期（用于计算价格变化）
    record_date = metadata.get('record_date') or metadata.get('publish_date')
    if record_date:
        print(f"   信号日期: {record_date}")
    else:
        print(f"   ⚠️ 未找到信号日期，无法计算价格变化")

    if max_signals:
        signals = signals[:max_signals]
        print(f"   只验证前 {max_signals} 个信号")

    print(f"   共 {len(signals)} 个信号需要验证\n")

    # 初始化 Vertex AI（传入信号日期）
    verifier = VertexVerifier(record_date=record_date)
    print("   ✓ 连接成功\n")

    # 并发验证所有信号（互相独立）
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _verify_one(i, signal):
        entities = signal.get('entities', [])
        entity_names = ', '.join([e['name'] for e in entities])
        claim = signal.get('claim', '')
        print(f"🔍 [{i}/{len(signals)}] 验证: {entity_names} — {claim[:50]}...")
        verification = verifier.verify_signal(signal)
        signal['verification'] = verification
        status_map = {
            'verified': '✅', 'partially_verified': '⚠️',
            'unverified': '❌', 'contradicted': '❌', 'error': '⚠️'
        }
        st = verification.get('verification_status', '?')
        print(f"   [{i}] {status_map.get(st, '?')} {st} — {entity_names}")
        return i, signal

    verified_signals = [None] * len(signals)
    max_workers = min(3, len(signals))  # 验证用 Google Search，不宜太多并发

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, signal in enumerate(signals):
            future = executor.submit(_verify_one, i + 1, signal)
            futures[future] = i

        for future in as_completed(futures):
            try:
                idx, signal = future.result()
                verified_signals[idx - 1] = signal
            except Exception as e:
                i = futures[future]
                print(f"   [{i+1}] 验证异常: {e}")
                signals[i]['verification'] = verifier._error_verification(str(e))
                verified_signals[i] = signals[i]

    # 保存结果
    output_data = {
        'metadata': {
            **data['metadata'],
            'verification_date': datetime.now().strftime('%Y-%m-%d'),
            'verification_method': 'gemini_3_pro + google_search + yahoo_finance',
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
        print("用法: python step6_verify_signals.py <signals_json> [output_json] [max_signals]")
        print("")
        print("参数:")
        print("  signals_json : 输入的信号 JSON 文件")
        print("  output_json  : 输出的验证后 JSON 文件（可选，默认 signals_verified.json）")
        print("  max_signals  : 最多验证几个信号（可选，默认全部）")
        print("")
        print("示例:")
        print("  python step6_verify_signals.py extracted_signals_fast.json")
        print("  python step6_verify_signals.py extracted_signals_fast.json verified.json 3")
        print("")
        print("需要:")
        print("  - Vertex AI Service Account Key (via GOOGLE_APPLICATION_CREDENTIALS)")
        print("  - 已安装: pip install google-genai")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'extracted_signals_verified.json'
    max_signals = int(sys.argv[3]) if len(sys.argv) > 3 else None

    verify_all_signals(input_file, output_file, max_signals)
