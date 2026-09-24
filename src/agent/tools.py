"""
Tools and environment interfaces for Fraud Investigation Agent.
Integrates TigerGraph GSQL queries, historical case retrieval, evidence analysis, and policy evaluation.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from src.graph_client import TigerGraphClient
from src.analysis.evidence_analyzer import FraudEvidenceAnalyzer
from src.policy.decision_engine import PolicyDecisionEngine

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_PACK_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "case_pack.csv")
CLOSED_CASES_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "closed_cases_history.csv")

POLICY_RULES_DOCS = {
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

TOOL_DEFINITIONS = [
    {
        "name": "retrieve_case_trigger",
        "description": "Retrieve alert metadata, customer ID, card ID, and flagged transaction ID from case pack.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "The case ID to look up (e.g. 'HHG-001')"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "investigate_transaction",
        "description": "Execute multi-hop graph traversal in TigerGraph around a transaction ID to extract customer history, device profile, cards, and closed case links.",
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "The transaction ID to investigate"}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "analyze_evidence",
        "description": "Perform baseline statistical, geographic, temporal burst clustering, and fraud pattern feature extraction on raw graph data.",
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "Transaction ID corresponding to the graph data"}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "get_similar_closed_cases",
        "description": "Retrieve detailed resolution outcomes, analyst narratives, and loss figures for historical closed cases.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_ids": {"type": "array", "items": {"type": "string"}, "description": "List of closed case IDs"}
            },
            "required": ["case_ids"]
        }
    },
    {
        "name": "get_policy_rule",
        "description": "Retrieve formal documentation and conditions for an operational policy rule (R1-R10).",
        "parameters": {
            "type": "object",
            "properties": {
                "rule_id": {"type": "string", "description": "Policy rule identifier (e.g. 'R1', 'R5', 'R9', 'R10')"}
            },
            "required": ["rule_id"]
        }
    },
    {
        "name": "request_customer_validation",
        "description": "Queue an out-of-band customer verification request without fabricating simulated answers.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Verification question or intent to verify"},
                "channel": {"type": "string", "description": "Channel: SMS, EMAIL, PUSH, PHONE"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "request_analyst_information",
        "description": "Queue a request for specialized L1/L2 human analyst review.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Specific question or area for analyst inspection"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "evaluate_policy_decision",
        "description": "Evaluate deterministic policy rules R1-R10 against structured evidence to produce final actions, exposure, and SAR determinations.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID being evaluated"},
                "trigger_type": {"type": "string", "description": "Trigger type"}
            },
            "required": ["case_id"]
        }
    }
]


class InvestigationTools:
    def __init__(self, client: Optional[TigerGraphClient] = None, use_mcp: bool = False):
        self.client = client or TigerGraphClient()
        self.use_mcp = use_mcp or os.environ.get("USE_MCP", "false").lower() in ["true", "1", "yes"]
        self.mcp_client = None
        if self.use_mcp:
            from src.mcp.client import TigerGraphMCPClient
            self.mcp_client = TigerGraphMCPClient()
        self.df_cases = pd.read_csv(CASE_PACK_PATH) if os.path.exists(CASE_PACK_PATH) else pd.DataFrame()
        self.df_closed = pd.read_csv(CLOSED_CASES_PATH) if os.path.exists(CLOSED_CASES_PATH) else pd.DataFrame()
        self._last_raw_graph_data: Dict[str, Any] = {}

    def retrieve_case_trigger(self, case_id: str) -> Dict[str, Any]:
        """Tool 1: Retrieve case metadata and trigger from case_pack.csv."""
        matches = self.df_cases[self.df_cases["case_id"] == case_id]
        if matches.empty:
            raise ValueError(f"Case ID '{case_id}' not found in case_pack.csv")
        row = matches.iloc[0].to_dict()
        return {
            "case_id": str(row.get("case_id")),
            "opened_at": str(row.get("opened_at")),
            "trigger_type": str(row.get("trigger_type")),
            "trigger_text": str(row.get("trigger_text")),
            "flagged_txn_id": str(int(row["flagged_txn_id"])) if pd.notna(row.get("flagged_txn_id")) else "",
            "card_id": str(row.get("card_id")) if pd.notna(row.get("card_id")) else "",
            "customer_id": str(row.get("customer_id")) if pd.notna(row.get("customer_id")) else "",
            "risk_score": float(row["risk_score"]) if pd.notna(row.get("risk_score")) else None,
        }

    def investigate_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Tool 2: Execute multi-hop investigate_transaction query on TigerGraph Savanna via MCP or REST++."""
        if self.use_mcp and self.mcp_client:
            data = self.mcp_client.investigate_transaction(str(transaction_id))
        else:
            data = self.client.run_investigation_query(str(transaction_id))
        self._last_raw_graph_data = data
        return data

    def analyze_evidence(self, raw_graph_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Tool 3: Run statistical baseline, geographic, and pattern alignment analysis."""
        graph_data = raw_graph_data or self._last_raw_graph_data
        if not graph_data:
            raise ValueError("No raw graph data available to analyze. Run investigate_transaction first.")
        analyzer = FraudEvidenceAnalyzer(graph_data)
        return analyzer.analyze()

    def get_similar_closed_cases(self, case_ids: List[str]) -> List[Dict[str, Any]]:
        """Tool 4: Retrieve full narratives and outcomes for related closed cases."""
        if not case_ids:
            return []
        matches = self.df_closed[self.df_closed["case_id"].isin(case_ids)]
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

    def retrieve_historical_case_details(self, case_ids: List[str]) -> List[Dict[str, Any]]:
        """Alias for backwards compatibility."""
        return self.get_similar_closed_cases(case_ids)

    def get_policy_rule(self, rule_id: str) -> Dict[str, str]:
        """Tool 5: Retrieve policy rule description."""
        clean_id = rule_id.upper().strip()
        desc = POLICY_RULES_DOCS.get(clean_id, f"Rule '{clean_id}' not found in official policy book.")
        return {"rule_id": clean_id, "description": desc}

    def request_customer_validation(self, question: str, channel: str = "SMS") -> Dict[str, Any]:
        """Tool 6: Queue customer validation request without fabricating answer."""
        return {
            "request_type": "customer_validation",
            "channel": channel,
            "question": question,
            "status": "QUEUED_OUT_OF_BAND",
            "response": None
        }

    def request_analyst_information(self, question: str) -> Dict[str, Any]:
        """Tool 7: Queue human analyst request."""
        return {
            "request_type": "analyst_review",
            "question": question,
            "status": "QUEUED_FOR_TRIAGE",
            "response": None
        }

    def evaluate_policy_decision(
        self,
        case_id: str,
        trigger_type: str,
        trigger_text: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tool 8: Apply deterministic PolicyDecisionEngine adhering to rules R1–R10."""
        engine = PolicyDecisionEngine(
            case_id=case_id,
            trigger_type=trigger_type,
            trigger_text=trigger_text,
            evidence=evidence
        )
        return engine.evaluate_decision()

    def write_case_to_graph_memory(
        self,
        case_id: str,
        case_decision: Dict[str, Any],
        case_meta: Dict[str, Any]
    ) -> bool:
        """Tool 9: Store the concluded investigation case and edges into TigerGraph memory."""
        case_data = case_decision.get("case", {})
        customer_id = case_meta.get("customer_id", "")
        card_id = case_meta.get("card_id", "")
        opened_at = case_meta.get("opened_at", "2016-12-01 00:00:00")
        closed_at = opened_at  # Immediate resolution timestamp
        status = case_data.get("status", "closed_legitimate")
        outcome = "confirmed_fraud" if case_data.get("verdict") == "fraud" else "cleared"
        pattern = case_data.get("pattern", "none")
        first_fraud_txn = case_data.get("first_suspicious_txn_id", "")
        affected_txns = case_data.get("affected_txn_ids", [])
        n_txns = len(affected_txns)
        exposure_usd = case_data.get("exposure_usd", 0.0)
        
        final_actions = case_decision.get("next_best_actions", {}).get("final", [])
        actions_str = ",".join([a["action"] for a in final_actions])
        report_filed = case_decision.get("sar", {}).get("file", False)
        notes = case_data.get("summary", "")
        connected_cards = case_data.get("connected_card_ids", [])

        return self.client.write_case_to_graph(
            case_id=case_id,
            customer_id=customer_id,
            card_id=card_id,
            opened_at=opened_at,
            closed_at=closed_at,
            status=status,
            outcome=outcome,
            pattern=pattern,
            first_fraud_txn_id=first_fraud_txn,
            n_txns=n_txns,
            exposure_usd=exposure_usd,
            actions_taken=actions_str,
            report_filed=report_filed,
            analyst_notes=notes,
            affected_txn_ids=affected_txns,
            connected_card_ids=connected_cards
        )
