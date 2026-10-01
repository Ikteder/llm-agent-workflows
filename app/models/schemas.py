from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    chunk_id: str
    project: str
    path: str
    kind: str
    content: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    summary: str


class ToolApprovalRequest(BaseModel):
    approval_id: str
    tool_name: str
    risk: Literal["read", "write"]
    project: str | None = None
    policy_version: str
    invocation_digest: str
    arguments: dict[str, Any]
    created_at: str
    expires_at: str


class ToolApprovalDecision(BaseModel):
    session_id: str
    decision: Literal["approve", "reject"]


class ToolApprovalDecisionResult(BaseModel):
    approval_id: str
    status: Literal["approved", "rejected"]
    tool_name: str
    expires_at: str


class CompareRunsRequest(BaseModel):
    project: str | None = None
    metric: str | None = None
    dataset: str | None = None
    category: str | None = None
    models: list[str] = Field(default_factory=list)
    limit: int = 10
    prefer_lowest: bool = False


class CompareRunsResult(BaseModel):
    request: CompareRunsRequest
    rows: list[dict[str, Any]]
    source_files: list[str]
    metric_used: str | None = None
    summary: str


class MetricsTablePreview(BaseModel):
    name: str
    path: str
    project: str
    columns: list[str]
    row_count: int
    preview: list[dict[str, Any]]


class ReportArtifact(BaseModel):
    title: str
    markdown_path: str
    html_path: str
    summary: str


class AgentResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    project: str | None = None
    intent: str
    tools_used: list[ToolCall] = Field(default_factory=list)
    sources: list[SourceChunk] = Field(default_factory=list)
    report: ReportArtifact | None = None
    memory_used: str | None = None
    latency_ms: float | None = None
    grounded: bool = True
    approval_required: ToolApprovalRequest | None = None
    approval_receipt: str | None = None


class ChatRequest(BaseModel):
    session_id: str
    question: str
    project: str | None = None
    generate_report: bool = False
    approval_id: str | None = None


class ChatSessionMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class ChatSessionHistory(BaseModel):
    session_id: str
    messages: list[ChatSessionMessage]


class ProjectFile(BaseModel):
    project: str
    kind: str
    path: str
    label: str


class ProjectSummary(BaseModel):
    name: str
    description: str
    file_count: int
    available_tools: list[str]
    artifacts: list[ProjectFile] = Field(default_factory=list)


class BenchmarkQuestion(BaseModel):
    question_id: str
    question: str
    project: str | None = None
    required_source: str
    expected_keywords: list[str]
    notes: str | None = None


class BenchmarkResult(BaseModel):
    question_id: str
    question: str
    expected_source: str
    cited_sources: list[str]
    expected_keywords: list[str]
    answer: str
    source_hit: bool
    keyword_hit_rate: float
    correct: bool
    latency_ms: float
