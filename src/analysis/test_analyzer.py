"""
Test script for FraudEvidenceAnalyzer on Benchmark Case HHG-001.
"""

import os
import json
from src.graph_client import TigerGraphClient
from src.analysis.evidence_analyzer import FraudEvidenceAnalyzer

def run_test():
    client = TigerGraphClient()
    
    # HHG-001 flagged transaction
    txn_id = "3514030"
    print(f"Fetching graph evidence for transaction: {txn_id} ...")
    raw_graph_data = client.run_investigation_query(txn_id)
    
    print("Running FraudEvidenceAnalyzer...")
    analyzer = FraudEvidenceAnalyzer(raw_graph_data)
    evidence = analyzer.analyze()
    
    print("\n" + "=" * 80)
    print("FRAUD EVIDENCE ANALYSIS OUTPUT (HHG-001)")
    print("=" * 80)
    print(json.dumps(evidence, indent=2))
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY FOR AGENT")
    print("=" * 80)
    print(f"1. Transaction: Amount=${evidence['transaction_summary']['amount']}, Channel={evidence['transaction_summary']['channel']}, RiskScore={evidence['transaction_summary']['risk_score']}")
    print(f"2. Customer: {evidence['customer_profile']['customer_id']} with {evidence['customer_baseline_statistics']['total_transactions']} historical transactions")
    print(f"3. Billing Region: Target Region {evidence['geographic_analysis']['target_billing_region']} (Historical count: {evidence['geographic_analysis']['target_region_historical_count']}, Unseen: {evidence['geographic_analysis']['is_unseen_region_for_customer']})")
    print(f"4. Temporal Next: Jumped to Region {evidence['geographic_analysis']['next_transaction_region']} in {evidence['temporal_sequencing']['next_transaction']['time_diff_hours']} hours (Cross-region transition: {evidence['geographic_analysis']['is_immediate_cross_region_transition']})")
    print(f"5. Historical Cases: {evidence['historical_cases_context']['total_related_closed_cases']} related closed cases ({evidence['historical_cases_context']['related_case_ids']})")
    print(f"6. Pattern Alignment Signals: {json.dumps(evidence['pattern_alignment_signals'], indent=2)}")
    print(f"7. Unavailable Signals: {evidence['unavailable_signals']}")

if __name__ == "__main__":
    run_test()
