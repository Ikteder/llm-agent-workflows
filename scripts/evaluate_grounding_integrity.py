from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.models.schemas import GroundingReceipt, SourceChunk
from app.retrieval.provenance import (
    bind_sources,
    create_grounding_receipt,
    filename_only_verify,
    verify_grounding_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "benchmarks" / "grounding-integrity-v1.json"


def _base_sources() -> list[SourceChunk]:
    return bind_sources(
        [
            SourceChunk(
                chunk_id="chunk-report-001",
                project="demo",
                path="C:/checkout/data/docs/report.md",
                source_uri="data/docs/report.md",
                kind="doc",
                content="Atlas reached 0.91 accuracy on the held-out set.",
                score=0.9123456789014,
            ),
            SourceChunk(
                chunk_id="chunk-log-001",
                project="demo",
                path="C:/checkout/data/logs/run.log",
                source_uri="data/logs/run.log",
                kind="log",
                content="Run atlas-17 completed without validation errors.",
                score=0.7123456789014,
            ),
        ]
    )


def _mutate(
    mutation: str,
    receipt: GroundingReceipt,
    sources: list[SourceChunk],
    query: str,
) -> tuple[GroundingReceipt, list[SourceChunk], str]:
    current_receipt = receipt.model_copy(deep=True)
    current_sources = [source.model_copy(deep=True) for source in sources]
    current_query = query
    if mutation == "content":
        current_sources[0].content += " Altered after the answer was produced."
    elif mutation == "missing":
        current_sources.pop(0)
    elif mutation == "reorder":
        current_sources.reverse()
    elif mutation == "uri":
        current_sources[0].source_uri = "mirror/report.md"
    elif mutation == "extra":
        current_sources.append(
            SourceChunk(
                chunk_id="chunk-extra-001",
                project="demo",
                path="C:/checkout/data/docs/extra.md",
                source_uri="data/docs/extra.md",
                kind="doc",
                content="Unrequested evidence.",
                score=0.1,
            )
        )
    elif mutation == "query":
        current_query = "Which run failed?"
    elif mutation == "receipt_id":
        current_receipt.receipt_id = "gr1-000000000000000000000000"
    elif mutation == "evidence_digest":
        current_receipt.evidence_sha256 = "0" * 64
    elif mutation == "duplicate":
        current_sources.append(current_sources[0].model_copy(deep=True))
    elif mutation == "score":
        current_sources[0].score = 0.111111111111
    elif mutation == "citation":
        current_receipt.citations[0].citation_id = "S9"
    elif mutation != "none":
        raise ValueError(f"Unknown mutation: {mutation}")
    return current_receipt, current_sources, current_query


def evaluate(cases_path: Path) -> dict[str, object]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    query = "Which run performed best?"
    sources = _base_sources()
    receipt = create_grounding_receipt(query, sources)
    if receipt is None:
        raise RuntimeError("Fixture did not produce a grounding receipt")

    results: list[dict[str, object]] = []
    for case in payload["cases"]:
        candidate_receipt, current_sources, current_query = _mutate(
            case["mutation"], receipt, sources, query
        )
        findings = verify_grounding_receipt(
            candidate_receipt,
            current_sources,
            query=current_query,
        )
        receipt_prediction = not findings
        baseline_prediction = filename_only_verify(candidate_receipt, current_sources)
        expected = bool(case["expected_valid"])
        results.append(
            {
                "id": case["id"],
                "mutation": case["mutation"],
                "expected_valid": expected,
                "filename_only_prediction": baseline_prediction,
                "receipt_prediction": receipt_prediction,
                "filename_only_correct": baseline_prediction == expected,
                "receipt_correct": receipt_prediction == expected,
                "findings": findings,
            }
        )

    return {
        "schema_version": "1",
        "corpus": payload["name"],
        "case_count": len(results),
        "filename_only_correct": sum(bool(item["filename_only_correct"]) for item in results),
        "receipt_correct": sum(bool(item["receipt_correct"]) for item in results),
        "results": results,
    }


def write_svg(result: dict[str, object], path: Path) -> None:
    case_count = int(result["case_count"])
    baseline = int(result["filename_only_correct"])
    receipt = int(result["receipt_correct"])
    baseline_width = round(440 * baseline / case_count)
    receipt_width = round(440 * receipt / case_count)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="360" viewBox="0 0 760 360" role="img" aria-labelledby="title desc">
  <title id="title">Grounding integrity benchmark</title>
  <desc id="desc">Filename-only baseline correctly classified {baseline} of {case_count} cases. Content-addressed receipts correctly classified {receipt} of {case_count} cases.</desc>
  <rect width="760" height="360" rx="24" fill="#f4f7fb"/>
  <text x="52" y="64" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#15324b">Grounding integrity benchmark</text>
  <text x="52" y="94" font-family="Arial, sans-serif" font-size="15" fill="#536779">Synthetic mutation detection, v1</text>
  <text x="52" y="148" font-family="Arial, sans-serif" font-size="17" fill="#20384d">Filename-only baseline</text>
  <rect x="250" y="126" width="440" height="28" rx="14" fill="#dce5ed"/>
  <rect x="250" y="126" width="{baseline_width}" height="28" rx="14" fill="#d47a3f"/>
  <text x="704" y="147" font-family="Arial, sans-serif" font-size="17" text-anchor="end" fill="#20384d">{baseline}/{case_count}</text>
  <text x="52" y="218" font-family="Arial, sans-serif" font-size="17" fill="#20384d">Grounding receipts</text>
  <rect x="250" y="196" width="440" height="28" rx="14" fill="#dce5ed"/>
  <rect x="250" y="196" width="{receipt_width}" height="28" rx="14" fill="#2a8066"/>
  <text x="675" y="217" font-family="Arial, sans-serif" font-size="17" text-anchor="end" fill="#ffffff">{receipt}/{case_count}</text>
  <text x="52" y="284" font-family="Arial, sans-serif" font-size="15" fill="#536779">Checks exact query, source URI, content digest, rank, score, and receipt identity.</text>
  <text x="52" y="311" font-family="Arial, sans-serif" font-size="14" fill="#6d7f8e">Integrity evidence only. This does not prove semantic entailment or truth.</text>
</svg>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate grounding receipt integrity.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    result = evaluate(args.cases)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.svg:
        write_svg(result, args.svg)
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
