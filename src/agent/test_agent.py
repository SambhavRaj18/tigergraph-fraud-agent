"""
Execution and verification script for FraudInvestigationAgent on Benchmark Case HHG-001.
"""

import os
import json
from src.agent.investigation_agent import FraudInvestigationAgent


def run_agent_test():
    agent = FraudInvestigationAgent()
    
    case_id = "HHG-001"
    print("=" * 80)
    print(f"RUNNING AGENTIC FRAUD INVESTIGATION: {case_id}")
    print("=" * 80)

    result = agent.investigate_case(case_id)

    # Separate audit trail for clean reporting
    audit_trail = result.pop("_audit_trail", [])

    print("\n" + "=" * 80)
    print("EXECUTION AUDIT TRAIL (TOOL INVOCATIONS)")
    print("=" * 80)
    for entry in audit_trail:
        print(f"Step {entry['step']:<2} | Tool: {entry['tool']:<32} | Latency: {entry['duration_s']:<6}s | Details: {entry['summary']}")

    print("\n" + "=" * 80)
    print("OFFICIAL BENCHMARK DELIVERABLE JSON (HHG-001)")
    print("=" * 80)
    print(json.dumps(result, indent=2))

    # Verification checklist
    print("\n" + "=" * 80)
    print("BENCHMARK FORMAT & POLICY COMPLIANCE CHECK")
    print("=" * 80)
    assert result["case_id"] == "HHG-001", "case_id mismatch"
    assert "case" in result, "missing 'case'"
    assert "status" in result["case"], "missing 'case.status'"
    assert "verdict" in result["case"], "missing 'case.verdict'"
    assert "fraud_probability" in result["case"], "missing 'case.fraud_probability'"
    assert "evidence" in result["case"], "missing 'case.evidence'"
    assert "evidence_requests" in result, "missing 'evidence_requests'"
    assert "next_best_actions" in result, "missing 'next_best_actions'"
    assert "initial" in result["next_best_actions"], "missing 'initial' actions"
    assert "final" in result["next_best_actions"], "missing 'final' actions"
    assert "sar" in result, "missing 'sar'"
    assert "stop_reason" in result, "missing 'stop_reason'"
    assert "tool_calls" in result, "missing 'tool_calls'"
    assert "latency_s" in result, "missing 'latency_s'"
    print("All required top-level and nested benchmark fields verified 100%!")


if __name__ == "__main__":
    run_agent_test()
