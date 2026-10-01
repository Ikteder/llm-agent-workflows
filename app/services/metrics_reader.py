from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.models.schemas import MetricsTablePreview
from app.agent.tool_policy import confined_path
from app.retrieval.ingest import infer_project


@dataclass
class MetricsReader:
    data_dir: Path

    def list_tables(self, project: str | None = None) -> list[Path]:
        paths = sorted((self.data_dir / "csv").glob("*.csv"))
        if project is None:
            return paths
        return [path for path in paths if infer_project(path) == project]

    def load_table(self, table_name: str) -> tuple[Path, pd.DataFrame]:
        path = confined_path(self.data_dir / "csv", table_name, filename_only=True)
        if not path.exists():
            raise FileNotFoundError(f"Metrics table not found: {table_name}")
        return path, pd.read_csv(path)

    def preview(self, table_name: str, rows: int = 8) -> MetricsTablePreview:
        path, frame = self.load_table(table_name)
        return MetricsTablePreview(
            name=path.name,
            path=str(path),
            project=infer_project(path),
            columns=frame.columns.tolist(),
            row_count=len(frame),
            preview=frame.head(rows).fillna("").to_dict(orient="records"),
        )

    def query(self, project: str | None = None, contains: str | None = None) -> list[MetricsTablePreview]:
        previews: list[MetricsTablePreview] = []
        query = contains.lower() if contains else None
        for path in self.list_tables(project):
            frame = pd.read_csv(path)
            if query:
                haystack = " ".join(frame.columns.astype(str)).lower() + " " + frame.head(20).to_csv(index=False).lower()
                if query not in haystack:
                    continue
            previews.append(
                MetricsTablePreview(
                    name=path.name,
                    path=str(path),
                    project=infer_project(path),
                    columns=frame.columns.tolist(),
                    row_count=len(frame),
                    preview=frame.head(6).fillna("").to_dict(orient="records"),
                )
            )
        return previews
