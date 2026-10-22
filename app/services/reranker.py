from typing import Any

from sentence_transformers import CrossEncoder

from app.config import settings


class RerankerService:
    def __init__(self) -> None:
        self.model: CrossEncoder | None = None

    def _get_model(self) -> CrossEncoder:
        if self.model is None:
            self.model = CrossEncoder(settings.reranker_model)
        return self.model

    def warm_up(self) -> None:
        self._get_model()

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        if not results or limit <= 0:
            return []

        candidates = [
            result
            for result in results
            if isinstance(result.get("content"), str) and result["content"].strip()
        ]

        if not settings.reranker_enabled:
            return candidates[:limit]

        if not candidates:
            return []

        pairs = [(query, result["content"]) for result in candidates]
        scores = self._get_model().predict(pairs)

        reranked = []

        for result, score in zip(candidates, scores, strict=True):
            item = result.copy()
            item["vector_score"] = item.get("score")
            item["score"] = float(score)
            reranked.append(item)

        reranked.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return reranked[:limit]


reranker_service = RerankerService()
