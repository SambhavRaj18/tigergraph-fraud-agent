"""
Investigation script to identify exact extra vertex IDs and edge records in TigerGraph.
Queries vertices and edges from RESTPP endpoints and sets difference against data_prepared.
"""

import os
import requests
import urllib3
import pandas as pd
from typing import Set, Dict, Any
from dotenv import load_dotenv

urllib3.disable_warnings()

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env")
host = os.getenv("TG_HOST").rstrip("/")
secret = os.getenv("TG_SECRET")
graph = os.getenv("TG_GRAPHNAME", "FraudInvestigation")
prep_dir = "d:/HHHGOA/tigergraph-fraud-agent/graph/loading/data_prepared"

r = requests.post(f"{host}/gsql/v1/tokens", json={"secret": secret, "graph": graph, "lifetime": 1000000}, verify=False)
jwt_token = r.json().get("token")
headers = {"Authorization": f"Bearer {jwt_token}"}

print("=" * 80)
print("INVESTIGATING GRAPH DATA DISCREPANCIES (Live Graph vs Prepared CSVs)")
print("=" * 80)

def get_all_vertex_ids(v_type: str, limit: int = 1000000) -> Set[str]:
    """Retrieve all vertex IDs of a given type from RESTPP."""
    url = f"{host}/restpp/graph/{graph}/vertices/{v_type}?limit={limit}"
    resp = requests.get(url, headers=headers, verify=False, timeout=60)
    if resp.status_code != 200:
        print(f"Error fetching vertices for {v_type}: {resp.status_code} - {resp.text[:200]}")
        return set()
    data = resp.json()
    return {str(v.get("v_id")) for v in data.get("results", [])}

# 1. Compare Vertex IDs
vertex_configs = [
    ("Customer", "vertices_customer.csv", "customer_id"),
    ("Card", "vertices_card.csv", "card_id"),
    ("EmailDomain", "vertices_email_domain.csv", "domain"),
    ("BillingRegion", "vertices_billing_region.csv", "region_id"),
    ("DeviceProfile", "vertices_device_profile.csv", "device_id"),
    ("ClosedCase", "vertices_closed_case.csv", "case_id"),
]

for v_type, csv_file, id_col in vertex_configs:
    df_prep = pd.read_csv(os.path.join(prep_dir, csv_file), dtype=str)
    prep_ids = set(df_prep[id_col].dropna().astype(str))
    
    live_ids = get_all_vertex_ids(v_type)
    
    extra_in_graph = live_ids - prep_ids
    missing_in_graph = prep_ids - live_ids
    
    print(f"\n--- Vertex: {v_type} ---")
    print(f"Prepared CSV IDs count : {len(prep_ids):,}")
    print(f"Live Graph IDs count   : {len(live_ids):,}")
    print(f"Extra IDs in Graph     : {len(extra_in_graph)} -> {extra_in_graph if len(extra_in_graph) <= 10 else list(extra_in_graph)[:10]}")
    print(f"Missing IDs in Graph   : {len(missing_in_graph)} -> {missing_in_graph if len(missing_in_graph) <= 10 else list(missing_in_graph)[:10]}")

# 2. Compare Transaction Vertices in batches if needed
print("\n--- Vertex: Transaction ---")
df_tx_prep = pd.read_csv(os.path.join(prep_dir, "vertices_transaction.csv"), usecols=["transaction_id"], dtype=str)
prep_tx_ids = set(df_tx_prep["transaction_id"].dropna().astype(str))
live_tx_ids = get_all_vertex_ids("Transaction", limit=1000000)
extra_tx = live_tx_ids - prep_tx_ids
missing_tx = prep_tx_ids - live_tx_ids
print(f"Prepared Transaction IDs count: {len(prep_tx_ids):,}")
print(f"Live Transaction IDs count    : {len(live_tx_ids):,}")
print(f"Extra Transaction IDs in Graph: {len(extra_tx)} -> {extra_tx}")
print(f"Missing Transaction IDs       : {len(missing_tx)}")

