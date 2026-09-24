"""
TigerGraph Agentic Fraud Investigation Analyst Dashboard.
Hacker House Goa - Benchmark Investigation & Case Review UI.
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
    page_title="TigerGraph Fraud Agent | Analyst Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for an enterprise fintech analyst dashboard
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .badge-fraud {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #FCA5A5;
        display: inline-block;
    }
    .badge-not-fraud {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #86EFAC;
        display: inline-block;
    }
    .badge-uncertain {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #FCD34D;
        display: inline-block;
    }
    .badge-route-l1 {
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #BFDBFE;
    }
    .badge-route-l2 {
        background-color: #FAF5FF;
        color: #6B21A8;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #E9D5FF;
    }
    .badge-route-auto {
        background-color: #F0FDF4;
        color: #15803D;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #BBF7D0;
    }
    .step-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    .provenance-box {
        background-color: #F8FAFC;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.88rem;
    }
    .sar-narrative-box {
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 16px;
        font-family: monospace;
        font-size: 0.92rem;
        line-height: 1.5;
        color: #0F172A;
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
        return '<span class="badge-fraud">⚠️ FRAUD</span>'
    elif verdict_lower == "not_fraud":
        return '<span class="badge-not-fraud">✅ NOT FRAUD</span>'
    else:
        return '<span class="badge-uncertain">⏳ UNCERTAIN / REVIEW</span>'

def get_route_badge(route: str) -> str:
    route_upper = (route or "").upper()
    if route_upper == "L1":
        return '<span class="badge-route-l1">Route: L1 Analyst</span>'
    elif route_upper == "L2":
        return '<span class="badge-route-l2">Route: L2 Compliance</span>'
    else:
        return '<span class="badge-route-auto">Route: Auto-Execution</span>'

# Sidebar
st.sidebar.image("https://raw.githubusercontent.com/tigergraph/ecosystem/master/tigergraph-logo.png", width=220) if False else None
st.sidebar.markdown("## 🛡️ Fraud Investigation Agent")
st.sidebar.caption("TigerGraph Savanna Cloud × Autonomous Agentic Core")

case_pack_df = load_case_pack()
all_case_ids = [f"HHG-{i:03d}" for i in range(1, 21)]

# Prominent case selector with HHG-006 featured
default_index = 5  # HHG-006 is index 5 in 0-indexed list
selected_case_id = st.sidebar.selectbox(
    "Select Benchmark Case",
    options=all_case_ids,
    index=default_index,
    format_func=lambda cid: f"⭐ {cid} (Demo Showcase)" if cid == "HHG-006" else f"📁 {cid}"
)

# Sidebar TigerGraph connection info
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 TigerGraph Savanna Cloud")
tg_host = os.getenv("TG_HOST", "https://tg-8e011c11-160d-4156-8ccf-a8b4f0b4116c.tg-3452941248.i.tgcloud.io")
st.sidebar.caption(f"**Host:** `{tg_host.split('//')[-1].split('.')[0]}...`")
st.sidebar.caption("**Graph:** `FraudInvestigation`")
st.sidebar.caption("**Case Memory:** `5,585 records` (5,565 historical + 20 benchmark)")
st.sidebar.link_button("🔗 Open TigerGraph GraphStudio", f"{tg_host}/#/")

# Load selected case data
case_data = load_case_json(selected_case_id)
trigger_row = case_pack_df[case_pack_df["case_id"] == selected_case_id] if not case_pack_df.empty else None
trigger_dict = trigger_row.iloc[0].to_dict() if (trigger_row is not None and len(trigger_row) > 0) else {}

# Main Header
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.markdown(f'<div class="main-header">Case Investigation: {selected_case_id}</div>', unsafe_allow_html=True)
    trigger_desc = trigger_dict.get('trigger_text', 'Automated anomaly detection alert.')
    st.markdown(f'<div class="sub-header">Trigger: <b>{trigger_dict.get("trigger_type", "Alert")}</b> — <i>"{trigger_desc}"</i></div>', unsafe_allow_html=True)

with col_header_2:
    verdict = case_data.get("case", {}).get("verdict", "uncertain")
    st.markdown(f'<div style="text-align: right; padding-top: 10px;">{get_verdict_badge(verdict)}</div>', unsafe_allow_html=True)

# Top Metrics Row
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    prob = case_data.get("case", {}).get("fraud_probability", 0.0)
    st.metric(label="Fraud Probability", value=f"{prob:.0%}")
with c2:
    exposure = case_data.get("case", {}).get("exposure_usd", 0.0)
    st.metric(label="Total Exposure", value=format_currency(exposure))
with c3:
    sar_filing = case_data.get("sar", {}).get("file", False)
    st.metric(label="SAR Filing Required", value="YES (FinCEN)" if sar_filing else "NO")
with c4:
    txns = case_data.get("case", {}).get("affected_txn_ids", [])
    st.metric(label="Affected Txns", value=f"{len(txns)} transaction(s)")
with c5:
    latency = case_data.get("latency_s", 0.0)
    calls = case_data.get("tool_calls", 0)
    st.metric(label="Agent Performance", value=f"{latency:.2f}s", help=f"Total MCP/Graph tool calls: {calls}")

st.markdown("---")

# Navigation Tabs
tab_progression, tab_evidence, tab_actions_sar, tab_graph, tab_raw = st.tabs([
    "🔄 Investigation Progression",
    "📊 Graph Evidence & Provenance",
    "⚡ Policy Actions & SAR Narrative",
    "🌐 TigerGraph Context & Subgraph",
    "📄 Benchmark Deliverable (JSON)"
])

# ==========================================
# TAB 1: INVESTIGATION PROGRESSION
# ==========================================
with tab_progression:
    st.subheader("Agentic Investigation Lifecycle")
    st.markdown("""
    The Autonomous Fraud Investigation Agent executes a closed-loop investigation process constrained by deterministic policy guardrails:
    """)
    
    col_p1, col_p2 = st.columns([1, 1])
    
    with col_p1:
        st.markdown("""
        <div class="step-box">
            <b>1. Trigger Ingestion & Alert Context</b><br>
            <span style="color: #64748B;">
            Flagged Txn: <code>{}</code> | Customer: <code>{}</code> | Card: <code>{}</code><br>
            Risk Score: <code>{}</code>
            </span>
        </div>
        <div class="step-box">
            <b>2. Multi-Hop TigerGraph Traversal</b><br>
            <span style="color: #64748B;">
            Traversed card, customer, device, and temporal <code>NEXT</code> transaction sequences.
            GSQL Query: <code>investigate_transaction(target_txn={})</code>
            </span>
        </div>
        <div class="step-box">
            <b>3. Graph Evidence Synthesis & Baseline Analysis</b><br>
            <span style="color: #64748B;">
            Computed spending Z-score, device sharing fingerprint across graph, and billing region frequency.
            </span>
        </div>
        <div class="step-box">
            <b>4. Historical Case Memory Precedent Lookup</b><br>
            <span style="color: #64748B;">
            Queried 5,565 historical closed cases on TigerGraph to find matching modus operandi.
            Precedents: <code>{}</code>
            </span>
        </div>
        """.format(
            trigger_dict.get("flagged_txn_id", "N/A"),
            trigger_dict.get("customer_id", "N/A"),
            trigger_dict.get("card_id", "N/A"),
            trigger_dict.get("risk_score", "N/A"),
            trigger_dict.get("flagged_txn_id", "N/A"),
            ", ".join(case_data.get("case", {}).get("similar_prior_cases", ["None"]))
        ), unsafe_allow_html=True)

    with col_p2:
        st.markdown("""
        <div class="step-box">
            <b>5. Deterministic Policy Engine (R1–R10)</b><br>
            <span style="color: #64748B;">
            Evaluated policy rules for transaction decline, card blocking, case creation, SAR filing, and connected card monitoring.
            </span>
        </div>
        <div class="step-box">
            <b>6. Termination & Stop Decision</b><br>
            <span style="color: #64748B;">
            Stop Reason: <code>{}</code> | Total Tool Iterations: <code>{}</code>
            </span>
        </div>
        <div class="step-box">
            <b>7. Persistent Graph Case Memory Write</b><br>
            <span style="color: #64748B;">
            Investigation record persisted to TigerGraph vertex <code>Case('{}')</code>.<br>
            Written Status: <b>{}</b>
            </span>
        </div>
        """.format(
            case_data.get("stop_reason", "sufficient_evidence"),
            case_data.get("tool_calls", 6),
            selected_case_id,
            "✅ SUCCESS" if case_data.get("case", {}).get("written_to_graph", True) else "FAILED"
        ), unsafe_allow_html=True)

    st.markdown("### Executive Investigation Summary")
    st.info(case_data.get("case", {}).get("summary", "No summary available."))

# ==========================================
# TAB 2: GRAPH EVIDENCE & PROVENANCE
# ==========================================
with tab_evidence:
    st.subheader("Graph Evidence & Baseline Decomposition")
    
    col_e1, col_e2 = st.columns([1, 1])
    
    with col_e1:
        st.markdown("#### 🎯 Flagged & Affected Transactions")
        txns_list = case_data.get("case", {}).get("affected_txn_ids", [])
        if txns_list:
            df_txns = pd.DataFrame({
                "Transaction ID": txns_list,
                "Status": ["Flagged / Target" if tid == case_data.get("case", {}).get("first_suspicious_txn_id") else "Episode Txn" for tid in txns_list],
                "Confidence": f"{prob:.0%}"
            })
            st.dataframe(df_txns, use_container_width=True, hide_index=True)
        else:
            st.warning("No transactions confirmed fraudulent (Uncertain / Insufficient evidence).")
        
        st.markdown("#### 📱 Connected Devices & Shared Rings")
        devices = case_data.get("case", {}).get("connected_device_profiles", [])
        if devices:
            for dev in devices:
                st.code(dev, language="text")
        else:
            st.caption("No physical device record linked (Card-Present POS / In-Store).")

        st.markdown("#### 💳 Connected Cards")
        cards = case_data.get("case", {}).get("connected_card_ids", [])
        st.write(cards)

    with col_e2:
        st.markdown("#### 🔍 Strict Evidence Provenance (Observed vs Inferred vs Simulated)")
        evidence_items = case_data.get("case", {}).get("evidence", [])
        if evidence_items:
            for ev in evidence_items:
                source_label = ev.get("source", "graph").upper()
                claim_text = ev.get("claim", "")
                ref_text = ev.get("ref", "")
                st.markdown(f"""
                <div class="provenance-box" style="border-left: 3px solid #10B981;">
                    <b>🏷️ [{source_label}]</b> {claim_text}<br>
                    <small style="color: #64748B;">Reference: <code>{ref_text}</code></small>
                </div>
                """, unsafe_allow_html=True)
        
        # Evidence Requests / Simulated Claims
        sim_requests = case_data.get("evidence_requests", [])
        if sim_requests:
            st.markdown("#### 💬 Customer Validation / External Inquiries")
            for req in sim_requests:
                req_type = req.get("type", "customer_validation")
                assumed = req.get("assumed_response", "")
                is_simulated = "SIMULATED" in assumed.upper() or "ASSUMED" in assumed.upper()
                badge = "⚠️ SIMULATED / ASSUMED" if is_simulated else "✅ OBSERVED"
                color = "#F59E0B" if is_simulated else "#10B981"
                st.markdown(f"""
                <div class="provenance-box" style="border-left: 3px solid {color};">
                    <b>{badge}</b> (Type: <code>{req_type}</code>)<br>
                    <i>"{assumed}"</i>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# TAB 3: POLICY ACTIONS & SAR NARRATIVE
# ==========================================
with tab_actions_sar:
    st.subheader("Deterministic Policy Execution (Rules R1–R10)")
    
    actions_initial = case_data.get("next_best_actions", {}).get("initial", [])
    actions_final = case_data.get("next_best_actions", {}).get("final", [])
    
    st.markdown("#### Recommended Actions & Approval Routing")
    if actions_final:
        for act in actions_final:
            act_name = act.get("action", "")
            route = act.get("route", "auto")
            reason = act.get("reason", "")
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; font-size: 1.0rem; color: #1E293B;">⚡ {act_name}</span>
                    {get_route_badge(route)}
                </div>
                <div style="color: #475569; font-size: 0.9rem;">{reason}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No policy actions triggered.")

    st.markdown("---")
    st.subheader("Suspicious Activity Report (FinCEN SAR)")
    sar_data = case_data.get("sar", {})
    
    if sar_data.get("file", False):
        st.markdown(f"""
        <div class="sar-narrative-box">
            <b>REGULATORY SAR FILING (FinCEN Form 111 Narrative)</b><br>
            <b>Filing Reason:</b> {sar_data.get('reason', 'Regulatory Threshold')}<br>
            <b>Subject(s):</b> {', '.join(sar_data.get('subjects', []))}<br>
            <b>Reportable Exposure:</b> {format_currency(sar_data.get('total_amount_usd', 0.0))}<br>
            <b>Activity Date Range:</b> {sar_data.get('activity_dates', ['N/A', 'N/A'])[0]} to {sar_data.get('activity_dates', ['N/A', 'N/A'])[1]}<br><br>
            <b>Narrative:</b><br>
            {sar_data.get('narrative', 'No narrative generated.')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 6px; padding: 16px; color: #64748B;">
            <b>No FinCEN SAR Filing Required</b><br>
            Exposure is below regulatory threshold ($1,000.00) or investigation resulted in non-fraud / inconclusive evidence.
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 4: TIGERGRAPH CONTEXT & SUBGRAPH
# ==========================================
with tab_graph:
    st.subheader("TigerGraph Cloud Schema & GraphStudio Context")
    
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        st.markdown("#### 🗺️ Graph Schema Architecture")
        st.markdown("""
        - **`Transaction`**: Flagged and lifetime transaction vertices (`amount`, `timestamp`, `channel`, `is_fraud`).
        - **`Card`**: Card vertex connecting transactions via `PERFORMED_WITH`.
        - **`Customer`**: Account holder identity connecting cards via `OWNS_CARD`.
        - **`Device`**: Browser/OS/Hardware fingerprint connecting transactions via `TRANSACTED_FROM`.
        - **`BillingRegion`**: Geographic billing region vertex connecting transactions via `BILLED_IN`.
        - **`Case`**: Graph case memory storing persistent investigation verdicts, patterns, exposure, and SAR status via `ASSOCIATED_WITH`.
        - **`NEXT` (Edge)**: Temporal sequential edge linking subsequent transactions on the same card.
        """)
        
    with col_g2:
        st.markdown("#### ⚡ GSQL Queries Deployed")
        st.markdown("""
        - **`investigate_transaction(target_txn)`**:
          - Traverses 1-hop and 2-hop neighborhoods.
          - Aggregates customer spending baseline (count, mean, stddev, z-score).
          - Analyzes device sharing across all cards in the 590,742 transaction graph.
          - Follows temporal `NEXT` chains to identify multi-transaction fraud bursts.
        - **`find_similar_cases(pattern, min_exposure, max_exposure)`**:
          - Graph similarity lookup against 5,565 historical closed cases.
        - **`write_investigation_case(...)`**:
          - Upserts active investigation results to graph memory.
        """)
    
    st.markdown("#### 💻 TigerGraph Savanna Cloud Endpoints")
    st.code(f"""
TigerGraph Host: {tg_host}
Active Graph: FraudInvestigation
REST++ API Port: 9000
GSQL Port: 14240
GraphStudio UI: {tg_host}/#/
    """, language="text")

# ==========================================
# TAB 5: RAW BENCHMARK DELIVERABLE
# ==========================================
with tab_raw:
    st.subheader(f"Raw Benchmark JSON Deliverable ({selected_case_id}.json)")
    st.caption("Exact schema deliverable submitted for Hacker House Goa benchmark evaluation.")
    st.json(case_data)
