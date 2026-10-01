from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.agent.graph import AgentWorkflow
from app.agent.memory import SessionMemory
from app.agent.tools import ToolContext
from app.agent.tool_policy import ToolPolicyEngine
from app.api.routes_chat import build_chat_router
from app.api.routes_reports import build_reports_router
from app.api.routes_runs import build_runs_router
from app.api.routes_tool_policy import build_tool_policy_router
from app.retrieval.embed import build_embedder
from app.retrieval.ingest import build_corpus
from app.retrieval.vector_store import InMemoryVectorStore
from app.services.compare_runs import RunComparator
from app.services.metrics_reader import MetricsReader
from app.services.report_generator import ReportGenerator


class AppContainer:
    def __init__(self, root_dir: Path) -> None:
        load_dotenv(root_dir / ".env")
        data_dir = root_dir / os.getenv("APP_DATA_DIR", "data")
        artifacts_dir = root_dir / "artifacts"
        chunks, project_summaries = build_corpus(data_dir)
        vector_store = InMemoryVectorStore(build_embedder(os.getenv("EMBEDDING_BACKEND", "tfidf")))
        vector_store.build(chunks)
        self.projects = project_summaries
        self.tool_context = ToolContext(
            data_dir=data_dir,
            vector_store=vector_store,
            metrics_reader=MetricsReader(data_dir),
            comparator=RunComparator(data_dir),
            report_generator=ReportGenerator(artifacts_dir),
        )
        self.memory = SessionMemory(Path(os.getenv("SESSION_DB_PATH", str(artifacts_dir / "generated" / "sessions.db"))))
        policy_secret = os.getenv("TOOL_POLICY_SECRET")
        self.tool_policy = ToolPolicyEngine(
            secret=policy_secret.encode("utf-8") if policy_secret else secrets.token_bytes(32),
            audit_path=Path(
                os.getenv(
                    "TOOL_POLICY_AUDIT_PATH",
                    str(artifacts_dir / "generated" / "tool-policy-audit.jsonl"),
                )
            ),
            allowed_projects={project.name for project in project_summaries},
        )
        self.workflow = AgentWorkflow(self.tool_context, self.memory, self.tool_policy)


def create_app() -> FastAPI:
    root_dir = Path(__file__).resolve().parents[1]
    container = AppContainer(root_dir)

    app = FastAPI(
        title="LLM Agent for Experiment and Knowledge Workflows",
        version="0.2.0",
        description="Grounded Q&A, run comparison, and report generation over experiment artifacts.",
    )
    app.state.container = container
    app.include_router(build_chat_router())
    app.include_router(build_runs_router())
    app.include_router(build_reports_router())
    app.include_router(build_tool_policy_router())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
