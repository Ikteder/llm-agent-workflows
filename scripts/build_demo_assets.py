from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.main import AppContainer
from app.models.schemas import BenchmarkQuestion, BenchmarkResult, ChatRequest


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
GENERATED_DIR = ARTIFACTS_DIR / "generated"
GRAPHICS_DIR = ROOT / "docs" / "graphics"


def load_questions() -> list[BenchmarkQuestion]:
    payload = json.loads((ARTIFACTS_DIR / "benchmark_questions.json").read_text(encoding="utf-8"))
    return [BenchmarkQuestion.model_validate(item) for item in payload]


def evaluate_questions(container: AppContainer, questions: list[BenchmarkQuestion]) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    for question in questions:
        response = container.workflow.answer(
            ChatRequest(
                session_id=f"eval-{question.question_id}",
                question=question.question,
                project=question.project,
                generate_report=False,
            )
        )
        cited_sources = [source.path for source in response.sources]
        answer_lower = response.answer.lower()
        keyword_hits = sum(keyword.lower() in answer_lower for keyword in question.expected_keywords)
        hit_rate = keyword_hits / max(len(question.expected_keywords), 1)
        source_hit = any(question.required_source in path for path in cited_sources) or (
            question.required_source in response.answer
        )
        results.append(
            BenchmarkResult(
                question_id=question.question_id,
                question=question.question,
                expected_source=question.required_source,
                cited_sources=cited_sources,
                expected_keywords=question.expected_keywords,
                answer=response.answer,
                source_hit=source_hit,
                keyword_hit_rate=hit_rate,
                correct=source_hit and hit_rate >= 0.5,
                latency_ms=response.latency_ms or 0.0,
            )
        )
    return results


def write_eval_outputs(results: list[BenchmarkResult]) -> dict[str, float]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "question_count": float(len(results)),
        "retrieval_hit_rate": float(np.mean([result.source_hit for result in results])),
        "answer_usefulness": float(np.mean([result.correct for result in results])),
        "grounded_keyword_rate": float(np.mean([result.keyword_hit_rate for result in results])),
        "average_latency_ms": float(np.mean([result.latency_ms for result in results])),
        "hallucination_rate_proxy": float(np.mean([not result.source_hit for result in results])),
    }
    (GENERATED_DIR / "eval_results.json").write_text(
        json.dumps([result.model_dump() for result in results], indent=2),
        encoding="utf-8",
    )
    (GENERATED_DIR / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def write_sample_report(container: AppContainer) -> None:
    response = container.workflow.answer(
        ChatRequest(
            session_id="sample-report",
            question="Generate a short experiment report comparing the strongest deployment-ready results across the predictive maintenance, model export, and computer vision projects.",
            project=None,
            generate_report=True,
        )
    )
    if response.report:
        markdown_path = Path(response.report.markdown_path)
        html_path = Path(response.report.html_path)
        stable_markdown = GENERATED_DIR / "sample_cross_project_report.md"
        stable_html = GENERATED_DIR / "sample_cross_project_report.html"
        stable_markdown.write_text(markdown_path.read_text(encoding="utf-8"), encoding="utf-8")
        stable_html.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
        (GENERATED_DIR / "sample_report_paths.json").write_text(
            json.dumps(
                response.report.model_dump()
                | {"stable_markdown_path": str(stable_markdown), "stable_html_path": str(stable_html)},
                indent=2,
            ),
            encoding="utf-8",
        )


def _load_font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def create_showcase_graphics(summary: dict[str, float], results: list[BenchmarkResult]) -> None:
    GRAPHICS_DIR.mkdir(parents=True, exist_ok=True)

    plt.style.use("seaborn-v0_8-whitegrid")
    labels = ["Retrieval Hit", "Usefulness", "Groundedness"]
    values = [
        summary["retrieval_hit_rate"],
        summary["answer_usefulness"],
        summary["grounded_keyword_rate"],
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(labels, values, color=["#2a7f62", "#1e6aa7", "#c56c2d"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("Agent Evaluation Snapshot")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.2f}", ha="center")
    fig.tight_layout()
    fig.savefig(GRAPHICS_DIR / "agent_eval_dashboard.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    latencies = [result.latency_ms for result in results]
    ax.hist(latencies, bins=8, color="#4a90c2", edgecolor="white")
    ax.set_title("Response Latency Distribution")
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Questions")
    fig.tight_layout()
    fig.savefig(GRAPHICS_DIR / "agent_latency_histogram.png", dpi=200)
    plt.close(fig)

    canvas = Image.new("RGB", (1600, 900), "#f2f7fb")
    draw = ImageDraw.Draw(canvas)
    title_font = _load_font(50)
    section_font = _load_font(26)
    body_font = _load_font(20)

    draw.rounded_rectangle((40, 40, 1560, 860), radius=30, fill="#ffffff", outline="#d6e3ee")
    draw.rounded_rectangle((70, 95, 1530, 180), radius=24, fill="#0c4a6e")
    draw.text((110, 115), "LLM Agent for Experiment and Knowledge Workflows", fill="#ffffff", font=title_font)
    draw.text((110, 210), "Chat over experiment docs, CSV metrics, logs, and report artifacts", fill="#2d4457", font=section_font)

    draw.rounded_rectangle((90, 280, 860, 820), radius=24, fill="#f8fbfe", outline="#d9e8f3")
    draw.text((120, 310), "Sample Analyst Question", fill="#0c4a6e", font=section_font)
    question = "Which model performed best on CIFAR-10 and what trade-off should I note for deployment?"
    draw.multiline_text((120, 360), textwrap.fill(question, width=48), fill="#203445", font=body_font, spacing=8)

    response_text = (
        "ConvNeXt-Tiny had the strongest CIFAR-10 accuracy at 0.9267, but MobileNetV3 remained the fastest "
        "option at 379.7 ms with a much smaller deployment footprint. Sources: efficient_robust_cv_leaderboard.csv"
    )
    draw.text((120, 470), "Grounded Response", fill="#0c4a6e", font=section_font)
    draw.multiline_text((120, 520), textwrap.fill(response_text, width=52), fill="#203445", font=body_font, spacing=8)

    draw.rounded_rectangle((930, 280, 1490, 520), radius=24, fill="#f8fbfe", outline="#d9e8f3")
    draw.text((960, 310), "Evaluation Snapshot", fill="#0c4a6e", font=section_font)
    snapshot_lines = [
        f"Retrieval hit rate: {summary['retrieval_hit_rate']:.2%}",
        f"Answer usefulness: {summary['answer_usefulness']:.2%}",
        f"Grounded keyword rate: {summary['grounded_keyword_rate']:.2%}",
        f"Average latency: {summary['average_latency_ms']:.1f} ms",
    ]
    draw.multiline_text((960, 365), "\n".join(snapshot_lines), fill="#203445", font=body_font, spacing=14)

    draw.rounded_rectangle((930, 560, 1490, 820), radius=24, fill="#f8fbfe", outline="#d9e8f3")
    draw.text((960, 590), "Tooling", fill="#0c4a6e", font=section_font)
    tooling = "\n".join(
        [
            "search_docs",
            "search_logs",
            "compare_runs",
            "read_metrics_csv",
            "generate_report",
            "show_confusion_matrix",
        ]
    )
    draw.multiline_text((960, 645), tooling, fill="#203445", font=body_font, spacing=14)
    canvas.save(GRAPHICS_DIR / "agent_ui_showcase.png")

    banner = Image.new("RGB", (1600, 620), "#0f2740")
    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle((50, 60, 1550, 560), radius=36, fill="#153d60", outline="#5fa7d6")
    draw.text((100, 120), "Grounded Experiment Agent", fill="#ffffff", font=title_font)
    draw.multiline_text(
        (100, 210),
        "FastAPI + Streamlit workspace for asking questions over benchmark reports,\n"
        "CSV metrics, experiment logs, and operator summaries with tool traces and report exports.",
        fill="#d9edf8",
        font=section_font,
        spacing=12,
    )
    draw.text(
        (100, 360),
        f"{int(summary['question_count'])} benchmark questions | "
        f"{summary['retrieval_hit_rate']:.0%} source hit rate | "
        f"{summary['answer_usefulness']:.0%} answer usefulness",
        fill="#7be0b5",
        font=section_font,
    )
    banner.save(GRAPHICS_DIR / "project_banner.png")


def write_eval_markdown(summary: dict[str, float]) -> None:
    markdown = [
        "# Agent Evaluation Summary",
        "",
        f"- Benchmark questions: {int(summary['question_count'])}",
        f"- Retrieval hit rate: {summary['retrieval_hit_rate']:.2%}",
        f"- Answer usefulness: {summary['answer_usefulness']:.2%}",
        f"- Grounded keyword rate: {summary['grounded_keyword_rate']:.2%}",
        f"- Average latency: {summary['average_latency_ms']:.1f} ms",
        f"- Hallucination proxy: {summary['hallucination_rate_proxy']:.2%}",
    ]
    (GENERATED_DIR / "evaluation_summary.md").write_text("\n".join(markdown), encoding="utf-8")


def main() -> None:
    container = AppContainer(ROOT)
    questions = load_questions()
    results = evaluate_questions(container, questions)
    summary = write_eval_outputs(results)
    write_sample_report(container)
    create_showcase_graphics(summary, results)
    write_eval_markdown(summary)


if __name__ == "__main__":
    main()
