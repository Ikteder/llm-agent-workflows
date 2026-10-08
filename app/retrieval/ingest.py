from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from app.models.schemas import ProjectFile, ProjectSummary, SourceChunk

PROJECT_DESCRIPTIONS = {
    "predictive_maintenance": "Early-warning predictive maintenance, drift detection, and operator-facing summaries.",
    "efficient_robust_cv": "Computer vision benchmark comparing accuracy, efficiency, and robustness under corruptions.",
    "model_export": "Model export and inference benchmarking across ONNX, TorchScript, and custom formats.",
}


def infer_project(path: Path) -> str:
    name = path.name.lower()
    if "predictive" in name or "maintenance" in name:
        return "predictive_maintenance"
    if "robust" in name or "cifar" in name or "cv" in name or "breastmnist" in name:
        return "efficient_robust_cv"
    if "export" in name or "onnx" in name or "torchscript" in name or "distilgpt2" in name:
        return "model_export"
    return "shared"


def infer_kind(path: Path) -> str:
    section = path.parent.name.lower()
    if section == "docs":
        return "doc"
    if section == "reports":
        return "doc"
    if section == "logs":
        return "log"
    if section == "csv":
        return "csv"
    if section == "artifacts":
        return "artifact"
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".json", ".log"}:
        return "log"
    return "doc"


def split_markdown(text: str, max_chars: int = 700) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{paragraph}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = paragraph
    if buffer:
        chunks.append(buffer)
    return chunks


def flatten_json(payload: object, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            lines.extend(flatten_json(value, child_prefix))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            child_prefix = f"{prefix}[{index}]"
            lines.extend(flatten_json(value, child_prefix))
    else:
        lines.append(f"{prefix}: {payload}")
    return lines


def chunk_csv(path: Path) -> list[str]:
    rows: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pairs = ", ".join(f"{key}={value}" for key, value in row.items())
            rows.append(f"{path.stem}: {pairs}")
    return rows


def load_text_chunks(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return chunk_csv(path)
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        lines = flatten_json(json.loads(text))
        return split_markdown("\n".join(lines), max_chars=900)
    return split_markdown(text)


def _normalized_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _sha256(value: str) -> str:
    return hashlib.sha256(_normalized_text(value).encode("utf-8")).hexdigest()


def build_corpus(data_dir: Path) -> tuple[list[SourceChunk], list[ProjectSummary]]:
    chunks: list[SourceChunk] = []
    project_files: dict[str, list[ProjectFile]] = {}
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            project = infer_project(path)
            project_files.setdefault(project, []).append(
                ProjectFile(
                    project=project,
                    kind="artifact",
                    path=str(path),
                    label=path.name,
                )
            )
            continue
        project = infer_project(path)
        kind = infer_kind(path)
        project_files.setdefault(project, []).append(
            ProjectFile(project=project, kind=kind, path=str(path), label=path.name)
        )
        try:
            source_uri = path.relative_to(data_dir.parent).as_posix()
        except ValueError:
            source_uri = path.name
        for part_index, part in enumerate(load_text_chunks(path), start=1):
            normalized_part = _normalized_text(part)
            content_sha256 = _sha256(normalized_part)
            stable_key = f"{source_uri}\n{part_index}\n{content_sha256}"
            chunks.append(
                SourceChunk(
                    chunk_id=f"chunk-{_sha256(stable_key)[:20]}",
                    project=project,
                    path=str(path),
                    kind=kind,
                    content=normalized_part,
                    source_uri=source_uri,
                    content_sha256=content_sha256,
                    metadata={"label": path.name, "part_index": part_index},
                )
            )

    summaries = [
        ProjectSummary(
            name=project,
            description=PROJECT_DESCRIPTIONS.get(project, "Shared artifacts and reports."),
            file_count=len(files),
            available_tools=[
                "search_docs",
                "search_logs",
                "compare_runs",
                "read_metrics_csv",
                "generate_report",
                "show_confusion_matrix",
                "summarize_failures",
            ],
            artifacts=files,
        )
        for project, files in sorted(project_files.items())
    ]
    return chunks, summaries
