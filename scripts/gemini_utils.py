"""LLM 统一入口 + Gemini 工具集。

合并自：
- qieman_invest/src/lib/llm_client.py (Anthropic fail-fast, auto-routing)
- podcast_juicer_sv101/scripts/gemini_utils.py (credential resolution, timeout, clean_json)
- podcast_juicer_getoff3pm/llm_client.py (DNS fallback, inline config)

用法：
    from gemini_utils import call_llm, get_gemini_client, clean_json, patch_dns
    patch_dns()  # optional, for networks with flaky DNS
    result = call_llm("prompt", engine="auto")  # Anthropic first, Gemini fallback
    client = get_gemini_client()  # for direct use (transcription etc.)
"""

from __future__ import annotations

import functools
import json
import os
import re
import socket
import subprocess
import time
from typing import Optional


# ── Config ───────────────────────────────────────────────────

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-pro-preview")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

DEFAULT_DNS_FALLBACKS: dict[str, list[str]] = {
    "api.anthropic.com": ["160.79.104.10"],
    "oauth2.googleapis.com": ["172.253.118.95"],
    "aiplatform.googleapis.com": [
        "74.125.200.95",
        "172.253.118.95",
        "172.217.70.95",
        "64.233.170.95",
        "74.125.68.95",
        "74.125.24.95",
        "142.251.12.95",
        "142.250.4.95",
        "74.125.130.95",
        "172.217.194.95",
        "142.251.10.95",
    ],
    "generativelanguage.googleapis.com": [
        "74.125.200.95",
        "142.250.4.95",
        "172.217.194.95",
        "64.233.170.95",
        "172.217.70.95",
        "74.125.68.95",
        "172.253.118.95",
        "74.125.130.95",
        "142.251.12.95",
        "74.125.24.95",
        "142.251.10.95",
    ],
}


# ── DNS fallback patch ───────────────────────────────────────

_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_DNS_PATCHED = False

try:
    _DNS_FALLBACK_MAP: dict[str, list[str]] = json.loads(
        os.getenv("DNS_FALLBACK_JSON", "") or "{}"
    )
except Exception:
    _DNS_FALLBACK_MAP = {}
for _host, _ips in DEFAULT_DNS_FALLBACKS.items():
    _DNS_FALLBACK_MAP.setdefault(_host, _ips)


@functools.lru_cache(maxsize=256)
def _dig_ipv4(host: str) -> list[str]:
    env_ips = _DNS_FALLBACK_MAP.get(host)
    if isinstance(env_ips, list):
        return [
            ip
            for ip in env_ips
            if isinstance(ip, str) and re.fullmatch(r"\d+\.\d+\.\d+\.\d+", ip)
        ]
    try:
        output = subprocess.check_output(
            [
                "curl", "--silent", "--show-error", "--max-time", "5",
                f"https://dns.google/resolve?name={host}&type=A",
            ],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
    except Exception:
        return []
    return re.findall(r'"data"\s*:\s*"(\d+\.\d+\.\d+\.\d+)"', output)


def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
    except socket.gaierror as err:
        if not isinstance(host, str) or host in {"localhost", "127.0.0.1"}:
            raise
        ips = _dig_ipv4(host)
        if not ips:
            raise err
        requested_family = family if family not in (0, socket.AF_UNSPEC) else socket.AF_INET
        requested_type = type or socket.SOCK_STREAM
        requested_proto = proto or socket.IPPROTO_TCP
        return [
            (requested_family, requested_type, requested_proto, "", (ip, port))
            for ip in ips
        ]


def patch_dns() -> None:
    """Install DNS fallback patch. Call from CLI entry points, not at import time."""
    global _DNS_PATCHED
    if not _DNS_PATCHED:
        socket.getaddrinfo = _patched_getaddrinfo
        _DNS_PATCHED = True


# ── Credential resolution (from sv101 gemini_utils) ─────────

def _global_env_file() -> str:
    return os.path.expanduser("~/.config/api-keys.env")


def _strip_quotes(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return value.strip().strip('"').strip("'")


def _load_value_from_file(file_path: str, key: str) -> Optional[str]:
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(f"{key}="):
                return _strip_quotes(line.split("=", 1)[1].strip())
    return None


def load_env_value(key: str) -> Optional[str]:
    """Resolve a config value: env var → ~/.config/api-keys.env."""
    value = os.getenv(key)
    if value:
        return _strip_quotes(value)
    return _load_value_from_file(_global_env_file(), key)


def get_sa_key_path() -> Optional[str]:
    """Find Google SA key: GOOGLE_APPLICATION_CREDENTIALS → well-known path."""
    candidates = [
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        _load_value_from_file(_global_env_file(), "GOOGLE_APPLICATION_CREDENTIALS"),
        "~/.config/secrets/liaoandi_vertex_ai_key.json",
    ]
    for candidate in candidates:
        key_path = _strip_quotes(candidate)
        if not key_path:
            continue
        expanded = os.path.expanduser(key_path)
        if os.path.exists(expanded):
            return expanded
    return None


def get_project_id() -> Optional[str]:
    """Resolve GCP project ID from SA key or env."""
    sa_key_path = get_sa_key_path()
    if sa_key_path:
        try:
            with open(sa_key_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                project_id = data.get("project_id")
                if project_id:
                    return project_id
        except Exception:
            pass
    return load_env_value("GOOGLE_CLOUD_PROJECT")


def ensure_credentials(verbose: bool = False) -> Optional[str]:
    """Set GOOGLE_APPLICATION_CREDENTIALS if found. Returns path or None."""
    sa_key_path = get_sa_key_path()
    if sa_key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_path
        if verbose:
            print(f"  [auth] Using SA key: {sa_key_path}")
    return sa_key_path


# ── Gemini (Vertex AI) ──────────────────────────────────────

_GEMINI_CLIENT = None


def init_gemini(timeout: int = 600) -> bool:
    """Initialize Vertex AI Gemini client with configurable timeout."""
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is not None:
        return True

    ensure_credentials()
    project_id = get_project_id()
    if not project_id:
        print("  [gemini] No project_id found. Set GOOGLE_CLOUD_PROJECT or configure SA key.")
        return False

    try:
        from google import genai
        from google.genai import types as _types

        timeout_ms = timeout * 1000
        _GEMINI_CLIENT = genai.Client(
            vertexai=True,
            project=project_id,
            location="global",
            http_options=_types.HttpOptions(timeout=timeout_ms),
        )
        return True
    except Exception as e:
        print(f"  [gemini] Init failed: {e}")
        return False


def get_gemini_client(
    project_id: Optional[str] = None,
    location: str = "global",
    timeout: Optional[int] = None,
):
    """Create and return a Gemini client (for direct use in transcription etc.)."""
    from google import genai
    from google.genai import types as _types

    ensure_credentials()
    pid = project_id or get_project_id()
    if not pid:
        raise ValueError("No project_id found.")
    timeout_ms = (timeout or 600) * 1000
    return genai.Client(
        vertexai=True,
        project=pid,
        location=location,
        http_options=_types.HttpOptions(timeout=timeout_ms),
    )


def call_gemini(prompt: str, model: Optional[str] = None) -> str:
    """Call Gemini model."""
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is None:
        if not init_gemini():
            return ""
    try:
        from google.genai import types

        response = _GEMINI_CLIENT.models.generate_content(
            model=model or GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=32768),
        )
        return response.text or ""
    except Exception as e:
        print(f"  [gemini] Call error: {e}")
        return ""


# ── Anthropic ────────────────────────────────────────────────

_ANTHROPIC_CLIENT = None


def _is_anthropic_fail_fast_error(exc: Exception) -> bool:
    """Skip retries for quota/auth failures that won't recover within the same run."""
    message = str(exc).lower()
    markers = (
        "usage limits", "rate limit", "credit balance is too low",
        "insufficient credits", "billing", "request not allowed",
        "forbidden", "permission", "invalid x-api-key", "authentication",
    )
    return any(marker in message for marker in markers)


def init_anthropic() -> bool:
    """Initialize Anthropic client (lazy import)."""
    global _ANTHROPIC_CLIENT
    if _ANTHROPIC_CLIENT is not None:
        return True
    try:
        import anthropic
        _ANTHROPIC_CLIENT = anthropic.Anthropic()
        return True
    except Exception:
        return False


def call_anthropic(prompt: str) -> str:
    """Call Anthropic (Sonnet) with retries and fail-fast detection."""
    if not init_anthropic():
        return ""

    last_exc = None
    for attempt in range(3):
        try:
            response = _ANTHROPIC_CLIENT.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            if response.content:
                return response.content[0].text or ""
        except Exception as exc:
            last_exc = exc
            if _is_anthropic_fail_fast_error(exc):
                print(f"  [anthropic] Fail-fast: {exc}", flush=True)
                break
            wait = 5 * (attempt + 1)
            print(f"  [anthropic] Error: {exc}; retry in {wait}s", flush=True)
            time.sleep(wait)

    if last_exc is not None:
        print(f"  [anthropic] Final failure: {last_exc}", flush=True)
    return ""


# ── Unified router ───────────────────────────────────────────

def call_llm(prompt: str, engine: str = "auto", require_success: bool = False) -> str:
    """Unified LLM call. engine: "auto" | "anthropic" | "gemini"."""
    if engine in {"auto", "anthropic"}:
        result = call_anthropic(prompt)
        if result:
            return result
        if engine == "anthropic" and require_success:
            raise RuntimeError("Anthropic call failed.")

    if engine in {"auto", "gemini"}:
        if init_gemini():
            result = call_gemini(prompt)
            if result:
                return result
        if engine == "gemini" and require_success:
            raise RuntimeError("Gemini call failed.")

    if require_success:
        raise RuntimeError(f"LLM call failed for engine={engine}.")
    return ""


# ── JSON cleanup ─────────────────────────────────────────────

def clean_json(text: str):
    """Parse LLM output into a Python object, handling common formatting issues.

    Handles markdown code blocks, Chinese quotes, trailing commas, truncated JSON.
    """
    if not text:
        return None

    json_text = text

    # Strip markdown code block
    if "```json" in json_text:
        start = json_text.find("```json") + 7
        end = json_text.find("```", start)
        if end > start:
            json_text = json_text[start:end].strip()
    elif "```" in json_text:
        json_text = json_text.replace("```", "").strip()

    # Fast path
    try:
        return json.loads(json_text)
    except Exception:
        pass

    # Extract JSON object or array
    obj_start = json_text.find("{")
    arr_start = json_text.find("[")
    if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
        end = json_text.rfind("}")
        if end > obj_start:
            json_text = json_text[obj_start : end + 1]
    elif arr_start >= 0:
        end = json_text.rfind("]")
        if end > arr_start:
            json_text = json_text[arr_start : end + 1]

    # Chinese quotes + trailing commas
    json_text = json_text.replace("\u201c", '"').replace("\u201d", '"')
    json_text = json_text.replace("\u2018", "'").replace("\u2019", "'")
    json_text = re.sub(r",(\s*[}\]])", r"\1", json_text)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass

    # Attempt to fix truncated JSON
    try:
        if json_text.strip().startswith("{"):
            last_complete = json_text.rfind("}")
            if last_complete > 0:
                fixed = json_text[: last_complete + 1]
                open_brackets = fixed.count("[") - fixed.count("]")
                open_braces = fixed.count("{") - fixed.count("}")
                fixed += "]" * max(0, open_brackets)
                fixed += "}" * max(0, open_braces)
                return json.loads(fixed)
    except Exception:
        pass

    return None


# Backward compat: sv101 scripts import DEFAULT_MODEL from here.
DEFAULT_MODEL = GEMINI_MODEL_NAME
FLASH_MODEL = GEMINI_FLASH_MODEL
