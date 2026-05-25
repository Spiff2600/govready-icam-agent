"""
Cleared Identity Co-Pilot
A demonstration of Claude AI reasoning about cross-cloud identity exposure
for federal agencies using synthetic data.

⚠️ ALL DATA IS SYNTHETIC AND FICTIONAL
Customer: Orion Federal Analytics Agency (FICTIONAL)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
load_dotenv(APP_DIR / ".env")

from tools.claude_client import analyze_identity_exposure
from tools.eval_runner import load_eval_prompts, run_full_eval_suite
from tools.graph_builder import build_identity_graph, get_blast_radius, get_graph_data_for_plotly
from tools.identity_loader import get_service_accounts, get_users_with_weak_mfa, load_all_users
from tools.report_writer import build_technical_remediation_report, generate_executive_brief
from tools.risk_scoring import get_risk_summary, score_all_users

st.set_page_config(page_title="Cleared Identity Co-Pilot", layout="wide")

RISK_BADGES = {
    "CRITICAL": "🔴 CRITICAL",
    "HIGH": "🟠 HIGH",
    "MED": "🟡 MED",
    "LOW": "🟢 LOW",
}
RISK_COLORS = {"CRITICAL": "#c0392b", "HIGH": "#e67e22", "MED": "#f1c40f", "LOW": "#27ae60"}
MODEL_OPTIONS = ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-7"]

st.markdown(
    """
    <style>
    .stApp {background: #f7f9fc;}
    .risk-card {padding: 1rem; border-radius: 0.75rem; background: white; border: 1px solid #dfe6ee;}
    .approval-box {padding: 1rem; border-left: 4px solid #9b59b6; background: #f8f4fb; margin-bottom: 0.75rem;}
    .banner {padding: 0.9rem 1rem; background: #fff6d8; border: 1px solid #e0c25c; border-radius: 0.5rem;}
    .synthetic-banner {padding: 0.9rem 1rem; background: #ffe8e8; border: 1px solid #d9534f; border-radius: 0.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    users = load_all_users()
    scored = score_all_users(users)
    summary = get_risk_summary(scored)
    return users, scored, summary


def render_risk_badge(level: str) -> str:
    return RISK_BADGES.get(level, level)


def token_meter(token_usage: dict[str, Any]) -> None:
    cols = st.columns(3)
    cols[0].metric("Input tokens", token_usage.get("input", 0))
    cols[1].metric("Output tokens", token_usage.get("output", 0))
    cols[2].metric("Estimated cost", f"${token_usage.get('cost_usd', 0.0):.4f}")


def build_graph_figure(graph_data: dict[str, Any], selected_levels: list[str], highlight_cross_cloud: bool, scored_lookup: dict[str, dict[str, Any]]) -> go.Figure:
    nodes = [node for node in graph_data["nodes"] if node["node_type"] != "user" or node.get("risk_level") in selected_levels]
    allowed_ids = {node["id"] for node in nodes}
    edges = [edge for edge in graph_data["edges"] if edge["source"] in allowed_ids and edge["target"] in allowed_ids]

    edge_x = []
    edge_y = []
    for edge in edges:
        edge_x += [edge["source_x"], edge["target_x"], None]
        edge_y += [edge["source_y"], edge["target_y"], None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1, color="#95a5a6"),
        hoverinfo="none",
        showlegend=False,
    )

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    for node in nodes:
        score = node.get("risk_score", 10)
        user_summary = scored_lookup.get(node["id"], {})
        is_cross = "Administrative or sensitive access spans Azure Gov and AWS GovCloud." in user_summary.get("factors", [])
        color = "#2c3e50" if node["node_type"] != "user" else node["color"]
        if highlight_cross_cloud and node["node_type"] == "user" and is_cross:
            color = "#8e44ad"
        node_x.append(node["x"])
        node_y.append(node["y"])
        node_color.append(color)
        node_size.append(18 if node["node_type"] != "user" else max(20, 12 + score * 0.35))
        node_text.append(
            f"<b>{node['label']}</b><br>Type: {node['node_type']}<br>Risk: {node.get('risk_level', 'LOW')}<br>Score: {score}<br>{node.get('title', '')}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#34495e")),
        text=node_text,
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    )

    annotations = []
    for edge in edges[:120]:
        annotations.append(
            dict(
                x=(edge["source_x"] + edge["target_x"]) / 2,
                y=(edge["source_y"] + edge["target_y"]) / 2,
                text=edge["relation"],
                showarrow=False,
                font=dict(size=9, color="#7f8c8d"),
            )
        )

    return go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Cross-cloud identity exposure graph",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            annotations=annotations,
            height=700,
        ),
    )


def render_customer_overview(users: list[dict[str, Any]], scored: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    st.header("Orion Federal Analytics Agency")
    st.markdown('<div class="synthetic-banner"><strong>SYNTHETIC DEMO:</strong> All identities, mission details, and findings are fictional and created solely for demonstration.</div>', unsafe_allow_html=True)
    st.subheader("Mission")
    st.write("Interagency OSINT fusion cell supporting synthetic counter-narcotics task force.")

    footprint_df = pd.DataFrame([
        {"Cloud": "Azure Gov", "Tenant/Account": "orion-demo.onmicrosoft.us", "Assets": "3 subscriptions", "Users": 247},
        {"Cloud": "AWS GovCloud", "Tenant/Account": "123456789012", "Assets": "us-gov-west-1", "Users": 189},
        {"Cloud": "SaaS", "Tenant/Account": "M365 GCC High / Salesforce Gov / Zoom for Government", "Assets": "3 SaaS platforms", "Users": "N/A"},
    ])
    left, right = st.columns([1.2, 1])
    left.dataframe(footprint_df, use_container_width=True, hide_index=True)
    right.markdown(
        """
        **Observed pain points**
        - Standing privilege on tenant and account administrators
        - SMS-based MFA still present on sensitive accounts
        - No unified ownership for service identities
        - Azure and AWS review cycles are disconnected
        - Stale access after transfers and contract end
        - Credential sharing confirmed in audit evidence
        """
    )

    mfa_counts = pd.Series({"FIDO2": 4, "Authenticator App": 11, "SMS": 3, "Email OTP": 1, "None": 2})
    pie = go.Figure(data=[go.Pie(labels=mfa_counts.index, values=mfa_counts.values, hole=0.45)])
    pie.update_layout(title="Current MFA distribution", margin=dict(l=10, r=10, t=45, b=10), height=380)
    st.plotly_chart(pie, use_container_width=True)

    weak_mfa = len(get_users_with_weak_mfa())
    unowned_accounts = sum(1 for acct in get_service_accounts() if not acct.get("service_account_owner") or acct.get("service_account_owner") == "Departed Employee")
    metrics = st.columns(4)
    metrics[0].metric("Critical users", summary["critical_count"])
    metrics[1].metric("High-risk accounts", summary["high_count"])
    metrics[2].metric("Weak MFA", weak_mfa)
    metrics[3].metric("Unowned accounts", unowned_accounts)


def render_graph_tab(users: list[dict[str, Any]], scored: list[dict[str, Any]]) -> None:
    scored_lookup = {item["user_id"]: item for item in scored}
    graph = build_identity_graph(users)
    graph_data = get_graph_data_for_plotly(graph)

    with st.sidebar:
        st.subheader("Graph controls")
        selected_levels = st.multiselect("Risk levels", ["CRITICAL", "HIGH", "MED", "LOW"], default=["CRITICAL", "HIGH", "MED", "LOW"], key="graph_levels")
        highlight_cross_cloud = st.checkbox("Highlight cross-cloud admins", value=True)

    figure = build_graph_figure(graph_data, selected_levels, highlight_cross_cloud, scored_lookup)
    st.plotly_chart(figure, use_container_width=True)

    distribution = pd.DataFrame(scored).groupby("risk_level", as_index=False).size()
    bar = go.Figure(data=[go.Bar(x=distribution["risk_level"], y=distribution["size"], marker_color=[RISK_COLORS.get(level, "#95a5a6") for level in distribution["risk_level"]])])
    bar.update_layout(title="Risk distribution", height=320, xaxis_title="Risk level", yaxis_title="Accounts")
    st.plotly_chart(bar, use_container_width=True)

    table_rows = []
    for user in users:
        scored_user = scored_lookup[user["user_id"]]
        blast = get_blast_radius(graph, user["user_id"])
        table_rows.append({
            "User ID": user["user_id"],
            "Name": user["name"],
            "Risk": render_risk_badge(scored_user["risk_level"]),
            "Score": scored_user["composite_score"],
            "Primary MFA": user.get("primary_mfa_method"),
            "Azure Roles": ", ".join(role["role_name"] for role in user.get("azure_roles", [])),
            "AWS Permissions": ", ".join(role["permission_set"] for role in user.get("aws_permission_sets", [])),
            "Blast Radius": blast["reachable_count"],
        })
    st.dataframe(pd.DataFrame(table_rows).sort_values(by=["Score", "User ID"], ascending=[False, True]), use_container_width=True, hide_index=True)


def render_claude_analysis(users: list[dict[str, Any]], scored: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    st.subheader("Evidence-based Claude analysis")
    col1, col2 = st.columns([2.5, 1])
    with col1:
        question = st.text_area(
            "Question",
            value=st.session_state.get("analysis_question", "Identify the top identity risks and provide evidence-based recommendations"),
            height=100,
        )
    with col2:
        model = st.selectbox("Model", MODEL_OPTIONS, index=1, key="analysis_model")
        run = st.button("Run Analysis", use_container_width=True)

    if run:
        st.session_state["analysis_question"] = question
        with st.spinner("Running Claude analysis..."):
            st.session_state["analysis_result"] = analyze_identity_exposure(
                question,
                user_context={"risk_summary": summary, "top_users": scored[:5], "total_users": len(users)},
                model=model,
            )

    result = st.session_state.get("analysis_result")
    if not result:
        st.info("Run an analysis to view tool trace, narrative reasoning, and structured output.")
        return
    if result.get("from_cache"):
        st.markdown('<div class="banner"><strong>No API key - showing cached example output.</strong></div>', unsafe_allow_html=True)

    st.markdown("### Tool Call Trace")
    if result.get("tool_calls"):
        for index, call in enumerate(result["tool_calls"], start=1):
            with st.expander(f"{index}. {call['tool']} ({call['duration_ms']} ms)", expanded=False):
                st.code(json.dumps(call.get("args", {}), indent=2), language="json")
                st.json(call.get("result", {}))
    else:
        st.caption("No tool calls were captured in this run.")

    st.markdown("### Analysis")
    st.markdown(result.get("analysis", ""))

    st.markdown("### Structured Output")
    st.json(result.get("structured_output", {}))
    token_meter(result.get("token_usage", {}))

    actions = [action for action in result.get("structured_output", {}).get("recommended_actions", []) if action.get("approval_required", "none") != "none"]
    st.markdown("### Human Approval Gate")
    if not actions:
        st.success("No approval-gated actions proposed in this analysis.")
        return

    action_log = st.session_state.setdefault("action_log", [])
    for action in actions:
        st.markdown(f'<div class="approval-box"><strong>{action["action_id"]}</strong> — {action["description"]}<br>Targets: {", ".join(action.get("target_users", []))}<br>Approval required: {action.get("approval_required")}</div>', unsafe_allow_html=True)
        cols = st.columns([1, 1, 1])
        if cols[0].button("Approve", key=f"approve_{action['action_id']}"):
            action_log.append({"timestamp": datetime.now(timezone.utc).isoformat(), "action_id": action["action_id"], "decision": "approved", "targets": action.get("target_users", [])})
            st.success(f"Action {action['action_id']} approved and logged.")
        if cols[1].button("Reject", key=f"reject_{action['action_id']}"):
            action_log.append({"timestamp": datetime.now(timezone.utc).isoformat(), "action_id": action["action_id"], "decision": "rejected", "targets": action.get("target_users", [])})
            st.warning(f"Action {action['action_id']} rejected and logged.")
        if cols[2].button("Modify", key=f"modify_{action['action_id']}"):
            action_log.append({"timestamp": datetime.now(timezone.utc).isoformat(), "action_id": action["action_id"], "decision": "modify_requested", "targets": action.get("target_users", [])})
            st.info(f"Modification request captured for {action['action_id']}.")

    if action_log:
        st.markdown("#### Approval log")
        st.dataframe(pd.DataFrame(action_log), use_container_width=True, hide_index=True)


def render_executive_brief() -> None:
    model = st.selectbox("Executive brief model", MODEL_OPTIONS, index=1, key="brief_model")
    if st.button("Generate Executive Brief"):
        with st.spinner("Generating executive brief..."):
            st.session_state["executive_brief"] = generate_executive_brief(model=model)
    brief = st.session_state.get("executive_brief")
    if not brief:
        st.info("Generate an executive brief to see CIO/CISO-ready output.")
        return
    if brief.get("from_cache"):
        st.markdown('<div class="banner"><strong>No API key - executive prose includes cached/local content.</strong></div>', unsafe_allow_html=True)
    st.markdown("### CIO Summary")
    st.write(brief["cio_summary"])
    st.markdown("### Risk posture summary")
    st.dataframe(pd.DataFrame([brief["risk_posture"]]), use_container_width=True, hide_index=True)
    st.markdown("### 30 / 60 / 90 day plan")
    st.dataframe(pd.DataFrame(brief["plan"]), use_container_width=True, hide_index=True)
    st.markdown("### CISO findings")
    for finding in brief["ciso_findings"]:
        st.markdown(f"- {finding}")
    token_meter(brief.get("token_usage", {}))


def render_technical_remediation() -> None:
    report = build_technical_remediation_report(limit=10)
    st.markdown("### Top 10 highest-risk identities")
    for item in report["top_users"]:
        with st.container(border=True):
            st.markdown(f"**{item['name']} ({item['user_id']})** — {render_risk_badge(item['risk_level'])}")
            st.caption(f"Risk score: {item['risk_score']}")
            st.markdown("**Risk factors**")
            for factor in item["risk_factors"]:
                st.markdown(f"- {factor}")
            st.markdown("**Remediation steps**")
            for step in item["remediation_steps"]:
                st.markdown(f"- {step}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Azure-specific remediation")
        for rec in report["azure_recommendations"]:
            st.markdown(f"- {rec}")
    with col2:
        st.markdown("### AWS-specific remediation")
        for rec in report["aws_recommendations"]:
            st.markdown(f"- {rec}")
    st.download_button(
        "Download remediation report (JSON)",
        data=json.dumps(report, indent=2),
        file_name="cleared_identity_remediation_report.json",
        mime="application/json",
    )


def render_evals() -> None:
    prompts = load_eval_prompts()
    st.warning("Running evals makes real API calls and costs real money when an Anthropic API key is configured.")
    st.dataframe(pd.DataFrame(prompts), use_container_width=True, hide_index=True)
    model_choice = st.selectbox("Eval model", ["Run All Models"] + MODEL_OPTIONS, index=0, key="eval_model")
    if st.button("Run Evals"):
        models = MODEL_OPTIONS if model_choice == "Run All Models" else [model_choice]
        with st.spinner("Running eval suite..."):
            st.session_state["eval_results"] = run_full_eval_suite(models=models)
    results = st.session_state.get("eval_results")
    if not results:
        return
    st.markdown("### Model summary")
    st.dataframe(pd.DataFrame(results["summary"]), use_container_width=True, hide_index=True)
    rows = []
    for item in results["results"]:
        rows.append({
            "Model": item["model"],
            "ID": item["id"],
            "Prompt": item["prompt"],
            "PASS/FAIL": "PASS" if item["passed"] else "FAIL",
            "Latency (ms)": item["latency_ms"],
            "Cost ($)": item["cost_usd"],
            "Category": item["category"],
            "Difficulty": item["difficulty"],
        })
    st.markdown("### Per-prompt results")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def main() -> None:
    users, scored, summary = load_dataset()
    st.title("Cleared Identity Co-Pilot")
    st.caption("Synthetic Streamlit demo: deterministic tooling + Claude reasoning + approval gates for federal identity exposure.")
    tabs = st.tabs([
        "Customer Overview",
        "Identity Exposure Graph",
        "Claude Analysis",
        "Executive Brief",
        "Technical Remediation",
        "Evals",
    ])
    with tabs[0]:
        render_customer_overview(users, scored, summary)
    with tabs[1]:
        render_graph_tab(users, scored)
    with tabs[2]:
        render_claude_analysis(users, scored, summary)
    with tabs[3]:
        render_executive_brief()
    with tabs[4]:
        render_technical_remediation()
    with tabs[5]:
        render_evals()


if __name__ == "__main__":
    main()
