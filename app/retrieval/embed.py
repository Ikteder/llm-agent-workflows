from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class EmbedderProtocol:
    def fit_transform(self, texts: list[str]):
        raise NotImplementedError

    def transform(self, texts: list[str]):
        raise NotImplementedError


@dataclass
class TfidfEmbedder(EmbedderProtocol):
    max_features: int = 4000

    def __post_init__(self) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
            stop_words="english",
        )

    def fit_transform(self, texts: list[str]):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts: list[str]):
        return self.vectorizer.transform(texts)


class SentenceTransformerEmbedder(EmbedderProtocol):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def fit_transform(self, texts: list[str]):
        return np.asarray(self.model.encode(texts, normalize_embeddings=True))

    def transform(self, texts: list[str]):
        return np.asarray(self.model.encode(texts, normalize_embeddings=True))


def build_embedder(name: str) -> EmbedderProtocol:
    normalized = name.lower().strip()
    if normalized in {"sentence-transformer", "sentence_transformer", "sbert"}:
        return SentenceTransformerEmbedder()
    return TfidfEmbedder()
