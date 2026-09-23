"""
Environment loader — shared by every step.

Deliberately tiny: one provider (the direct Anthropic API), one model default.
The point of this workshop is the agent loop, not provider abstraction — if
that's interesting to you afterward, see claude_env.py in the AirClaude
project for a version that also supports Bedrock and Vertex.
"""

import os
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

DEFAULT_MODEL = "claude-sonnet-5"


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)


def get_model() -> str:
    load_env()
    return (os.environ.get("CLAUDE_MODEL") or "").strip() or DEFAULT_MODEL


def get_api_key() -> str:
    """Return a validated API key, or exit with a one-line fix if it's missing."""
    load_env()
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()

    if not key or key.startswith("your_"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set.\n"
            "  Fix: cp .env.example .env, then paste your key into .env\n"
            "  Get one at https://console.anthropic.com/settings/keys"
        )

    if not key.startswith("sk-ant-"):
        raise SystemExit(
            f"ANTHROPIC_API_KEY doesn't look right "
            f"(expected it to start with 'sk-ant-', got '{key[:7]}…')."
        )

    return key


def data_file(name: str) -> Path:
    return ROOT / "data" / name
