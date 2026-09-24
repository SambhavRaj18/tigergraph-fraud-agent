"""
Test script for TigerGraph MCP Server & Client over stdio transport.
Tests:
1. MCP Protocol connection and handshake.
2. tools/list returning exposed TigerGraph tools.
3. tools/call investigate_transaction on transaction 3476682 (HHG-006).
4. tools/call analyze_evidence.
5. tools/call get_policy_rule.
"""

import sys
import json
import time
from src.mcp.client import TigerGraphMCPClient


def main():
    print("=======================================================")
    print("  TESTING REAL TIGERGRAPH MCP SERVER & CLIENT (STDIO)")
    print("=======================================================")

    client = TigerGraphMCPClient()

    # Step 1: List MCP Tools
    print("\n[Step 1] Connecting to MCP Server and calling tools/list...")
    t0 = time.time()
    tools = client.list_tools()
    print(f"-> Handshake complete in {round(time.time() - t0, 3)}s.")
    print(f"-> Exposed Tools Count: {len(tools)}")
    for t in tools:
        print(f"   * Tool: {t['name']}")
        print(f"     Description: {t['description']}")

    assert len(tools) >= 4, "Expected at least 4 MCP tools"

    # Step 2: Call investigate_transaction
    txn_id = "3476682"
    print(f"\n[Step 2] Executing MCP tools/call 'investigate_transaction' for txn={txn_id}...")
    t0 = time.time()
    graph_res = client.investigate_transaction(txn_id)
    print(f"-> MCP call returned in {round(time.time() - t0, 3)}s.")
    print("DEBUG type(graph_res):", type(graph_res))
    if isinstance(graph_res, str):
        graph_res = json.loads(graph_res)
        print("DEBUG after json.loads type:", type(graph_res))
    
    print("DEBUG keys:", list(graph_res.keys()) if isinstance(graph_res, dict) else "Not a dict")
    target_val = graph_res.get("target_txn")
    if isinstance(target_val, list) and len(target_val) > 0:
        target_id = target_val[0].get("v_id") if isinstance(target_val[0], dict) else str(target_val[0])
    elif isinstance(target_val, str):
        target_id = target_val
    else:
        target_id = str(target_val)
        
    cust_val = graph_res.get("customer")
    if isinstance(cust_val, list) and len(cust_val) > 0:
        customer = cust_val[0].get("v_id") if isinstance(cust_val[0], dict) else str(cust_val[0])
    elif isinstance(cust_val, str):
        customer = cust_val
    else:
        customer = str(cust_val)
    
    print(f"   Target Txn: {target_id}")
    print(f"   Customer: {customer}")
    print(f"   Historical Txns Count: {len(graph_res.get('customer_transactions', []))}")
    print(f"   Connected Closed Cases: {len(graph_res.get('related_closed_cases', []))}")

    assert str(target_id) == str(txn_id), f"Expected target txn {txn_id}, got {target_id}"

    # Step 3: Call analyze_evidence
    print(f"\n[Step 3] Executing MCP tools/call 'analyze_evidence' for txn={txn_id}...")
    t0 = time.time()
    evidence_res = client.analyze_evidence(txn_id)
    print(f"-> MCP call returned in {round(time.time() - t0, 3)}s.")
    print(f"   Total Txns: {evidence_res.get('customer_baseline_statistics', {}).get('total_transactions')}")
    print(f"   Billing Region: {evidence_res.get('geographic_analysis', {}).get('target_billing_region')}")
    print(f"   Detected Bursts: {evidence_res.get('burst_analysis', {}).get('burst_detected')}")

    # Step 4: Call get_policy_rule
    print("\n[Step 4] Executing MCP tools/call 'get_policy_rule' for rule_id='R5'...")
    t0 = time.time()
    rule_res = client.get_policy_rule("R5")
    print(f"-> MCP call returned in {round(time.time() - t0, 3)}s.")
    print(f"   Rule: {rule_res.get('rule_id')} -> {rule_res.get('description')}")

    print("\n=======================================================")
    print("  ALL MCP PROTOCOL TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================")


if __name__ == "__main__":
    main()
