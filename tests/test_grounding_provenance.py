from __future__ import annotations

from pathlib import Path

from app.models.schemas import ChatRequest, SourceChunk
from app.retrieval.ingest import build_corpus
from app.retrieval.provenance import (
    bind_sources,
    create_grounding_receipt,
    verify_grounding_receipt,
)


def test_chunk_identity_is_independent_of_checkout_root(tmp_path: Path) -> None:
    roots = [tmp_path / "one", tmp_path / "two"]
    ids: list[str] = []
    for root in roots:
        data_dir = root / "data"
        docs_dir = data_dir / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "report.md").write_text("# Result\n\nAtlas reached 0.91 accuracy.\n", encoding="utf-8")
        chunks, _ = build_corpus(data_dir)
        ids.append(chunks[0].chunk_id)
        assert chunks[0].source_uri == "data/docs/report.md"
    assert ids[0] == ids[1]


def test_receipt_detects_content_mutation() -> None:
    sources = bind_sources(
        [
            SourceChunk(
                chunk_id="chunk-a",
                project="demo",
                path="C:/repo/data/docs/a.md",
                source_uri="data/docs/a.md",
                kind="doc",
                content="Original evidence.",
                score=0.75,
            )
        ]
    )
    receipt = create_grounding_receipt("What happened?", sources)
    assert receipt is not None
    assert verify_grounding_receipt(receipt, sources, query="What happened?") == []
    mutated = [sources[0].model_copy(deep=True)]
    mutated[0].content = "Changed evidence."
    assert verify_grounding_receipt(receipt, mutated, query="What happened?") == [
        "CONTENT_DIGEST_MISMATCH:S1"
    ]


def test_agent_response_has_resolvable_receipt(container) -> None:
    response = container.workflow.answer(
        ChatRequest(
            session_id="grounding-receipt-test",
            project="predictive_maintenance",
            question="What does the hybrid fusion approach do in predictive maintenance?",
        )
    )
    assert response.sources
    assert response.grounding_receipt is not None
    assert response.citation_integrity is not None
    assert response.citation_integrity.status == "verified"
    assert "[S1]" in response.answer
    assert response.sources[0].content_sha256
    assert response.sources[0].source_uri.startswith("data/")
    assert verify_grounding_receipt(
        response.grounding_receipt,
        response.sources,
        query=response.question,
    ) == []
