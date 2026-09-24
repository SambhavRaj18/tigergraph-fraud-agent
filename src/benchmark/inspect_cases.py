"""
Deep case inspection script for all 20 benchmark cases.
Queries TigerGraph and prints detailed graph evidence for each case.
"""

import os
import json
import pandas as pd
from src.graph_client import TigerGraphClient
from src.analysis.evidence_analyzer import FraudEvidenceAnalyzer

CASE_PACK_PATH = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/case_pack.csv")

def inspect_all():
    client = TigerGraphClient()
    df = pd.read_csv(CASE_PACK_PATH)
    
    for idx, row in df.iterrows():
        cid = row["case_id"]
        tid = str(int(row["flagged_txn_id"]))
        ttype = row["trigger_type"]
        ttext = row["trigger_text"]
        
        raw = client.run_investigation_query(tid)
        analyzer = FraudEvidenceAnalyzer(raw)
        evidence = analyzer.analyze()
        
        obs = evidence["observed_evidence"]
        t_sum = obs["transaction"]
        base = evidence["customer_baseline_statistics"]
        geo = evidence["geographic_analysis"]
        dev = evidence["device_and_identity_analysis"]
        temp = evidence["temporal_sequencing"]
        
        print("=" * 80)
        print(f"CASE: {cid} | Trigger: {ttype} | Flagged Txn: {tid}")
        print(f"Text: {ttext}")
        print(f"Txn details: amt=${t_sum.get('amount')}, chan={t_sum.get('channel')}, reg={t_sum.get('addr1')}, risk={t_sum.get('risk_score')}")
        print(f"Customer txns count: {base.get('total_transactions')}, mean amt: ${base.get('amount_distribution', {}).get('mean')}")
        print(f"Device: {dev.get('device_id')}, is_new={dev.get('is_new')}, shared_custs={dev.get('shared_customer_count')}")
        print(f"Temporal: prior_1h={temp.get('prior_1_hour_transactions_count')}, prior_24h={temp.get('prior_24_hour_transactions_count')}")
        print(f"Next txns: {len(raw.get('next_transactions', []))}")
        print(f"Related closed cases: {len(raw.get('related_closed_cases', []))}")

if __name__ == "__main__":
    inspect_all()

