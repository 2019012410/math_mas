from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class LLMConfig:
    model: str
    api_key: str
    base_url: str

    def as_autogen_config_list(self) -> List[Dict[str, str]]:
        return [
            {
                "model": self.model,
                "api_key": self.api_key,
                "base_url": self.base_url,
            }
        ]


def load_llm_config() -> LLMConfig:
    """Load LLM credentials from environment variables."""
    model = os.getenv("MAS_MODEL", "deepseek-v4")
    api_key = os.getenv("MAS_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("MAS_BASE_URL") or os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
    )

    if not api_key:
        raise ValueError(
            "Missing API key. Set MAS_API_KEY or DEEPSEEK_API_KEY before running."
        )

    return LLMConfig(model=model, api_key=api_key, base_url=base_url)
