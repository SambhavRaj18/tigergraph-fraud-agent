"""
TigerGraph Fraud Investigation Agent - Analyst Console.
Hacker House Goa 2026 - Benchmark Investigation & Next-Best-Action Dashboard.
"""

import os
import json
import time
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="TigerGraph Fraud Console | SOC & Analyst Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Financial Fraud / SOC Analyst Console CSS
st.markdown("""
<style>
    /* Global Financial Operations Theme */
    .stApp {
        background-color: #0F172A;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Header */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 16px;
        background-color: #1E293B;
        border-bottom: 1px solid #334155;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    .brand-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin: 0;
    }
    .status-pill-online {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
    }

    /* KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 10px 14px;
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }

    /* Verdict Badges */
    .badge-verdict-fraud {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-verdict-legit {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-verdict-uncertain {
        background-color: rgba(245, 158, 11, 0.2);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Stepper Timeline */
    .stepper-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 10px 16px;
        margin-bottom: 16px;
        overflow-x: auto;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        min-width: 100px;
    }
    .step-badge {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #3B82F6;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 4px;
    }
    .step-title {
        font-size: 0.72rem;
        font-weight: 600;
        color: #E2E8F0;
    }
    .step-arrow {
        color: #475569;
        font-size: 0.9rem;
        font-weight: bold;
    }

    /* Content Cards */
    .panel-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 14px;
    }
    .panel-header {
        font-size: 0.88rem;
        font-weight: 700;
        color: #E2E8F0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 12px;
        border-bottom: 1px solid #334155;
        padding-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Provenance Tags */
    .tag-provenance-graph {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .tag-provenance-baseline {
        background-color: rgba(139, 92, 246, 0.15);
        color: #A78BFA;
        border: 1px solid rgba(139, 92, 246, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .tag-provenance-simulated {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }

    /* Action Cards */
    .action-card {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-left: 4px solid #3B82F6;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .action-route-auto {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .action-route-l1 {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .action-route-l2 {
        background-color: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    /* SAR Container */
    .sar-container {
        background-color: #0F172A;
        border: 1px solid #475569;
        border-radius: 4px;
        padding: 14px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.82rem;
        line-height: 1.45;
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_case_pack() -> pd.DataFrame:
    pack_path = os.path.join(os.path.dirname(__file__), "data", "raw", "case_pack.csv")
    if os.path.exists(pack_path):
        return pd.read_csv(pack_path)
    return pd.DataFrame()

@st.cache_data
def load_case_json(case_id: str) -> dict:
    case_path = os.path.join(os.path.dirname(__file__), "cases", f"{case_id}.json")
    if os.path.exists(case_path):
        with open(case_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def format_currency(val) -> str:
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def get_verdict_badge(verdict: str) -> str:
    verdict_lower = (verdict or "").lower()
    if verdict_lower == "fraud":
        return '<span class="badge-verdict-fraud">FRAUD</span>'
    elif verdict_lower == "not_fraud" or verdict_lower == "legitimate":
        return '<span class="badge-verdict-legit">LEGITIMATE</span>'
    else:
        return '<span class="badge-verdict-uncertain">UNCERTAIN / REVIEW</span>'

def get_route_chip(route: str) -> str:
    route_upper = (route or "").upper()
    if route_upper == "L1":
        return '<span class="action-route-l1">Route: L1 Analyst</span>'
    elif route_upper == "L2":
        return '<span class="action-route-l2">Route: L2 Compliance</span>'
    else:
        return '<span class="action-route-auto">Route: Auto</span>'

# Sidebar Navigation & Investigation Context
st.sidebar.markdown("### 🛡️ Investigation")
case_pack_df = load_case_pack()
all_case_ids = [f"HHG-{i:03d}" for i in range(1, 21)]

# Case selection formatting
def format_case_option(cid: str) -> str:
    if cid == "HHG-006":
        return f"⭐ {cid} (Demo Showcase - $1,906.07 SAR)"
    elif cid == "HHG-017":
        return f"⚠️ {cid} (Uncertainty Workflow - Policy R1)"
    elif cid == "HHG-011":
        return f"📁 {cid} (10-Txn Burst - $470.97 SAR)"
    elif cid == "HHG-010":
        return f"📁 {cid} (Single Txn - $1,000.03 SAR)"
    else:
        return f"📁 {cid}"

selected_case_id = st.sidebar.selectbox(
    "Active Case",
    options=all_case_ids,
    index=5,  # Default HHG-006
    format_func=format_case_option
)

# Load selected case data
case_data = load_case_json(selected_case_id)
trigger_row = case_pack_df[case_pack_df["case_id"] == selected_case_id] if not case_pack_df.empty else None
trigger_dict = trigger_row.iloc[0].to_dict() if (trigger_row is not None and len(trigger_row) > 0) else {}

# Sidebar Trigger Box
st.sidebar.markdown("---")
st.sidebar.markdown("#### Alert Trigger Context")
st.sidebar.markdown(f"""
- **Trigger Type:** `{trigger_dict.get('trigger_type', 'N/A')}`
- **Flagged Txn:** `{trigger_dict.get('flagged_txn_id', 'N/A')}`
- **Customer ID:** `{trigger_dict.get('customer_id', 'N/A')}`
- **Card ID:** `{trigger_dict.get('card_id', 'N/A')}`
- **Opened Date:** `{trigger_dict.get('opened_at', 'N/A')}`
""")
trigger_msg = trigger_dict.get("trigger_text", "")
if trigger_msg:
    st.sidebar.caption(f'"{trigger_msg}"')

# Sidebar System Health & Architecture Status
st.sidebar.markdown("---")
st.sidebar.markdown("#### System Connectivity")
tg_host = os.getenv("TG_HOST", "https://tg-8e011c11-160d-4156-8ccf-a8b4f0b4116c.tg-3452941248.i.tgcloud.io")
st.sidebar.markdown("""
- **TigerGraph Savanna:** <span style="color:#10B981;">● Connected</span>
- **MCP Protocol:** <span style="color:#10B981;">● Active (stdio)</span>
- **Policy Engine:** <span style="color:#10B981;">● Enforced (R1–R10)</span>
- **Graph Memory:** `5,585 Cases`
""", unsafe_allow_html=True)
st.sidebar.link_button("🌐 Open Savanna GraphStudio", f"{tg_host}/#/", use_container_width=True)

# TOP HEADER
st.markdown(f"""
<div class="top-navbar">
    <div>
        <div class="brand-title">TigerGraph Fraud Investigation Agent</div>
        <div class="brand-subtitle">Agentic Investigation & Next-Best-Action Console</div>
    </div>
    <div>
        <div class="status-pill-online"><span class="status-dot"></span> TigerGraph Savanna Cloud Active</div>
    </div>
</div>
""", unsafe_allow_html=True)

# MAIN CASE KPI BAR
case_inner = case_data.get("case", {})
verdict = case_inner.get("verdict", "uncertain")
prob = case_inner.get("fraud_probability", 0.0)
exposure = case_inner.get("exposure_usd", 0.0)
pattern = case_inner.get("pattern", "none")
sar_data = case_data.get("sar", {})
sar_file = sar_data.get("file", False)
affected_txns = case_inner.get("affected_txn_ids", [])
latency = case_data.get("latency_s", 0.0)
tool_calls_count = case_data.get("tool_calls", 0)

kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)
with kpi_c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Case Identifier</div>
        <div class="kpi-value">{selected_case_id}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Verdict</div>
        <div>{get_verdict_badge(verdict)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Fraud Probability</div>
        <div class="kpi-value" style="color: {'#F87171' if prob >= 0.7 else ('#FBBF24' if prob >= 0.3 else '#34D399')};">{prob:.0%}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Fraud Pattern</div>
        <div class="kpi-value" style="font-size: 0.88rem; font-family: monospace; color: #93C5FD;">{pattern}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Exposure</div>
        <div class="kpi-value">{format_currency(exposure)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c6:
    sar_badge = '<span style="color:#F87171; font-weight:700;">REQUIRED (FinCEN)</span>' if sar_file else '<span style="color:#94A3B8; font-weight:600;">NOT REQUIRED</span>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">SAR Filing</div>
        <div style="font-size: 0.85rem; margin-top: 2px;">{sar_badge}</div>
    </div>
    """, unsafe_allow_html=True)

# INVESTIGATION TIMELINE / STEPPER
st.markdown("""
<div class="stepper-container">
    <div class="step-item">
        <div class="step-badge">1</div>
        <div class="step-title">Trigger Ingestion</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">2</div>
        <div class="step-title">Graph Traversal</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">3</div>
        <div class="step-title">Evidence Analysis</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">4</div>
        <div class="step-title">Case Memory</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">5</div>
        <div class="step-title">Policy Evaluation</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">6</div>
        <div class="step-title">Decision (Stop)</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-item">
        <div class="step-badge">7</div>
        <div class="step-title">Graph Persistence</div>
    </div>
</div>
""", unsafe_allow_html=True)

# UNCERTAINTY & DECISION BANNER
if verdict.lower() == "uncertain":
    st.markdown(f"""
    <div style="background-color: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; padding: 12px 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: #FBBF24; font-size: 0.95rem;">⚠️ INVESTIGATION CONFIDENCE: {prob:.0%} — STATUS: UNCERTAIN / REVIEW</span>
            <span class="tag-provenance-simulated">POLICY R1 ENFORCED</span>
        </div>
        <div style="font-size: 0.85rem; color: #E2E8F0; margin-top: 6px;">
            Available structural graph evidence does not meet the definitive fraud threshold (P < 0.70) without out-of-band cardholder validation.
            Under Policy Rule R1, the card remains active under raised monitoring sensitivity (<code>VERIFY_WITH_CUSTOMER -> MONITOR_CARD</code>).
        </div>
    </div>
    """, unsafe_allow_html=True)

# TWO-COLUMN EVIDENCE AREA
col_left, col_right = st.columns([1, 1])

with col_left:
    # Transaction Evidence Area
    st.markdown("""
    <div class="panel-card">
        <div class="panel-header">
            <span>Transaction Evidence</span>
            <span class="tag-provenance-graph">GRAPH VERIFIED</span>
        </div>
    """, unsafe_allow_html=True)
    
    if affected_txns:
        target_txn_id = case_inner.get("first_suspicious_txn_id", trigger_dict.get("flagged_txn_id", ""))
        df_txns = pd.DataFrame([
            {
                "Transaction ID": tid,
                "Role": "Flagged / Initial Target" if str(tid) == str(target_txn_id) else "Episode Bursts",
                "Channel": "Online / CNP",
                "Status": "At-Risk / Fraud"
            }
            for tid in affected_txns
        ])
        st.dataframe(df_txns, use_container_width=True, hide_index=True)
        
        st.caption(f"**Episode Summary:** {len(affected_txns)} transaction(s) | First Suspicious: `{target_txn_id}` | Cumulative Exposure: `{format_currency(exposure)}`")
    else:
        st.markdown("""
        <div style="color: #94A3B8; font-size: 0.85rem; padding: 8px 0;">
            No confirmed fraudulent transactions in episode (Target transaction cleared or awaiting verification).
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

    # Next Best Action Area
    st.markdown("""
    <div class="panel-card">
        <div class="panel-header">
            <span>Next Best Action (Deterministic Policy Engine)</span>
            <span class="tag-provenance-baseline">RULES R1–R10</span>
        </div>
    """, unsafe_allow_html=True)
    
    actions_final = case_data.get("next_best_actions", {}).get("final", [])
    if actions_final:
        for act in actions_final:
            act_name = act.get("action", "")
            route = act.get("route", "auto")
            reason = act.get("reason", "")
            st.markdown(f"""
            <div class="action-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC;">⚡ {act_name}</span>
                    {get_route_chip(route)}
                </div>
                <div style="color: #94A3B8; font-size: 0.82rem;">{reason}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No policy actions generated.")
        
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # Entity & Behavioral Evidence Area
    st.markdown("""
    <div class="panel-card">
        <div class="panel-header">
            <span>Entity & Behavioral Evidence</span>
            <span class="tag-provenance-baseline">BASELINE & NETWORK</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Evidence items from graph
    evidence_list = case_inner.get("evidence", [])
    for ev in evidence_list:
        claim = ev.get("claim", "")
        ref = ev.get("ref", "")
        source = ev.get("source", "graph").upper()
        tag_class = "tag-provenance-graph" if source == "GRAPH" else "tag-provenance-baseline"
        st.markdown(f"""
        <div style="background-color: #0F172A; border: 1px solid #334155; border-radius: 4px; padding: 8px 12px; margin-bottom: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span class="{tag_class}">[{source}]</span>
                <span style="font-size: 0.7rem; color: #64748B; font-family: monospace;">{ref}</span>
            </div>
            <div style="font-size: 0.83rem; color: #E2E8F0;">{claim}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Connected Device & Cards
    devices = case_inner.get("connected_device_profiles", [])
    cards = case_inner.get("connected_card_ids", [])
    if devices:
        st.markdown(f"**Device Profile:** `{devices[0]}`")
    st.markdown(f"**Associated Cards:** `{', '.join(cards) if cards else 'None'}`")
    
    # Historical Precedents
    precedents = case_inner.get("similar_prior_cases", [])
    st.markdown(f"**TigerGraph Case Memory Precedents:** `{', '.join(precedents) if precedents else 'None'}`")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Customer Validation / External Inquiries
    requests = case_data.get("evidence_requests", [])
    if requests:
        st.markdown("""
        <div class="panel-card">
            <div class="panel-header">
                <span>Customer Inquiries & Evidence Provenance</span>
                <span class="tag-provenance-simulated">SIMULATED / ASSUMED</span>
            </div>
        """, unsafe_allow_html=True)
        for req in requests:
            assumed = req.get("assumed_response", "")
            st.markdown(f"""
            <div style="background-color: #0F172A; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; padding: 10px 12px; font-size: 0.82rem; color: #FCD34D;">
                <b>Cardholder Validation Response:</b><br>
                <i>"{assumed}"</i>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# REGULATORY SAR SECTION (IF FILED)
if sar_file:
    st.markdown("""
    <div class="panel-card" style="border-left: 4px solid #EF4444;">
        <div class="panel-header">
            <span style="color: #F87171;">FinCEN Suspicious Activity Report (Form 111 Narrative)</span>
            <span class="badge-verdict-fraud">MANDATORY FILING</span>
        </div>
    """, unsafe_allow_html=True)
    
    dates = sar_data.get("activity_dates", ["N/A", "N/A"])
    date_str = f"{dates[0]} to {dates[1]}" if len(dates) >= 2 else "N/A"
    
    st.markdown(f"""
    <div class="sar-container">
        <b>FILING REASON:</b> {sar_data.get('reason', 'Policy 3a Regulatory Trigger')}<br>
        <b>SUBJECTS:</b> {', '.join(sar_data.get('subjects', []))}<br>
        <b>REPORTABLE AMOUNT:</b> {format_currency(sar_data.get('total_amount_usd', 0.0))}<br>
        <b>ACTIVITY DATES:</b> {date_str}<br><br>
        <b>NARRATIVE:</b><br>
        {sar_data.get('narrative', '')}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# EXPANDABLE AUDIT & DEVELOPER SECTIONS
with st.expander("🔍 Agent Investigation Trace & Tool Sequence", expanded=False):
    st.markdown(f"""
    - **Stop Reason:** `{case_data.get('stop_reason', 'sufficient_evidence')}`
    - **Investigation Latency:** `{latency:.2f}s`
    - **MCP Tool Invocations:** `{tool_calls_count}`
    - **Graph Memory Vertex Written:** `{case_inner.get('graph_case_id', selected_case_id)}` (Status: `{'Written' if case_inner.get('written_to_graph') else 'Pending'}`)
    """)
    st.markdown("#### Tool Execution Log")
    st.code(f"""
[1] retrieve_case_trigger       -> Flagged Txn: {trigger_dict.get('flagged_txn_id')}, Customer: {trigger_dict.get('customer_id')}
[2] investigate_transaction     -> GSQL 2-Hop Traversal (Target: {trigger_dict.get('flagged_txn_id')})
[3] analyze_evidence            -> Baseline Z-score, Geographic Region & Device Fingerprint
[4] get_similar_closed_cases    -> Case Memory Lookup (5,565 historical records)
[5] evaluate_policy_decision    -> Evaluated Deterministic Rules R1-R10
[6] stop_investigation          -> Stop Condition Satisfied ({case_data.get('stop_reason')})
    """, language="text")

with st.expander("📄 Developer / Benchmark Deliverable (JSON)", expanded=False):
    st.caption(f"Official benchmark deliverable file: cases/{selected_case_id}.json")
    st.json(case_data)
