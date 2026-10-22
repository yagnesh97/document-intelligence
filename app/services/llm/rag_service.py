from collections.abc import Iterator

from bson import ObjectId

from app.services.llm.factory import LLMFactory
from app.services.llm.model_service import LLMModelService
from app.services.llm.prompt_service import prompt_service
from app.services.search import search_service


class RAGService:
    def __init__(self):
        self.model_service = LLMModelService()

    def _prepare(
        self,
        question: str,
        model_id: str,
        limit: int,
        document_id: ObjectId | None,
    ) -> tuple:
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        model_config = self.model_service.get_by_id(model_id)

        if model_config is None:
            raise ValueError("LLM model configuration not found.")

        if not model_config.enabled:
            raise ValueError("LLM model is disabled.")

        results = search_service.search(
            query=question,
            limit=limit,
            document_id=document_id,
        )

        system_prompt = prompt_service.get("financial_qa")

        context = self._build_context(results)

        user_prompt = f"Document context:\n{context}\n\nQuestion:\n{question}"

        return (
            model_config,
            results,
            system_prompt,
            user_prompt,
        )

    def ask(
        self,
        question: str,
        model_id: str,
        limit: int = 5,
        document_id: ObjectId | None = None,
    ) -> dict:
        (
            model_config,
            results,
            system_prompt,
            user_prompt,
        ) = self._prepare(
            question=question,
            model_id=model_id,
            limit=limit,
            document_id=document_id,
        )

        if not results:
            return {
                "answer": (
                    "I could not find relevant information in the uploaded documents."
                ),
                "sources": [],
            }

        provider = LLMFactory.create(model_config)

        answer = provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return {
            "answer": answer,
            "sources": self._build_sources(results),
        }

    def stream(
        self,
        question: str,
        model_id: str,
        limit: int = 5,
        document_id: ObjectId | None = None,
    ) -> Iterator[str]:
        (
            model_config,
            results,
            system_prompt,
            user_prompt,
        ) = self._prepare(
            question=question,
            model_id=model_id,
            limit=limit,
            document_id=document_id,
        )

        if not results:
            yield ("I could not find relevant information in the uploaded documents.")
            return

        provider = LLMFactory.create(model_config)

        yield from provider.stream(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    @staticmethod
    def _build_context(
        results: list[dict],
    ) -> str:
        sections = []

        for index, result in enumerate(results, start=1):
            sections.append(
                f"[Source {index}]\n"
                f"Document ID: {result['document_id']}\n"
                f"Chunk ID: {result['chunk_id']}\n"
                f"Content:\n{result['content']}"
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_sources(
        results: list[dict],
    ) -> list[dict]:
        return [
            {
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "chunk_index": result["chunk_index"],
                "score": result["score"],
                "content": result["content"],
                "metadata": result["metadata"],
            }
            for result in results
        ]


rag_service = RAGService()
