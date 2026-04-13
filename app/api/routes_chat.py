from __future__ import annotations

from fastapi import APIRouter, Request

from app.models.schemas import AgentResponse, ChatRequest, ChatSessionHistory


def build_chat_router() -> APIRouter:
    router = APIRouter(prefix="/api/chat", tags=["chat"])

    @router.post("", response_model=AgentResponse)
    def chat(payload: ChatRequest, request: Request) -> AgentResponse:
        container = request.app.state.container
        return container.workflow.answer(payload)

    @router.get("/sessions/{session_id}", response_model=ChatSessionHistory)
    def get_session(session_id: str, request: Request) -> ChatSessionHistory:
        container = request.app.state.container
        return container.memory.history(session_id)

    return router
