"""
Test script for PolicyDecisionEngine on Benchmark Case HHG-001.
"""

import json
from src.graph_client import TigerGraphClient
from src.analysis.evidence_analyzer import FraudEvidenceAnalyzer
from src.policy.decision_engine import PolicyDecisionEngine


def run_test():
    client = TigerGraphClient()
    
    # HHG-001 Case Parameters
    case_id = "HHG-001"
    trigger_type = "risk_score"
    trigger_text = "Real-time model scored transaction 3514030 ($77.07, in billing region 444.0) at 0.61. Review and decide."
    flagged_txn_id = "3514030"

    print(f"=== 1. Fetching Graph Data for {case_id} (txn={flagged_txn_id}) ===")
    raw_graph_data = client.run_investigation_query(flagged_txn_id)

    print("=== 2. Running FraudEvidenceAnalyzer ===")
    analyzer = FraudEvidenceAnalyzer(raw_graph_data)
    evidence = analyzer.analyze()

    print("=== 3. Running PolicyDecisionEngine ===")
    engine = PolicyDecisionEngine(
        case_id=case_id,
        trigger_type=trigger_type,
        trigger_text=trigger_text,
        evidence=evidence
    )
    decision = engine.evaluate_decision()

    print("\n" + "=" * 80)
    print("COMPLETE STRUCTURED CASE DECISION (HHG-001)")
    print("=" * 80)
    print(json.dumps(decision, indent=2))

    print("\n" + "=" * 80)
    print("DECISION SUMMARY & COMPLIANCE CHECK")
    print("=" * 80)
    print(f"Case ID           : {decision['case_id']}")
    print(f"Status            : {decision['case']['status']}")
    print(f"Verdict           : {decision['case']['verdict']}")
    print(f"Fraud Probability : {decision['case']['fraud_probability']}")
    print(f"Pattern           : {decision['case']['pattern']}")
    print(f"Exposure USD      : ${decision['case']['exposure_usd']}")
    print(f"Initial Actions   : {decision['next_best_actions']['initial']}")
    print(f"Final Actions     : {decision['next_best_actions']['final']}")
    print(f"What Changed      : {decision['next_best_actions']['what_changed']}")
    print(f"SAR File Required : {decision['sar']['file']}")
    print(f"Stop Reason       : {decision['stop_reason']}")


if __name__ == "__main__":
    run_test()
