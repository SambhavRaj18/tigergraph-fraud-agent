"""
Live End-to-End Investigation of HHG-006 using Real GeminiProvider & Real TigerGraph MCP Server.
"""

import sys
import json
import time
from src.agent.investigation_agent import FraudInvestigationAgent
from src.agent.tools import InvestigationTools
from src.agent.llm_provider import GeminiProvider


def main():
    print("=" * 90)
    print("  LIVE AGENTIC RUN: HHG-006 (GEMINI PROVIDER + REAL TIGERGRAPH MCP SERVER)")
    print("=" * 90)

    # 1. Initialize Real TigerGraph MCP Tools & Strict GeminiProvider
    tools = InvestigationTools(use_mcp=True)
    gemini = GeminiProvider(strict=True)

    print(f"\n[1] LLM Provider Initialized:")
    print(f"    - Provider Class : {gemini.__class__.__name__}")
    print(f"    - Model Name     : {gemini.model}")
    print(f"    - Strict Mode    : {gemini.strict} (Fallback Disabled)")
    print(f"    - MCP Enabled    : {tools.use_mcp} (Transport: stdio)")

    agent = FraudInvestigationAgent(tools=tools, llm_provider=gemini)

    # 2. Execute Investigation for HHG-006
    t0 = time.time()
    result = agent.investigate_case("HHG-006")
    total_time = round(time.time() - t0, 3)

    # 3. Report Results and Telemetry
    print("\n" + "=" * 90)
    print("  LIVE EXECUTION TELEMETRY & RESULTS")
    print("=" * 90)
    print(f"Real External Gemini API Calls Made: {gemini.real_api_calls}")
    print(f"Total Investigation Latency        : {total_time}s")
    print(f"Total Tools Executed (Audit Trail) : {len(result['_audit_trail'])}")

    print("\n--- TOOL CALL AUDIT TRAIL (LLM-Selected -> Executed via Real MCP) ---")
    for step in result["_audit_trail"]:
        print(f"Step {step['step']:2d} | Tool: {step['tool']:<26s} | Duration: {step['duration_s']:5.3f}s")
        print(f"        Args     : {step['args']}")
        print(f"        Rationale: {step['rationale']}")
        print(f"        Summary  : {step['summary']}")

    print("\n--- FINAL INVESTIGATION DELIVERABLE ---")
    print(f"Case ID           : {result['case_id']}")
    print(f"Status            : {result['case']['status']}")
    print(f"Verdict           : {result['case']['verdict']}")
    print(f"Pattern           : {result['case']['pattern']}")
    print(f"Fraud Probability : {result['case']['fraud_probability']}")
    print(f"First Suspicious  : {result['case']['first_suspicious_txn_id']}")
    print(f"Affected Txn IDs  : {result['case']['affected_txn_ids']}")
    print(f"Total Exposure    : ${result['case']['exposure_usd']:.2f}")
    print(f"SAR Filing        : {result['sar']['file']} (Total Amount: ${result['sar']['total_amount_usd']:.2f})")
    print(f"Written to Graph  : {result['case']['written_to_graph']}")
    print(f"Graph Case ID     : {result['case']['graph_case_id']}")
    print(f"Summary Narrative : {result['case']['summary']}")

    # 4. Strict Assertions for HHG-006
    assert gemini.real_api_calls >= 1, "Expected at least 1 real external Gemini API call"
    assert result["case"]["verdict"] == "fraud", f"Expected fraud, got {result['case']['verdict']}"
    assert result["case"]["pattern"] == "card_not_present_fraud", f"Expected card_not_present_fraud, got {result['case']['pattern']}"
    assert abs(result["case"]["exposure_usd"] - 1906.07) < 0.01, f"Expected 1906.07 exposure, got {result['case']['exposure_usd']}"
    assert result["sar"]["file"] is True, "Expected SAR filing to be True"
    assert result["case"]["written_to_graph"] is True, "Expected case to be written to TigerGraph memory"

    print("\n" + "=" * 90)
    print("  ALL HHG-006 STRICT GEMINI + MCP VERIFICATION CRITERIA SATISFIED!")
    print("=" * 90)


if __name__ == "__main__":
    main()
