from abc import ABC
from collections.abc import Iterator

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.llm_model import LLMModel


class BaseLLMProvider(ABC):
    def __init__(self, model_config: LLMModel):
        self.model_config = model_config
        self.model = None

    @staticmethod
    def _messages(
        system_prompt: str,
        user_prompt: str,
    ) -> list[SystemMessage | HumanMessage]:
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

    @staticmethod
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []

            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)

                elif (
                    isinstance(item, dict)
                    and item.get("type") == "text"
                    and isinstance(item.get("text"), str)
                ):
                    text_parts.append(item["text"])

            return "".join(text_parts)

        return ""

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        response = self.model.invoke(self._messages(system_prompt, user_prompt))

        return self._extract_text(response.content)

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Iterator[str]:
        for chunk in self.model.stream(self._messages(system_prompt, user_prompt)):
            text = self._extract_text(chunk.content)

            if text:
                yield text
