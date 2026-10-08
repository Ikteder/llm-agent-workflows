from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.models.schemas import (
    CitationIntegrityAudit,
    GroundingCitation,
    GroundingReceipt,
    SourceChunk,
)

CITATION_PATTERN = re.compile(r"\[(S[1-9][0-9]*)\]")
SCORE_DIGITS = 12


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def canonical_source_uri(source: SourceChunk) -> str:
    if source.source_uri:
        return source.source_uri.replace("\\", "/")
    return Path(source.path).name


def bind_sources(sources: list[SourceChunk]) -> list[SourceChunk]:
    bound: list[SourceChunk] = []
    for rank, source in enumerate(sources, start=1):
        item = source.model_copy(deep=True)
        item.source_uri = canonical_source_uri(item)
        item.content = normalize_text(item.content)
        item.content_sha256 = sha256_text(item.content)
        item.retrieval_rank = rank
        item.citation_id = f"S{rank}"
        bound.append(item)
    return bound


def _citation_payload(citation: GroundingCitation) -> dict[str, object]:
    payload = citation.model_dump(mode="json")
    if citation.score is not None:
        payload["score"] = round(citation.score, SCORE_DIGITS)
    return payload


def _evidence_digest(citations: list[GroundingCitation]) -> str:
    payload = [_citation_payload(citation) for citation in citations]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_text(encoded)


def _receipt_id(query_sha256: str, evidence_sha256: str) -> str:
    receipt_payload = f"1\n{query_sha256}\n{evidence_sha256}"
    return f"gr1-{sha256_text(receipt_payload)[:24]}"


def create_grounding_receipt(query: str, sources: list[SourceChunk]) -> GroundingReceipt | None:
    if not sources:
        return None
    citations = [
        GroundingCitation(
            citation_id=source.citation_id or f"S{index}",
            chunk_id=source.chunk_id,
            source_uri=canonical_source_uri(source),
            project=source.project,
            kind=source.kind,
            content_sha256=source.content_sha256 or sha256_text(source.content),
            retrieval_rank=source.retrieval_rank or index,
            score=source.score,
        )
        for index, source in enumerate(sources, start=1)
    ]
    query_sha256 = sha256_text(query.strip())
    evidence_sha256 = _evidence_digest(citations)
    return GroundingReceipt(
        receipt_id=_receipt_id(query_sha256, evidence_sha256),
        query_sha256=query_sha256,
        evidence_sha256=evidence_sha256,
        citations=citations,
    )


def ensure_answer_citations(answer: str, sources: list[SourceChunk]) -> str:
    if not sources or CITATION_PATTERN.search(answer):
        return answer
    tokens = " ".join(f"[{source.citation_id}]" for source in sources[:3] if source.citation_id)
    if not tokens:
        return answer
    return f"{answer.rstrip()}\n\nEvidence: {tokens}"


def audit_answer_citations(answer: str, sources: list[SourceChunk]) -> CitationIntegrityAudit:
    if not sources:
        return CitationIntegrityAudit(status="not_applicable", source_count=0)
    found = list(dict.fromkeys(CITATION_PATTERN.findall(answer)))
    available = {source.citation_id for source in sources if source.citation_id}
    resolved = [citation for citation in found if citation in available]
    unresolved = [citation for citation in found if citation not in available]
    findings: list[str] = []
    if not found:
        findings.append("MISSING_ANSWER_CITATION")
    if unresolved:
        findings.append("UNRESOLVED_ANSWER_CITATION")
    return CitationIntegrityAudit(
        status="verified" if not findings else "failed",
        source_count=len(sources),
        citations_found=found,
        resolved_citations=resolved,
        unresolved_citations=unresolved,
        findings=findings,
    )


def verify_grounding_receipt(
    receipt: GroundingReceipt,
    current_sources: list[SourceChunk],
    *,
    query: str | None = None,
) -> list[str]:
    findings: list[str] = []
    receipt_chunk_ids = [citation.chunk_id for citation in receipt.citations]
    receipt_citation_ids = [citation.citation_id for citation in receipt.citations]
    receipt_ranks = [citation.retrieval_rank for citation in receipt.citations]
    if len(set(receipt_chunk_ids)) != len(receipt_chunk_ids):
        findings.append("DUPLICATE_RECEIPT_CHUNK")
    if len(set(receipt_citation_ids)) != len(receipt_citation_ids):
        findings.append("DUPLICATE_RECEIPT_CITATION")
    if receipt_ranks != list(range(1, len(receipt.citations) + 1)):
        findings.append("INVALID_RECEIPT_RANKS")
    if any(
        citation.citation_id != f"S{citation.retrieval_rank}" for citation in receipt.citations
    ):
        findings.append("CITATION_RANK_BINDING_MISMATCH")
    expected_evidence = _evidence_digest(receipt.citations)
    if expected_evidence != receipt.evidence_sha256:
        findings.append("EVIDENCE_DIGEST_MISMATCH")
    expected_receipt_id = _receipt_id(receipt.query_sha256, receipt.evidence_sha256)
    if expected_receipt_id != receipt.receipt_id:
        findings.append("RECEIPT_ID_MISMATCH")
    if query is not None and sha256_text(query.strip()) != receipt.query_sha256:
        findings.append("QUERY_DIGEST_MISMATCH")

    current_by_id: dict[str, SourceChunk] = {}
    duplicate_ids: set[str] = set()
    for source in current_sources:
        if source.chunk_id in current_by_id:
            duplicate_ids.add(source.chunk_id)
        current_by_id[source.chunk_id] = source
    if duplicate_ids:
        findings.append("DUPLICATE_CURRENT_CHUNK")

    expected_ids = {citation.chunk_id for citation in receipt.citations}
    current_ids = {source.chunk_id for source in current_sources}
    if current_ids - expected_ids:
        findings.append("UNEXPECTED_CHUNK")

    for citation in receipt.citations:
        source = current_by_id.get(citation.chunk_id)
        if source is None:
            findings.append(f"MISSING_CHUNK:{citation.citation_id}")
            continue
        if canonical_source_uri(source) != citation.source_uri:
            findings.append(f"SOURCE_URI_MISMATCH:{citation.citation_id}")
        if sha256_text(source.content) != citation.content_sha256:
            findings.append(f"CONTENT_DIGEST_MISMATCH:{citation.citation_id}")
        current_rank = current_sources.index(source) + 1
        if current_rank != citation.retrieval_rank:
            findings.append(f"RETRIEVAL_RANK_MISMATCH:{citation.citation_id}")
        current_score = round(source.score, SCORE_DIGITS) if source.score is not None else None
        receipt_score = round(citation.score, SCORE_DIGITS) if citation.score is not None else None
        if current_score != receipt_score:
            findings.append(f"RETRIEVAL_SCORE_MISMATCH:{citation.citation_id}")
    return findings


def filename_only_verify(receipt: GroundingReceipt, current_sources: list[SourceChunk]) -> bool:
    expected = {Path(citation.source_uri).name for citation in receipt.citations}
    current = {Path(canonical_source_uri(source)).name for source in current_sources}
    return expected.issubset(current)
