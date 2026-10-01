from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.schemas import ChatRequest, ReportArtifact


class ReportRequest(BaseModel):
    question: str
    project: str | None = None
    session_id: str = "report-session"
    approval_id: str | None = None


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
                approval_id=payload.approval_id,
            )
        )
        if response.report is None:
            if response.approval_required is not None:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Report generation requires exact-intent approval.",
                        "approval_required": response.approval_required.model_dump(mode="json"),
                    },
                )
            raise HTTPException(status_code=403, detail="Report generation was denied by tool policy.")
        return response.report

    return router
