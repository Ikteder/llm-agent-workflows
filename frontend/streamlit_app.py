from __future__ import annotations

import os
import uuid
from pathlib import Path

import requests
import streamlit as st


API_URL = os.getenv("WORKFLOW_AGENT_API", "http://127.0.0.1:8000")
ROOT_DIR = Path(__file__).resolve().parents[1]


def fetch_projects() -> list[dict]:
    try:
        response = requests.get(f"{API_URL}/api/runs/projects", timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def fetch_files(project: str | None) -> list[Path]:
    data_dir = ROOT_DIR / "data"
    if project:
        return [path for path in data_dir.rglob("*") if path.is_file() and project in path.name]
    return [path for path in data_dir.rglob("*") if path.is_file()]


st.set_page_config(page_title="Experiment Workflow Agent", layout="wide")
st.title("LLM Agent for Experiment and Knowledge Workflows")
st.caption("Grounded Q&A over experiment docs, logs, metrics, and report artifacts.")

projects = fetch_projects()
project_names = ["All projects"] + [project["name"] for project in projects]
selected_project = st.sidebar.selectbox("Project", options=project_names)
project_key = None if selected_project == "All projects" else selected_project

session_id = st.sidebar.text_input("Session ID", value=st.session_state.get("session_id", str(uuid.uuid4())[:8]))
st.session_state["session_id"] = session_id

st.sidebar.markdown("### Available Files")
for path in fetch_files(project_key)[:20]:
    st.sidebar.write(path.name)

left, right = st.columns([1.3, 1])

with left:
    question = st.text_area(
        "Ask about runs, reports, failures, or metrics",
        value="Which model performed best on CIFAR-10 and how did MobileNetV3 robust training change robustness drop?",
        height=140,
    )
    generate_report = st.checkbox("Generate report", value=False)
    if st.button("Ask Agent", type="primary"):
        payload = {
            "session_id": session_id,
            "question": question,
            "project": project_key,
            "generate_report": generate_report,
        }
        response = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
        response.raise_for_status()
        st.session_state["last_response"] = response.json()

    result = st.session_state.get("last_response")
    if result:
        st.subheader("Response")
        st.write(result["answer"])
        if result.get("report"):
            st.success(f"Report generated: {result['report']['markdown_path']}")
        st.caption(f"Intent: {result['intent']} | Latency: {result.get('latency_ms', 0):.1f} ms")

with right:
    st.subheader("Cited Sources")
    result = st.session_state.get("last_response")
    if result and result.get("sources"):
        for source in result["sources"]:
            with st.expander(Path(source["path"]).name):
                st.code(source["path"])
                st.write(source["content"])
    else:
        st.info("Ask a question to see grounded source chunks.")

    st.subheader("Tool Trace")
    if result and result.get("tools_used"):
        for tool in result["tools_used"]:
            st.markdown(f"**{tool['name']}**")
            st.write(tool["summary"])
