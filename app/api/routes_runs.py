from __future__ import annotations

from fastapi import APIRouter, Request

from app.models.schemas import (
    CompareRunsRequest,
    CompareRunsResult,
    MetricsTablePreview,
    ProjectSummary,
)


def build_runs_router() -> APIRouter:
    router = APIRouter(prefix="/api/runs", tags=["runs"])

    @router.get("/projects", response_model=list[ProjectSummary])
    def list_projects(request: Request) -> list[ProjectSummary]:
        return request.app.state.container.projects

    @router.get("/metrics", response_model=list[MetricsTablePreview])
    def list_metrics(request: Request, project: str | None = None, contains: str | None = None) -> list[MetricsTablePreview]:
        container = request.app.state.container
        return container.tool_context.metrics_reader.query(project=project, contains=contains)

    @router.post("/compare", response_model=CompareRunsResult)
    def compare(payload: CompareRunsRequest, request: Request) -> CompareRunsResult:
        container = request.app.state.container
        return container.tool_context.comparator.compare(payload)

    return router
