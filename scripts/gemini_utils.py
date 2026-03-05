#!/usr/bin/env python3
"""
Gemini/Vertex AI shared helpers.

- Resolve GOOGLE_APPLICATION_CREDENTIALS from env or project .env
- Resolve project_id from SA key or GOOGLE_CLOUD_PROJECT
- Create genai.Client with optional timeout
- JSON cleanup helper
- Unified model constant
- API call retry logic
"""

import json
import os
import re
import time
from typing import Optional

from google import genai

# ---------------------------------------------------------------------------
# Default model – single source of truth for all scripts
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-3.1-pro-preview"


def project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _strip_quotes(value: str) -> str:
    if value is None:
        return value
    return value.strip().strip('"').strip("'")


def load_env_value(key: str) -> Optional[str]:
    value = os.getenv(key)
    if value:
        return _strip_quotes(value)

    env_file = os.path.join(project_root(), ".env")
    if not os.path.exists(env_file):
        return None

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(f"{key}="):
                return _strip_quotes(line.split("=", 1)[1].strip())

    return None


def get_sa_key_path() -> Optional[str]:
    key_path = load_env_value("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path and os.path.exists(key_path):
        return key_path
    return None


def get_project_id() -> str:
    sa_key_path = get_sa_key_path()
    if sa_key_path and os.path.exists(sa_key_path):
        try:
            with open(sa_key_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                project_id = data.get("project_id")
                if project_id:
                    return project_id
        except Exception:
            pass

    project_id = load_env_value("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id

    raise ValueError(
        "未找到 project_id，请设置 GOOGLE_CLOUD_PROJECT 环境变量或配置 service account key"
    )


def ensure_credentials(verbose: bool = False) -> Optional[str]:
    sa_key_path = get_sa_key_path()
    if sa_key_path:
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", sa_key_path)
        if verbose:
            print(f"✓ 使用 Service Account Key: {sa_key_path}")
    else:
        if verbose:
            print("⚠️  未找到 GOOGLE_APPLICATION_CREDENTIALS")
            print("   请在 .env 文件中配置或设置环境变量")
    return sa_key_path


def get_gemini_client(
    project_id: Optional[str] = None,
    location: str = "global",
    timeout: Optional[int] = None,
    verbose: bool = False,
):
    """Create a Gemini client.

    Args:
        timeout: Timeout in seconds (converted to ms for SDK).
                 Default: 600s (10 minutes) for thinking models.
    """
    from google.genai import types as _types

    ensure_credentials(verbose=verbose)
    pid = project_id or get_project_id()
    # Default 600s timeout; SDK expects milliseconds
    timeout_ms = (timeout or 600) * 1000
    return genai.Client(
        vertexai=True,
        project=pid,
        location=location,
        http_options=_types.HttpOptions(timeout=timeout_ms),
    )


# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------
_lazy_client = None


def get_gemini_client_lazy(
    location: str = "global",
    timeout: Optional[int] = None,
):
    """Return a lazily-initialised singleton Gemini client."""
    global _lazy_client
    if _lazy_client is None:
        _lazy_client = get_gemini_client(location=location, timeout=timeout)
    return _lazy_client


# ---------------------------------------------------------------------------
# Robust JSON cleanup – merges best practices from 4 different implementations
# ---------------------------------------------------------------------------
def clean_json(text: str):
    """Parse LLM output into a Python object, handling common formatting issues.

    Handles:
    - Markdown code blocks (```json ... ```)
    - Extracting first JSON object {...} or array [...]
    - Chinese quotes replacement
    - Trailing commas
    - Truncated JSON (attempts to fix)
    """
    if not text:
        return None

    json_text = text

    # 1. Strip markdown code block
    if '```json' in json_text:
        start = json_text.find('```json') + 7
        end = json_text.find('```', start)
        if end > start:
            json_text = json_text[start:end].strip()
    elif '```' in json_text:
        json_text = json_text.replace('```', '').strip()

    # 2. Try direct parse first (fast path)
    try:
        return json.loads(json_text)
    except Exception:
        pass

    # 3. Extract JSON object or array
    obj_start = json_text.find('{')
    arr_start = json_text.find('[')

    if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
        end = json_text.rfind('}')
        if end > obj_start:
            json_text = json_text[obj_start:end + 1]
    elif arr_start >= 0:
        end = json_text.rfind(']')
        if end > arr_start:
            json_text = json_text[arr_start:end + 1]

    # 4. Replace Chinese quotes
    json_text = json_text.replace('\u201c', '"').replace('\u201d', '"')
    json_text = json_text.replace('\u2018', "'").replace('\u2019', "'")

    # 5. Remove trailing commas before } or ]
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

    # 6. Try parsing again
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass

    # 7. Attempt to fix truncated JSON
    try:
        # If it looks like a truncated array inside an object, close it
        if '"speaker_labels": [' in json_text or '"signal_candidates": [' in json_text or '"companies": [' in json_text:
            last_complete = json_text.rfind('"}')
            if last_complete < 0:
                last_complete = json_text.rfind('}')
            if last_complete > 0:
                # Close any open arrays and the root object
                fixed = json_text[:last_complete + 1]
                # Count unclosed brackets
                open_brackets = fixed.count('[') - fixed.count(']')
                open_braces = fixed.count('{') - fixed.count('}')
                fixed += ']' * max(0, open_brackets)
                fixed += '}' * max(0, open_braces)
                return json.loads(fixed)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Retry wrapper for Gemini API calls
# ---------------------------------------------------------------------------
def call_gemini_with_retry(client, model, contents, config, max_retries=3):
    """Call client.models.generate_content with automatic retry.

    - 429 (quota) errors: exponential back-off 30s, 60s, 90s
    - Other errors: short back-off 5s, 10s, 15s
    - Returns the response on success, raises on final failure.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            last_error = e
            error_msg = str(e)

            if attempt >= max_retries - 1:
                raise

            if '429' in error_msg:
                wait_time = 30 * (attempt + 1)
                print(f"   ⏳ API 配额限制 (429)，等待 {wait_time}s...")
            else:
                wait_time = 5 * (attempt + 1)
                print(f"   ⚠️ API 调用失败: {error_msg[:100]}，{wait_time}s 后重试...")

            time.sleep(wait_time)

    raise last_error  # type: ignore[misc]
