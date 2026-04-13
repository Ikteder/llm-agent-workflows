from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.metrics.pairwise import cosine_similarity

from app.models.schemas import SourceChunk
from app.retrieval.embed import EmbedderProtocol


@dataclass
class InMemoryVectorStore:
    embedder: EmbedderProtocol
    chunks: list[SourceChunk] = field(default_factory=list)
    matrix: object | None = None

    def build(self, chunks: list[SourceChunk]) -> None:
        self.chunks = chunks
        self.matrix = self.embedder.fit_transform([chunk.content for chunk in chunks])

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kind: str | None = None,
        project: str | None = None,
    ) -> list[SourceChunk]:
        if not self.chunks or self.matrix is None:
            return []

        candidate_indexes = [
            index
            for index, chunk in enumerate(self.chunks)
            if (kind is None or chunk.kind == kind) and (project is None or chunk.project == project)
        ]
        if not candidate_indexes:
            return []

        query_matrix = self.embedder.transform([query])
        candidate_matrix = self.matrix[candidate_indexes]
        scores = cosine_similarity(query_matrix, candidate_matrix)[0]
        ranked = sorted(zip(candidate_indexes, scores), key=lambda item: item[1], reverse=True)[:limit]

        results: list[SourceChunk] = []
        for index, score in ranked:
            chunk = self.chunks[index].model_copy(deep=True)
            chunk.score = float(score)
            results.append(chunk)
        return results
