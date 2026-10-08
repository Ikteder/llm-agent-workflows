from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import (
    CompareRunsRequest,
    MetricsTablePreview,
    ReportArtifact,
    SourceChunk,
)
from app.retrieval.ingest import infer_project
from app.retrieval.vector_store import InMemoryVectorStore
from app.services.compare_runs import RunComparator
from app.services.metrics_reader import MetricsReader
from app.services.report_generator import ReportGenerator


@dataclass
class ToolContext:
    data_dir: Path
    vector_store: InMemoryVectorStore
    metrics_reader: MetricsReader
    comparator: RunComparator
    report_generator: ReportGenerator


def search_docs(context: ToolContext, query: str, project: str | None = None, limit: int = 5) -> list[SourceChunk]:
    return context.vector_store.search(query, project=project, kind="doc", limit=limit)


def search_logs(context: ToolContext, query: str, project: str | None = None, limit: int = 5) -> list[SourceChunk]:
    return context.vector_store.search(query, project=project, kind="log", limit=limit)


def read_metrics_csv(
    context: ToolContext,
    table_name: str | None = None,
    project: str | None = None,
    contains: str | None = None,
) -> list[MetricsTablePreview]:
    if table_name:
        return [context.metrics_reader.preview(table_name)]
    return context.metrics_reader.query(project=project, contains=contains)


def compare_runs(
    context: ToolContext,
    *,
    project: str | None = None,
    metric: str | None = None,
    dataset: str | None = None,
    category: str | None = None,
    models: list[str] | None = None,
    limit: int = 8,
    prefer_lowest: bool = False,
):
    request = CompareRunsRequest(
        project=project,
        metric=metric,
        dataset=dataset,
        category=category,
        models=models or [],
        limit=limit,
        prefer_lowest=prefer_lowest,
    )
    return context.comparator.compare(request)


def generate_report(
    context: ToolContext,
    *,
    title: str,
    question: str,
    summary: str,
    sources: list[SourceChunk],
) -> ReportArtifact:
    return context.report_generator.generate(
        question=question,
        summary=summary,
        sources=sources,
        title=title,
    )


def show_confusion_matrix(context: ToolContext, project: str) -> list[str]:
    matches: list[str] = []
    for path in sorted((context.data_dir / "artifacts").glob("*.png")):
        if infer_project(path) == project and "confusion" in path.name.lower():
            matches.append(str(path))
    return matches


def summarize_failures(context: ToolContext, project: str) -> list[SourceChunk]:
    query = "failure cases failure gallery error patterns operator summary"
    return context.vector_store.search(query, project=project, limit=4)
