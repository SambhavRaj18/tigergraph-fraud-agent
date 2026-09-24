"""
TigerGraph Model Context Protocol (MCP) Server.
Implements standard JSON-RPC 2.0 MCP protocol over stdio using the official MCP Python SDK.
Exposes TigerGraph fraud investigation tools to AI agents.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import pandas as pd
from typing import Dict, Any, List, Optional
from mcp.server.mcpserver import MCPServer
from src.graph_client import TigerGraphClient
from src.analysis.evidence_analyzer import FraudEvidenceAnalyzer

# Initialize server
mcp_server = MCPServer("tigergraph-fraud-mcp")

# Initialize graph client & data sources
_tg_client = TigerGraphClient()
_CASE_PACK_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "case_pack.csv")
_CLOSED_CASES_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "closed_cases_history.csv")

_df_cases = pd.read_csv(_CASE_PACK_PATH) if os.path.exists(_CASE_PACK_PATH) else pd.DataFrame()
_df_closed = pd.read_csv(_CLOSED_CASES_PATH) if os.path.exists(_CLOSED_CASES_PATH) else pd.DataFrame()

_POLICY_RULES_DOCS = {
    "R1": "Transaction amount <= $5.00: ALLOW_TRANSACTION / CLOSE_NO_FRAUD unless card_testing sequence detected.",
    "R2": "Customer risk score >= 0.85: ESCALATE_TO_ANALYST and STEP_UP_AUTH if pattern matches ATO or CNP.",
    "R3": "Customer confirms fraud: BLOCK_CARD, CANCEL_SUBSCRIPTION, FILE_SAR if exposure >= $2000.",
    "R4": "Out of region transaction (> 500 miles / novel region) with high risk score: STEP_UP_AUTH / VERIFY_WITH_CUSTOMER.",
    "R5": "Card testing sequence (multiple sub-$5 auths within short time frame): BLOCK_CARD, DECLINE_TRANSACTION, CREATE_CASE.",
    "R6": "Card not present on new device with no prior customer link: STEP_UP_AUTH, MONITOR_CARD.",
    "R7": "Account takeover (email change + rapid high-dollar spend or new device): BLOCK_CARD, STEP_UP_AUTH, ESCALATE_TO_ANALYST.",
    "R8": "Multi-transaction burst on compromised card: aggregate exposure across episode, BLOCK_CARD.",
    "R9": "FinCEN SAR filing requirement: mandatory if total confirmed exposure >= $2,000.00.",
    "R10": "Approval routing thresholds: exposure < $1,000 auto-executable; $1,000 <= exposure < $10,000 requires L1 analyst approval; exposure >= $10,000 requires L2 compliance approval."
}


@mcp_server.tool()
def investigate_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Execute multi-hop graph traversal in TigerGraph Savanna Cloud around a transaction ID.
    Retrieves customer profile, historical transactions, connected cards, devices, and closed cases.
    """
    return _tg_client.run_investigation_query(str(transaction_id))


@mcp_server.tool()
def analyze_evidence(transaction_id: str) -> Dict[str, Any]:
    """
    Perform statistical baseline, geographic distance, device sharing, and fraud pattern feature extraction.
    """
    graph_data = _tg_client.run_investigation_query(str(transaction_id))
    analyzer = FraudEvidenceAnalyzer(graph_data)
    return analyzer.analyze()


@mcp_server.tool()
def get_similar_closed_cases(case_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Retrieve resolution outcomes, analyst narratives, and historical losses from TigerGraph closed case memory.
    """
    if not case_ids:
        return []
    matches = _df_closed[_df_closed["case_id"].isin(case_ids)]
    results = []
    for _, row in matches.iterrows():
        results.append({
            "case_id": str(row.get("case_id")),
            "opened_at": str(row.get("opened_at")),
            "closed_at": str(row.get("closed_at")),
            "outcome": str(row.get("outcome")),
            "pattern": str(row.get("pattern")),
            "exposure_usd": float(row.get("exposure_usd", 0.0)) if pd.notna(row.get("exposure_usd")) else 0.0,
            "actions_taken": str(row.get("actions_taken", "")),
            "report_filed": str(row.get("report_filed", "")),
            "analyst_notes": str(row.get("analyst_notes", "")),
        })
    return results


@mcp_server.tool()
def get_policy_rule(rule_id: str) -> Dict[str, str]:
    """
    Retrieve documented logic and conditions for an operational policy rule (R1-R10).
    """
    clean_id = rule_id.upper().strip()
    desc = _POLICY_RULES_DOCS.get(clean_id, f"Rule '{clean_id}' not found in official policy book.")
    return {"rule_id": clean_id, "description": desc}


def run_stdio():
    """Run the MCP server using standard IO transport."""
    mcp_server.run()


if __name__ == "__main__":
    run_stdio()
