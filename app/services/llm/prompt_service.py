import json
from functools import lru_cache
from pathlib import Path

PROMPTS_FILE = Path(__file__).resolve().parents[2] / "prompts" / "prompts.json"


class PromptService:
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_prompts() -> dict:
        with PROMPTS_FILE.open(encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def get(cls, name: str) -> str:
        prompts = cls._load_prompts()

        prompt = prompts.get(name)

        if prompt is None:
            raise ValueError(f"Prompt not found: {name}")

        return prompt["system"]


prompt_service = PromptService()
