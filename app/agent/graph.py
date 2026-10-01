from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from app.agent.memory import SessionMemory
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import (
    ToolContext,
    compare_runs,
    generate_report,
    read_metrics_csv,
    search_docs,
    search_logs,
    show_confusion_matrix,
    summarize_failures,
)
from app.agent.tool_policy import ToolInvocation, ToolPolicyEngine
from app.models.schemas import AgentResponse, ChatRequest, ReportArtifact, SourceChunk, ToolCall


PROJECT_KEYWORDS = {
    "predictive_maintenance": ["predictive maintenance", "drift", "sensor", "early warning", "maintenance"],
    "efficient_robust_cv": ["cifar", "breastmnist", "convnext", "mobilenetv3", "vision", "robustness", "cv benchmark"],
    "model_export": ["onnx", "torchscript", "model export", "distilgpt2", "verification", "npz"],
}

MODEL_KEYWORDS = [
    "resnet",
    "mobilenet",
    "efficientnet",
    "convnext",
    "xgboost",
    "logistic",
    "distilgpt2",
    "gru",
    "transformer",
    "random forest",
    "isolation forest",
]

METRIC_KEYWORDS = {
    "auroc": ["auroc"],
    "f1": ["f1"],
    "accuracy": ["accuracy"],
    "precision": ["precision"],
    "recall": ["recall"],
    "latency_ms": ["latency", "slow", "fast", "faster", "fastest"],
    "throughput_items_per_sec": ["throughput", "items/sec", "tokens/sec"],
    "model_size_mb": ["model size", "size", "smallest"],
    "lead_time_cycles": ["lead time", "warning time"],
    "false_alarm_rate": ["false alarm"],
    "robustness_drop": ["robustness drop", "corruption drop", "robust", "more robust", "robustness"],
    "sensitivity": ["sensitivity"],
}


def _infer_project(query: str, explicit_project: str | None = None) -> str | None:
    if explicit_project:
        return explicit_project
    lowered = query.lower()
    for project, phrases in PROJECT_KEYWORDS.items():
        if any(phrase in lowered for phrase in phrases):
            return project
    return None


def _infer_metric(query: str) -> tuple[str | None, bool]:
    lowered = query.lower()
    prefer_lowest = any(token in lowered for token in ["lowest", "fastest", "smallest", "least", "more robust"])
    for metric, phrases in METRIC_KEYWORDS.items():
        if any(phrase in lowered for phrase in phrases):
            return metric, prefer_lowest
    return None, prefer_lowest


def _infer_models(query: str) -> list[str]:
    lowered = query.lower()
    return [keyword for keyword in MODEL_KEYWORDS if keyword in lowered]


def _infer_dataset(query: str) -> str | None:
    lowered = query.lower()
    for dataset in ["cifar-10", "cifar", "breastmnist"]:
        if dataset in lowered:
            return "CIFAR-10" if dataset.startswith("cifar") else "BreastMNIST"
    return None


def _infer_format(query: str) -> str | None:
    lowered = query.lower()
    for format_name in ["onnx", "torchscript", "npz", "baseline"]:
        if format_name in lowered:
            return format_name
    return None


def _extractive_summary(query: str, chunks: list[SourceChunk], limit: int = 4) -> str:
    if not chunks:
        return "I could not retrieve grounded evidence for that question from the current corpus."
    query_terms = {term for term in query.lower().replace("?", " ").split() if len(term) > 2}
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for chunk in chunks:
        for sentence in chunk.content.replace("\n", " ").split(". "):
            normalized = sentence.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            score = sum(term in normalized.lower() for term in query_terms)
            scored.append((score, normalized))
    selected = [sentence for _, sentence in sorted(scored, reverse=True)[:limit] if sentence]
    return "\n".join(f"- {sentence.rstrip('.')}" for sentence in selected)


def _call_openai_if_available(question: str, memory_context: str, tool_context: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    backend = os.getenv("LLM_BACKEND", "heuristic").lower()
    if backend != "openai" or not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"Memory context:\n{memory_context}\n\n"
                                f"Question:\n{question}\n\n"
                                f"Tool outputs and sources:\n{tool_context}\n\n"
                                "Answer with source citations."
                            ),
                        }
                    ],
                },
            ],
        )
        return response.output_text
    except Exception:
        return None


@dataclass
class AgentWorkflow:
    tool_context: ToolContext
    memory: SessionMemory
    tool_policy: ToolPolicyEngine

    def answer(self, request: ChatRequest) -> AgentResponse:
        started = time.perf_counter()
        if request.project is not None and not self.tool_policy.validate_project(request.project):
            return AgentResponse(
                session_id=request.session_id,
                question=request.question,
                answer=f"Project scope `{request.project}` is not available to this agent.",
                project=request.project,
                intent="policy_denied",
                tools_used=[
                    ToolCall(
                        name="tool_policy",
                        arguments={"project": request.project},
                        summary="Denied an unknown project scope before tool planning.",
                    )
                ],
                grounded=False,
                latency_ms=(time.perf_counter() - started) * 1000.0,
            )
        project = _infer_project(request.question, request.project)
        metric, prefer_lowest = _infer_metric(request.question)
        models = _infer_models(request.question)
        dataset = _infer_dataset(request.question)
        format_name = _infer_format(request.question)
        category = "anomaly_detection" if "anomaly" in request.question.lower() else None
        lowered = request.question.lower()

        tools_used: list[ToolCall] = []
        sources: list[SourceChunk] = []
        intent = "retrieval"
        answer = ""
        report = None
        approval_required = None
        approval_receipt = None

        def create_report_with_policy(title: str) -> ReportArtifact | None:
            nonlocal approval_required, approval_receipt
            source_bindings = [source.model_dump(mode="json") for source in sources[:6]]
            arguments = {
                "title": title,
                "question": request.question,
                "summary": answer,
                "sources": source_bindings,
            }
            if request.approval_id:
                decision = self.tool_policy.consume(
                    request.approval_id,
                    session_id=request.session_id,
                    tool_name="generate_report",
                    project=project,
                )
            else:
                decision = self.tool_policy.authorize(
                    ToolInvocation(
                        session_id=request.session_id,
                        tool_name="generate_report",
                        arguments=arguments,
                        project=project,
                    )
                )
            if decision.status == "pending":
                approval_required = decision.approval_request
                tools_used.append(
                    ToolCall(
                        name="tool_policy",
                        arguments={
                            "tool_name": "generate_report",
                            "project": project,
                            "invocation_digest": approval_required.invocation_digest if approval_required else None,
                        },
                        summary="Paused report generation for exact-intent approval.",
                    )
                )
                return None
            if decision.status == "denied":
                tools_used.append(
                    ToolCall(
                        name="tool_policy",
                        arguments={"tool_name": "generate_report", "project": project},
                        summary=f"Denied report generation: {decision.reason}.",
                    )
                )
                return None

            approval_receipt = decision.receipt
            approved_arguments = decision.arguments or arguments
            approved_sources = [SourceChunk.model_validate(item) for item in approved_arguments["sources"]]
            artifact = generate_report(
                self.tool_context,
                title=str(approved_arguments["title"]),
                question=str(approved_arguments["question"]),
                summary=str(approved_arguments["summary"]),
                sources=approved_sources,
            )
            tools_used.append(
                ToolCall(
                    name="generate_report",
                    arguments={"title": artifact.title, "approval_receipt": approval_receipt},
                    summary=f"Generated one approved report at {artifact.markdown_path}",
                )
            )
            return artifact

        if any(token in lowered for token in ["compare", "best", "highest", "lowest", "fastest", "smallest", "more robust"]) or (
            metric is not None and ("which" in lowered or "what" in lowered)
        ):
            intent = "compare_runs"
            result = compare_runs(
                self.tool_context,
                project=project,
                metric=metric,
                dataset=dataset,
                category=category,
                models=models,
                prefer_lowest=prefer_lowest,
            )
            tools_used.append(
                ToolCall(
                    name="compare_runs",
                    arguments=result.request.model_dump(),
                    summary=result.summary,
                )
            )
            for source_file in result.source_files[:3]:
                sources.append(
                    SourceChunk(
                        chunk_id=f"source-{len(sources) + 1}",
                        project=project or "shared",
                        path=source_file,
                        kind="csv",
                        content=f"Derived comparison rows from {Path(source_file).name}",
                    )
                )
            if result.rows and result.metric_used:
                best = result.rows[0]
                model_name = best.get("model_name", best.get("monitor_name", "Top row"))
                dataset_label = best.get("dataset", "")
                metric_value = best.get(result.metric_used, "")
                project_label = best.get("project", "")
                variant_label = best.get("variant", best.get("format_name", best.get("format", "")))
                project_detail = f" in {project_label.replace('_', ' ')}" if project_label else ""
                dataset_detail = f" on {dataset_label}" if dataset_label else ""
                variant_detail = f" using {variant_label}" if variant_label else ""
                detail = ""
                if "source_file" in best:
                    detail = f" Source table: `{best['source_file']}`."
                answer = (
                    f"{model_name} is the strongest match for this query"
                    f"{project_detail}"
                    f"{dataset_detail}"
                    f"{variant_detail}"
                    f" with `{result.metric_used} = {metric_value}`.{detail}"
                )
                if len(result.rows) > 1:
                    answer += "\n\nNext closest rows:\n"
                    for row in result.rows[1:4]:
                        row_name = row.get("model_name", row.get("monitor_name", "row"))
                        row_value = row.get(result.metric_used, "")
                        answer += f"- {row_name}: `{result.metric_used} = {row_value}` from `{row.get('source_file', 'table')}`\n"
            else:
                answer = result.summary

        elif ("files" in lowered or "where should i look" in lowered) and "verification" in lowered:
            intent = "file_lookup"
            previews = read_metrics_csv(self.tool_context, table_name="model_export_verification_summary.csv")
            doc_hits = search_docs(self.tool_context, request.question, project="model_export", limit=2)
            tools_used.extend(
                [
                    ToolCall(
                        name="read_metrics_csv",
                        arguments={"table_name": "model_export_verification_summary.csv"},
                        summary=f"Found {len(previews)} matching metric tables.",
                    ),
                    ToolCall(
                        name="search_docs",
                        arguments={"project": "model_export", "limit": 2},
                        summary=f"Retrieved {len(doc_hits)} model export docs.",
                    ),
                ]
            )
            sources.extend(doc_hits)
            answer_parts = []
            answer_parts.append(
                "Start with the verification table `model_export_verification_summary.csv` for pass/fail and error thresholds."
            )
            if previews:
                sources.append(
                    SourceChunk(
                        chunk_id="verification-file",
                        project="model_export",
                        path=previews[0].path,
                        kind="csv",
                        content=f"Verification table columns: {previews[0].columns}",
                    )
                )
            if doc_hits:
                answer_parts.append(f"Then use `{Path(doc_hits[0].path).name}` for the narrative interpretation.")
            answer = " ".join(answer_parts) if answer_parts else "Look at the verification summary CSV and the Markdown report."

        elif "verification" in lowered or "passed" in lowered or "parity" in lowered:
            intent = "verification_lookup"
            path, frame = self.tool_context.metrics_reader.load_table("model_export_verification_summary.csv")
            tools_used.append(
                ToolCall(
                    name="read_metrics_csv",
                    arguments={"table_name": Path(path).name},
                    summary=f"Loaded verification table with {len(frame)} rows.",
                )
            )
            sources.append(
                SourceChunk(
                    chunk_id="verification-preview",
                    project="model_export",
                    path=str(path),
                    kind="csv",
                    content=f"Verification table loaded from {Path(path).name}",
                )
            )
            matching = frame
            if models:
                pattern = "|".join(models)
                matching = matching[matching["model_key"].astype(str).str.contains(pattern, case=False, na=False)]
            if format_name:
                matching = matching[matching["format_name"].astype(str).str.contains(format_name, case=False, na=False)]
            if not matching.empty:
                row = matching.iloc[0].to_dict()
                answer = (
                    f"`{row.get('model_key')}` in `{row.get('format_name')}` "
                    f"has `passed = {row.get('passed')}` with `max_abs_error = {row.get('max_abs_error')}`."
                )
            else:
                answer = f"The verification table is `{Path(path).name}` and it contains export parity metrics and pass/fail status."

        elif "report" in lowered:
            intent = "generate_report"
            doc_hits = search_docs(self.tool_context, request.question, project=project, limit=4)
            log_hits = search_logs(self.tool_context, request.question, project=project, limit=2)
            sources = doc_hits + log_hits
            tools_used.extend(
                [
                    ToolCall(
                        name="search_docs",
                        arguments={"project": project, "limit": 4},
                        summary=f"Retrieved {len(doc_hits)} document chunks.",
                    ),
                    ToolCall(
                        name="search_logs",
                        arguments={"project": project, "limit": 2},
                        summary=f"Retrieved {len(log_hits)} log chunks.",
                    ),
                ]
            )
            answer = _extractive_summary(request.question, sources)
            report = create_report_with_policy(f"{(project or 'cross_project').replace('_', ' ').title()} report")
            if approval_required is not None:
                answer += "\n\nReport creation is paused until you approve this exact tool call."
            elif report is None:
                answer += "\n\nReport creation was denied by the tool policy."

        elif "log" in lowered:
            intent = "log_lookup"
            log_hits = search_logs(self.tool_context, request.question, project=project, limit=4)
            sources = log_hits
            tools_used.append(
                ToolCall(
                    name="search_logs",
                    arguments={"project": project, "limit": 4},
                    summary=f"Retrieved {len(log_hits)} log chunks.",
                )
            )
            answer = _extractive_summary(request.question, log_hits)

        elif "confusion matrix" in lowered:
            intent = "artifact_lookup"
            project = project or "efficient_robust_cv"
            matches = show_confusion_matrix(self.tool_context, project)
            tools_used.append(
                ToolCall(
                    name="show_confusion_matrix",
                    arguments={"project": project},
                    summary=f"Found {len(matches)} confusion matrix artifacts.",
                )
            )
            if matches:
                answer = "Available confusion matrices:\n" + "\n".join(f"- `{path}`" for path in matches)
            else:
                answer = "I could not find a confusion matrix artifact for that project."

        elif "failure" in lowered:
            intent = "failure_summary"
            project = project or "predictive_maintenance"
            if project == "efficient_robust_cv":
                sources = search_docs(
                    self.tool_context,
                    "gaussian blur gaussian noise brightness contrast cutout compression failure cases",
                    project=project,
                    limit=5,
                )
                tools_used.append(
                    ToolCall(
                        name="search_docs",
                        arguments={"project": project, "limit": 5},
                        summary=f"Retrieved {len(sources)} CV failure-analysis chunks.",
                    )
                )
            else:
                sources = summarize_failures(self.tool_context, project)
                tools_used.append(
                    ToolCall(
                        name="summarize_failures",
                        arguments={"project": project},
                        summary=f"Retrieved {len(sources)} failure-related chunks.",
                    )
                )
            answer = _extractive_summary(request.question, sources)

        elif any(token in lowered for token in ["csv", "table", "metric", "metrics"]):
            intent = "metrics_lookup"
            contains = models[0] if models else dataset
            previews = read_metrics_csv(self.tool_context, project=project, contains=contains)
            tools_used.append(
                ToolCall(
                    name="read_metrics_csv",
                    arguments={"project": project, "contains": contains},
                    summary=f"Found {len(previews)} matching metric tables.",
                )
            )
            if previews:
                top = previews[0]
                answer = (
                    f"The most relevant metrics table is `{top.name}` with {top.row_count} rows and columns "
                    f"{', '.join(top.columns[:8])}."
                )
                for preview in previews[:2]:
                    sources.append(
                        SourceChunk(
                            chunk_id=f"preview-{preview.name}",
                            project=preview.project,
                            path=preview.path,
                            kind="csv",
                            content=f"Preview from {preview.name}: {preview.preview[:2]}",
                        )
                    )
            else:
                answer = "I could not find a matching metrics table."

        else:
            doc_hits = search_docs(self.tool_context, request.question, project=project, limit=5)
            log_hits = search_logs(self.tool_context, request.question, project=project, limit=3)
            sources = doc_hits + log_hits
            tools_used.extend(
                [
                    ToolCall(
                        name="search_docs",
                        arguments={"project": project, "limit": 5},
                        summary=f"Retrieved {len(doc_hits)} document chunks.",
                    ),
                    ToolCall(
                        name="search_logs",
                        arguments={"project": project, "limit": 3},
                        summary=f"Retrieved {len(log_hits)} log chunks.",
                    ),
                ]
            )
            answer = _extractive_summary(request.question, sources)

        memory_context = self.memory.recent_context(request.session_id)
        llm_tool_context = "\n\n".join(
            [f"{source.path}\n{source.content}" for source in sources[:6]]
            + [call.summary for call in tools_used]
        )
        openai_answer = _call_openai_if_available(request.question, memory_context, llm_tool_context)
        if openai_answer:
            answer = openai_answer

        if request.generate_report and report is None and approval_required is None:
            report = create_report_with_policy(f"{(project or 'cross_project').replace('_', ' ').title()} chat report")
            if approval_required is not None:
                answer += "\n\nReport creation is paused until you approve this exact tool call."
            elif report is None:
                answer += "\n\nReport creation was denied by the tool policy."

        self.memory.append(request.session_id, "user", request.question)
        self.memory.append(request.session_id, "assistant", answer)

        latency_ms = (time.perf_counter() - started) * 1000.0
        return AgentResponse(
            session_id=request.session_id,
            question=request.question,
            answer=answer,
            project=project,
            intent=intent,
            tools_used=tools_used,
            sources=sources[:8],
            report=report,
            memory_used=memory_context or None,
            latency_ms=latency_ms,
            grounded=bool(sources or "compare_runs" in intent or "metrics" in intent or "artifact" in intent),
            approval_required=approval_required,
            approval_receipt=approval_receipt,
        )
