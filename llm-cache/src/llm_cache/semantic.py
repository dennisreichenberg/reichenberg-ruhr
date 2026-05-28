"""Embedding helper for semantic-mode cache lookups.

sentence-transformers is an optional dependency. The proxy starts up fine even
without it -- if a request asks for semantic mode and the model is unavailable,
the proxy degrades to exact-match only and logs a warning.
"""

from __future__ import annotations

from typing import Optional, Protocol


class Embedder(Protocol):
    def encode(self, text: str) -> list[float]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(model_name)

    def encode(self, text: str) -> list[float]:
        vec = self._model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vec.tolist()]


class StubEmbedder:
    """Deterministic stand-in used when sentence-transformers is not installed.

    Builds a tiny bag-of-words vector so the semantic plumbing can be tested
    end-to-end without pulling a heavy model. NOT suitable for production
    similarity matching."""

    DIM = 64

    def encode(self, text: str) -> list[float]:
        import hashlib

        vec = [0.0] * self.DIM
        for token in text.lower().split():
            h = hashlib.sha256(token.encode("utf-8")).digest()
            idx = h[0] % self.DIM
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


def load_embedder(model_name: str) -> Optional[Embedder]:
    """Try to load sentence-transformers; fall back to the stub.

    Returns None if even the stub can't be created (should not happen).
    """
    try:
        return SentenceTransformerEmbedder(model_name)
    except Exception:
        return StubEmbedder()
