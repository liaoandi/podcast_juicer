#!/usr/bin/env python3
"""Gemini/Vertex AI shared helpers — re-export from shared invest_sync_lib."""
import sys, os

agent_toolkit_dir = os.path.expanduser(
    os.getenv("AGENT_TOOLKIT_DIR", "~/Desktop/projects/agent_toolkit")
)
sys.path.insert(0, os.path.join(agent_toolkit_dir, "shared", "invest_sync_lib"))
from invest_llm import *  # noqa: F401,F403,E402

# Backward compat: sv101 scripts import DEFAULT_MODEL from here
DEFAULT_MODEL = GEMINI_MODEL_NAME  # noqa: F405
FLASH_MODEL = GEMINI_FLASH_MODEL  # noqa: F405
