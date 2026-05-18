"""Pluggable embedding provider — local SentenceTransformer or remote OpenAI.

Select via env vars:
  EMBEDDING_PROVIDER = "sentence-transformers" (default) or "openai"
  EMBEDDING_MODEL = "all-MiniLM-L6-v2" (default) or e.g. "text-embedding-3-small"
"""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod

import numpy as np


class Embedder(ABC):
    """Abstract interface for text embedding."""

    @abstractmethod
    async def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into a 2D numpy array (N x dim)."""
        ...

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this embedder."""
        ...


class SentenceTransformerEmbedder(Embedder):
    """Local embedding using sentence-transformers (no API cost, offline)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None  # lazy-loaded

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([]).reshape(0, self.dim)
        model = await asyncio.to_thread(self._load)
        embeddings = await asyncio.to_thread(
            model.encode,
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(embeddings)

    @property
    def dim(self) -> int:
        dims = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "multi-qa-mpnet-base-dot-v1": 768,
        }
        return dims.get(self._model_name, 384)

    @property
    def name(self) -> str:
        return f"sentence-transformers/{self._model_name}"


class OpenAIEmbedder(Embedder):
    """Remote embedding using OpenAI API (requires OPENAI_API_KEY env var)."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self._model_name = model_name
        self._client = None

    def _load(self):
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    async def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([]).reshape(0, self.dim)
        client = self._load()
        response = await client.embeddings.create(model=self._model_name, input=texts)
        embeddings = [item.embedding for item in response.data]
        # OpenAI embeddings are already normalized
        return np.array(embeddings)

    @property
    def dim(self) -> int:
        dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dims.get(self._model_name, 1536)

    @property
    def name(self) -> str:
        return f"openai/{self._model_name}"


def create_embedder(provider: str = "sentence-transformers", model: str = "all-MiniLM-L6-v2") -> Embedder:
    """Factory: create an embedder based on config."""
    if provider == "openai":
        return OpenAIEmbedder(model)
    return SentenceTransformerEmbedder(model)


# Module-level singleton, lazy-initialized
_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Return the singleton embedder, creating it from env config on first call."""
    global _embedder
    if _embedder is None:
        provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
        model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _embedder = create_embedder(provider, model)
    return _embedder
