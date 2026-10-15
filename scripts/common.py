"""Shared helpers for the Part 2 live demos."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

SAMPLE_TICKET = (
    "Hi, this is Priya from Acme. Order #4821 arrived yesterday but the "
    "keyboard is missing two keys. Can I get a replacement shipped to "
    "91 Market Street by Friday? Thanks."
)


def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "Set OPENAI_API_KEY in the environment or in a .env file "
            "(see .env.example)."
        )


def llm(temperature: float = 0) -> ChatOpenAI:
    require_api_key()
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=temperature,
    )


def banner(title: str) -> None:
    line = "=" * 64
    print(f"\n{line}\n{title}\n{line}")


def show_json(label: str, data: Any) -> None:
    print(f"\n{label}")
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    print(json.dumps(data, indent=2))
