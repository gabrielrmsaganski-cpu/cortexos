from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.text_utils import hashed_dense_vector, hashed_sparse_vector

logger = logging.getLogger(__name__)


@dataclass
class EncodedText:
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]


class BaseHybridEncoder:
    dense_dim: int

    def encode_documents(self, texts: list[str]) -> list[EncodedText]:
        raise NotImplementedError

    def encode_queries(self, texts: list[str]) -> list[EncodedText]:
        return self.encode_documents(texts)


class FallbackHybridEncoder(BaseHybridEncoder):
    def __init__(self, dense_dim: int) -> None:
        self.dense_dim = dense_dim

    def encode_documents(self, texts: list[str]) -> list[EncodedText]:
        encoded: list[EncodedText] = []
        for text in texts:
            dense = hashed_dense_vector(text, self.dense_dim)
            sparse_indices, sparse_values = hashed_sparse_vector(text)
            encoded.append(
                EncodedText(
                    dense=dense,
                    sparse_indices=sparse_indices,
                    sparse_values=sparse_values,
                )
            )
        return encoded


class BgeM3HybridEncoder(BaseHybridEncoder):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.dense_dim = 1024
        from FlagEmbedding import BGEM3FlagModel  # type: ignore

        self.model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)

    def encode_documents(self, texts: list[str]) -> list[EncodedText]:
        result = self.model.encode(
            texts,
            batch_size=4,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
        )
        encoded: list[EncodedText] = []
        dense_vectors = result.get("dense_vecs", [])
        lexical_weights = result.get("lexical_weights", [])
        for dense, sparse in zip(dense_vectors, lexical_weights, strict=False):
            indices = [int(key) for key in sparse.keys()]
            values = [float(value) for value in sparse.values()]
            encoded.append(
                EncodedText(
                    dense=list(map(float, dense)),
                    sparse_indices=indices,
                    sparse_values=values,
                )
            )
        return encoded


def build_encoder() -> BaseHybridEncoder:
    settings = get_settings()
    if settings.embedding_backend == "bge-m3":
        try:
            return BgeM3HybridEncoder()
        except Exception as exc:
            logger.warning("Falling back to hashed hybrid encoder: %s", exc)
    return FallbackHybridEncoder(settings.dense_dim)
