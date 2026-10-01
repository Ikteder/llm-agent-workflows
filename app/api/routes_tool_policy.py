from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ToolApprovalDecision, ToolApprovalDecisionResult


def build_tool_policy_router() -> APIRouter:
    router = APIRouter(prefix="/api/tool-policy", tags=["tool-policy"])

    @router.get("/manifest")
    def manifest(request: Request) -> dict:
        return request.app.state.container.tool_policy.manifest()

    @router.post("/approvals/{approval_id}", response_model=ToolApprovalDecisionResult)
    def decide(approval_id: str, payload: ToolApprovalDecision, request: Request) -> ToolApprovalDecisionResult:
        try:
            pending = request.app.state.container.tool_policy.decide(
                approval_id,
                session_id=payload.session_id,
                approve=payload.decision == "approve",
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return ToolApprovalDecisionResult(
            approval_id=pending.approval_id,
            status="approved" if payload.decision == "approve" else "rejected",
            tool_name=pending.tool_name,
            expires_at=pending.expires_at,
        )

    return router
