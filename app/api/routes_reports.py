from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.models.schemas import ChatRequest, ReportArtifact


class ReportRequest(BaseModel):
    question: str
    project: str | None = None
    session_id: str = "report-session"


def build_reports_router() -> APIRouter:
    router = APIRouter(prefix="/api/reports", tags=["reports"])

    @router.post("/generate", response_model=ReportArtifact)
    def create_report(payload: ReportRequest, request: Request) -> ReportArtifact:
        container = request.app.state.container
        response = container.workflow.answer(
            ChatRequest(
                session_id=payload.session_id,
                question=payload.question,
                project=payload.project,
                generate_report=True,
            )
        )
        if response.report is None:
            raise RuntimeError("Report generation did not produce an artifact.")
        return response.report

    return router
