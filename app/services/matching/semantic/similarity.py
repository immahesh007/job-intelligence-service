"""Cosine similarity computation for embeddings."""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two already-normalized vectors.

    Vectors are expected to be L2-normalized (unit vectors), so dot product
    directly gives cosine similarity.
    """
    if a.ndim == 0 or b.ndim == 0 or len(a) == 0 or len(b) == 0:
        return 0.0
    return float(np.dot(a, b))


def batch_cosine_similarity(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between one query vector and N candidate vectors.

    All vectors must be L2-normalized.
    Returns 1D array of shape (N,).
    """
    if candidates.size == 0:
        return np.array([])
    return np.dot(candidates, query)


def compute_title_similarity(
    candidate_title_emb: np.ndarray,
    job_title_emb: np.ndarray,
) -> float:
    """Compute title similarity score scaled to 0-100."""
    if candidate_title_emb.size == 0 or job_title_emb.size == 0:
        return 30.0
    raw = cosine_similarity(candidate_title_emb, job_title_emb)
    return round(max(0.0, raw) * 100.0, 1)


def compute_description_similarity(
    candidate_profile_emb: np.ndarray,
    job_description_emb: np.ndarray,
) -> float:
    """Compute description similarity score scaled to 0-100."""
    if candidate_profile_emb.size == 0 or job_description_emb.size == 0:
        return 30.0
    raw = cosine_similarity(candidate_profile_emb, job_description_emb)
    return round(max(0.0, raw) * 100.0, 1)
