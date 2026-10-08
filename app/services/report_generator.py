from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Template

from app.agent.tool_policy import confined_path
from app.models.schemas import ReportArtifact, SourceChunk

HTML_TEMPLATE = Template(
    """
    <html>
      <head>
        <meta charset="utf-8" />
        <title>{{ title }}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; color: #182230; }
          h1, h2 { color: #0f3d5e; }
          .meta { color: #5f6b7a; margin-bottom: 24px; }
          pre { background: #f4f7fa; padding: 12px; border-radius: 10px; white-space: pre-wrap; }
          .source { margin-bottom: 14px; padding: 12px; background: #f7fbff; border-left: 4px solid #4f9ec4; }
        </style>
      </head>
      <body>
        <h1>{{ title }}</h1>
        <p class="meta">Generated at {{ created_at }}</p>
        <h2>Question</h2>
        <p>{{ question }}</p>
        <h2>Summary</h2>
        <pre>{{ summary }}</pre>
        <h2>Sources</h2>
        {% for source in sources %}
        <div class="source">
          <strong>{{ source.path }}</strong>
          <div>{{ source.content[:400] }}</div>
        </div>
        {% endfor %}
      </body>
    </html>
    """
)


@dataclass
class ReportGenerator:
    output_dir: Path

    def generate(self, *, question: str, summary: str, sources: list[SourceChunk], title: str) -> ReportArtifact:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        stem = re.sub(r"[^a-z0-9_-]+", "_", title.lower()).strip("_")[:48] or "report"
        report_dir = self.output_dir / "generated"
        report_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = confined_path(report_dir, f"{timestamp}_{stem}.md", filename_only=True)
        html_path = confined_path(report_dir, f"{timestamp}_{stem}.html", filename_only=True)

        markdown = [
            f"# {title}",
            "",
            f"Generated at: `{datetime.now(UTC).isoformat()}`",
            "",
            "## Question",
            "",
            question,
            "",
            "## Summary",
            "",
            summary,
            "",
            "## Sources",
            "",
        ]
        for source in sources:
            markdown.extend(
                [
                    f"- `{source.path}`",
                    f"  Extract: {source.content[:280].replace(chr(10), ' ')}",
                ]
            )

        markdown_path.write_text("\n".join(markdown), encoding="utf-8")
        html_path.write_text(
            HTML_TEMPLATE.render(
                title=title,
                question=question,
                summary=summary,
                sources=sources,
                created_at=datetime.now(UTC).isoformat(),
            ),
            encoding="utf-8",
        )
        return ReportArtifact(
            title=title,
            markdown_path=str(markdown_path),
            html_path=str(html_path),
            summary=summary.splitlines()[0] if summary else title,
        )
