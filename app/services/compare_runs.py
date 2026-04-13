from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.models.schemas import CompareRunsRequest, CompareRunsResult
from app.retrieval.ingest import infer_project


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.copy()
    if "model_key" in renamed.columns and "model_name" not in renamed.columns:
        renamed["model_name"] = renamed["model_key"]
    if "dataset_name" in renamed.columns and "dataset" not in renamed.columns:
        renamed["dataset"] = renamed["dataset_name"]
    if "format_name" in renamed.columns:
        renamed["variant"] = renamed["format_name"]
    return renamed


@dataclass
class RunComparator:
    data_dir: Path

    def _iter_frames(self, project: str | None = None) -> list[tuple[Path, pd.DataFrame]]:
        frames: list[tuple[Path, pd.DataFrame]] = []
        for path in sorted((self.data_dir / "csv").glob("*.csv")):
            if project and infer_project(path) != project:
                continue
            frame = _normalize_columns(pd.read_csv(path))
            frame["source_file"] = path.name
            frame["project"] = infer_project(path)
            frames.append((path, frame))
        return frames

    def compare(self, request: CompareRunsRequest) -> CompareRunsResult:
        rows: list[dict[str, object]] = []
        source_files: list[str] = []
        metric = request.metric
        for path, frame in self._iter_frames(request.project):
            filtered = frame
            if request.dataset and "dataset" in filtered.columns:
                filtered = filtered[filtered["dataset"].astype(str).str.contains(request.dataset, case=False, na=False)]
            if request.category and "category" in filtered.columns:
                filtered = filtered[filtered["category"].astype(str).str.contains(request.category, case=False, na=False)]
            if request.models and "model_name" in filtered.columns:
                pattern = "|".join(request.models)
                filtered = filtered[filtered["model_name"].astype(str).str.contains(pattern, case=False, na=False)]
            if filtered.empty:
                continue
            source_files.append(str(path))
            rows.extend(filtered.to_dict(orient="records"))

        if not rows:
            return CompareRunsResult(
                request=request,
                rows=[],
                source_files=[],
                metric_used=metric,
                summary="No matching runs were found for that request.",
            )

        frame = pd.DataFrame(rows)
        if metric is None:
            metric = next(
                (
                    candidate
                    for candidate in ["accuracy", "f1", "auroc", "latency_ms", "throughput_items_per_sec", "throughput", "model_size_mb"]
                    if candidate in frame.columns
                ),
                None,
            )

        if metric and metric in frame.columns:
            frame = frame.sort_values(metric, ascending=request.prefer_lowest)
        limited = frame.head(request.limit)
        if metric and metric in limited.columns and not limited.empty:
            best = limited.iloc[0]
            model_name = best.get("model_name", best.get("monitor_name", "Best row"))
            qualifier = "lowest" if request.prefer_lowest else "highest"
            summary = f"{model_name} had the {qualifier} {metric} in the matching runs."
        else:
            summary = f"Found {len(limited)} matching run rows."

        return CompareRunsResult(
            request=request,
            rows=limited.fillna("").to_dict(orient="records"),
            source_files=source_files,
            metric_used=metric,
            summary=summary,
        )
