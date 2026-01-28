#!/usr/bin/env python3
"""
通用 Gemini API 客户端 (Vertex AI)

功能：
- 自动处理认证（从 .env 或环境变量读取 Service Account Key）
- 支持 JSON 模式输出
- 支持 Google Search 工具
- 简化的调用接口

使用方法：
    from gemini_client import GeminiClient

    # 基本使用
    client = GeminiClient()
    response = client.generate(prompt="解释量子计算")
    print(response)

    # JSON 模式
    client = GeminiClient(json_mode=True)
    result = client.generate(prompt="返回 JSON 格式: {name: '张三', age: 30}")
    print(result)  # dict

    # 启用 Google Search
    client = GeminiClient(enable_search=True)
    response = client.generate(prompt="搜索 2026 年最新 AI 进展")

    # 自定义模型
    client = GeminiClient(model="gemini-3-pro-preview")

环境变量配置：
    .env 文件或环境变量：
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
    GOOGLE_CLOUD_PROJECT=your-project-id  # 可选，会自动从 SA key 读取
"""

import json
import os
from typing import Optional, Dict, Any, Union
from google import genai
from google.genai import types


class GeminiClient:
    """通用 Gemini API 客户端（Vertex AI）"""

    # 默认配置
    DEFAULT_LOCATION = "global"
    DEFAULT_MODEL = "gemini-3-pro-preview"

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model: Optional[str] = None,
        json_mode: bool = False,
        enable_search: bool = False,
        verbose: bool = False
    ):
        """
        初始化 Gemini 客户端

        Args:
            project_id: Google Cloud 项目 ID（可选，自动从 SA key 读取）
            location: Vertex AI 位置（默认 'global'）
            model: 模型名称（默认 'gemini-3-pro-preview'）
            json_mode: 是否启用 JSON 模式输出（默认 False）
            enable_search: 是否启用 Google Search 工具（默认 False）
            verbose: 是否输出详细日志（默认 False）
        """
        self.verbose = verbose
        self.json_mode = json_mode
        self.enable_search = enable_search

        # 设置认证
        self._setup_credentials()

        # 获取项目配置
        self.project_id = project_id or self._get_project_id()
        self.location = location or self.DEFAULT_LOCATION
        self.model_name = model or self.DEFAULT_MODEL

        if self.verbose:
            print(f"🔧 初始化 Vertex AI:")
            print(f"   模型: {self.model_name}")
            print(f"   位置: {self.location}")
            print(f"   项目: {self.project_id}")
            print(f"   JSON 模式: {self.json_mode}")
            print(f"   Google Search: {self.enable_search}")

        # 初始化客户端
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

        if self.verbose:
            print("   ✓ 连接成功\n")

    def _setup_credentials(self):
        """设置 Google Cloud 认证"""
        sa_key_path = self._get_sa_key_path()
        if sa_key_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path
            if self.verbose:
                print(f"✓ 找到 Service Account Key: {sa_key_path}")
        else:
            if self.verbose:
                print("⚠️  未找到 GOOGLE_APPLICATION_CREDENTIALS")
                print("   请在 .env 文件中配置或设置环境变量")
                print("   例如：GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")

    def _get_sa_key_path(self) -> Optional[str]:
        """从环境变量或 .env 获取 Service Account Key 路径"""
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
                        # 移除可能的引号
                        key_path = key_path.strip('"').strip("'")
                        if os.path.exists(key_path):
                            return key_path

        return None

    def _get_project_id(self) -> str:
        """获取 Google Cloud Project ID"""
        # 从 Service Account Key 读取
        sa_key_path = self._get_sa_key_path()
        if sa_key_path and os.path.exists(sa_key_path):
            try:
                with open(sa_key_path, 'r') as f:
                    data = json.load(f)
                    project_id = data.get('project_id')
                    if project_id:
                        return project_id
            except Exception:
                pass

        # 从环境变量读取
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return project_id

        raise ValueError(
            "未找到 project_id。请设置 GOOGLE_CLOUD_PROJECT 环境变量，"
            "或确保 Service Account Key 包含 project_id"
        )

    def generate(
        self,
        prompt: str,
        json_mode: Optional[bool] = None,
        enable_search: Optional[bool] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        生成内容

        Args:
            prompt: 输入提示词
            json_mode: 是否启用 JSON 模式（覆盖初始化设置）
            enable_search: 是否启用 Google Search（覆盖初始化设置）
            temperature: 温度参数（0.0-2.0）
            max_tokens: 最大输出 token 数
            **kwargs: 其他传递给 generate_content 的参数

        Returns:
            如果 json_mode=True，返回解析后的 dict
            否则返回原始文本字符串
        """
        # 使用参数或默认设置
        use_json = json_mode if json_mode is not None else self.json_mode
        use_search = enable_search if enable_search is not None else self.enable_search

        # 构建配置
        config_params = {}

        if use_json:
            config_params['response_mime_type'] = "application/json"

        if temperature is not None:
            config_params['temperature'] = temperature

        if max_tokens is not None:
            config_params['max_output_tokens'] = max_tokens

        # 构建工具
        tools = []
        if use_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        # 调用 API
        try:
            if self.verbose:
                print(f"📤 调用 {self.model_name}...")
                print(f"   提示词长度: {len(prompt)} 字符")
                print(f"   JSON 模式: {use_json}")
                print(f"   Google Search: {use_search}")

            # 准备参数
            api_params = {
                'model': self.model_name,
                'contents': prompt,
            }

            # 添加配置
            if config_params or tools:
                config = types.GenerateContentConfig(**config_params)
                if tools:
                    config.tools = tools
                api_params['config'] = config

            # 添加其他参数
            api_params.update(kwargs)

            # 调用
            response = self.client.models.generate_content(**api_params)

            if self.verbose:
                print("   ✓ 调用成功")

            # 处理响应
            text = response.text

            if use_json:
                # 尝试解析 JSON
                result = self._clean_json(text)
                if result is not None:
                    return result
                else:
                    # JSON 解析失败，返回原始文本
                    if self.verbose:
                        print("   ⚠️ JSON 解析失败，返回原始文本")
                    return text
            else:
                return text

        except Exception as e:
            error_msg = f"Gemini API 调用失败: {str(e)}"
            if self.verbose:
                print(f"   ❌ {error_msg}")
                import traceback
                traceback.print_exc()
            raise RuntimeError(error_msg)

    def _clean_json(self, text: str) -> Optional[Dict[str, Any]]:
        """清理和解析 JSON"""
        if not text:
            return None

        try:
            # 移除可能的 markdown 代码块标记
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"   ⚠️ JSON 解析错误: {e}")
                print(f"   原始文本前 200 字符: {text[:200]}...")
            return None

    def batch_generate(
        self,
        prompts: list[str],
        **kwargs
    ) -> list[Union[str, Dict[str, Any]]]:
        """
        批量生成（顺序执行）

        Args:
            prompts: 提示词列表
            **kwargs: 传递给 generate 的参数

        Returns:
            响应列表
        """
        results = []
        for i, prompt in enumerate(prompts, 1):
            if self.verbose:
                print(f"\n[{i}/{len(prompts)}] 处理中...")

            try:
                result = self.generate(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ 处理失败: {e}")
                results.append(None)

        return results


# 便捷函数
def quick_generate(
    prompt: str,
    json_mode: bool = False,
    enable_search: bool = False,
    model: str = GeminiClient.DEFAULT_MODEL,
    verbose: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    快速调用 Gemini（单次使用）

    Args:
        prompt: 输入提示词
        json_mode: 是否返回 JSON
        enable_search: 是否启用 Google Search
        model: 模型名称
        verbose: 是否输出日志

    Returns:
        生成的内容

    Example:
        >>> response = quick_generate("解释量子纠缠")
        >>> print(response)
    """
    client = GeminiClient(
        model=model,
        json_mode=json_mode,
        enable_search=enable_search,
        verbose=verbose
    )
    return client.generate(prompt)


if __name__ == "__main__":
    # 示例用法
    print("=" * 60)
    print("Gemini Client 示例")
    print("=" * 60)

    # 示例 1: 基本文本生成
    print("\n示例 1: 基本文本生成")
    print("-" * 60)
    client = GeminiClient(verbose=True)
    response = client.generate("用一句话解释什么是大语言模型")
    print(f"响应: {response}\n")

    # 示例 2: JSON 模式
    print("\n示例 2: JSON 模式")
    print("-" * 60)
    client = GeminiClient(json_mode=True, verbose=True)
    prompt = """
    请返回以下信息的 JSON 格式：
    {
        "name": "Claude",
        "type": "AI助手",
        "capabilities": ["对话", "编程", "分析"]
    }
    """
    response = client.generate(prompt)
    print(f"响应类型: {type(response)}")
    print(f"响应内容: {json.dumps(response, ensure_ascii=False, indent=2)}\n")

    # 示例 3: 启用 Google Search
    print("\n示例 3: 启用 Google Search")
    print("-" * 60)
    client = GeminiClient(enable_search=True, verbose=True)
    response = client.generate("2026 年 1 月最新的 AI 行业新闻")
    print(f"响应: {response[:200]}...\n")

    # 示例 4: 快速调用
    print("\n示例 4: 快速调用")
    print("-" * 60)
    response = quick_generate(
        "列举 3 个著名的 AI 公司",
        verbose=True
    )
    print(f"响应: {response}\n")

    print("=" * 60)
    print("所有示例完成！")
    print("=" * 60)
