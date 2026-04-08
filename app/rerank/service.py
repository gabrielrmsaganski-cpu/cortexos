from __future__ import annotations

import logging

from app.core.text_utils import lexical_overlap_score

logger = logging.getLogger(__name__)


class BaseReranker:
    def score(self, query: str, passages: list[str]) -> list[float]:
        raise NotImplementedError


class FallbackReranker(BaseReranker):
    def score(self, query: str, passages: list[str]) -> list[float]:
        return [lexical_overlap_score(query, passage) for passage in passages]


class BgeReranker(BaseReranker):
    def __init__(self) -> None:
        from FlagEmbedding import FlagReranker  # type: ignore

        self.model = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)

    def score(self, query: str, passages: list[str]) -> list[float]:
        pairs = [[query, passage] for passage in passages]
        scores = self.model.compute_score(pairs, normalize=True)
        if isinstance(scores, float):
            return [scores]
        return [float(score) for score in scores]


def build_reranker() -> BaseReranker:
    try:
        return BgeReranker()
    except Exception as exc:
        logger.warning("Falling back to lexical reranker: %s", exc)
        return FallbackReranker()
