"""
Safe cleanup script for TigerGraph FraudInvestigation graph.
Deletes strictly the 10 identified synthetic header and test artifacts:
- Customer: customer_id, C99998, C99999
- Card: card_id
- Transaction: transaction_id
- DeviceProfile: device_id
- EmailDomain: domain, r_email_domain
- BillingRegion: region_id
- ClosedCase: case_id

Verifies live vertex and edge counts against prepared targets post-cleanup.
"""

import os
import time
import requests
import urllib3
from typing import List, Tuple, Dict
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env")
host = os.getenv("TG_HOST", "").rstrip("/")
secret = os.getenv("TG_SECRET", "").strip()
graph = os.getenv("TG_GRAPHNAME", "FraudInvestigation").strip()

# 10 Exact Artifacts to Delete
TARGET_DELETIONS: List[Tuple[str, str]] = [
    ("Customer", "customer_id"),
    ("Customer", "C99998"),
    ("Customer", "C99999"),
    ("Card", "card_id"),
    ("Transaction", "transaction_id"),
    ("DeviceProfile", "device_id"),
    ("EmailDomain", "domain"),
    ("EmailDomain", "r_email_domain"),
    ("BillingRegion", "region_id"),
    ("ClosedCase", "case_id"),
]

EXPECTED_VERTICES: Dict[str, int] = {
    "Customer": 13553,
    "Card": 1927,
    "Transaction": 590742,
    "DeviceProfile": 9705,
    "EmailDomain": 60,
    "BillingRegion": 332,
    "ClosedCase": 5565,
}

EXPECTED_EDGES: Dict[str, int] = {
    "OWNS": 1927,
    "OWNED_BY": 1927,
    "MADE": 14975,
    "TRANSACTION_OF": 14975,
    "FROM_DEVICE": 140784,
    "DEVICE_OF": 140784,
    "PURCHASER_EMAIL": 496262,
    "EMAIL_OF": 496262,
    "RECIPIENT_EMAIL": 137454,
    "RECIPIENT_OF": 137454,
    "BILLED_IN": 525003,
    "REGION_OF": 525003,
    "PERFORMED": 590742,
    "PERFORMED_BY": 590742,
    "NEXT": 577189,
    "INVOLVES": 14955,
    "ON_CARD": 5565,
    "CONNECTED_TO": 92,
}


def run_cleanup():
    print("=" * 80)
    print("STARTING CONTROLLED ARTIFACT CLEANUP ON TIGERGRAPH SAVANNA")
    print("=" * 80)

    # 1. Acquire Token
    token_url = f"{host}/gsql/v1/tokens"
    resp = requests.post(token_url, json={"secret": secret, "graph": graph, "lifetime": 1000000}, verify=False, timeout=15)
    jwt_token = resp.json().get("token")
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # 2. Verify Presence Before Deletion
    print("\n--- 1. Pre-Deletion Verification of Target Artifacts ---")
    verified_list = []
    for v_type, v_id in TARGET_DELETIONS:
        check_url = f"{host}/restpp/graph/{graph}/vertices/{v_type}/{v_id}"
        r = requests.get(check_url, headers=headers, verify=False, timeout=10)
        if r.status_code == 200 and r.json().get("results"):
            print(f"CONFIRMED TARGET: {v_type} ID='{v_id}' exists in graph.")
            verified_list.append((v_type, v_id))
        else:
            print(f"NOT FOUND (or already clean): {v_type} ID='{v_id}'")

    assert len(verified_list) == len(TARGET_DELETIONS), "Not all target artifacts were verified!"

    # 3. Execute Deletions
    print("\n--- 2. Executing Targeted Deletions ---")
    for v_type, v_id in verified_list:
        del_url = f"{host}/restpp/graph/{graph}/vertices/{v_type}/{v_id}"
        r_del = requests.delete(del_url, headers=headers, verify=False, timeout=15)
        print(f"DELETE {v_type}:{v_id} -> Status: {r_del.status_code}, Response: {r_del.text.strip()[:100]}")

    print("\nWaiting 5 seconds for GPE engine synchronization...")
    time.sleep(5)

    # 4. Query Final Live Counts
    print("\n" + "=" * 80)
    print("FINAL POST-CLEANUP VERIFICATION")
    print("=" * 80)

    # Vertices
    v_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_vertex_number", "type": "*"}, verify=False)
    v_dict = {item["v_type"]: item["count"] for item in v_resp.json().get("results", [])}

    # Edges
    e_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_edge_number", "type": "*"}, verify=False)
    e_dict = {item["e_type"]: item["count"] for item in e_resp.json().get("results", [])}

    print("\n--- Vertex Counts Verification ---")
    print(f"{'Vertex Type':<25} | {'Live Count in Graph':<20} | {'Expected Target':<16} | {'Status':<10}")
    print("-" * 77)
    v_all_match = True
    for v_name, exp_cnt in EXPECTED_VERTICES.items():
        actual_cnt = v_dict.get(v_name, 0)
        status = "PASSED" if actual_cnt == exp_cnt else "MISMATCH"
        if status == "MISMATCH":
            v_all_match = False
        print(f"{v_name:<25} | {actual_cnt:<20,} | {exp_cnt:<16,} | {status:<10}")

    print("\n--- Edge Counts Verification ---")
    print(f"{'Edge Type':<25} | {'Live Count in Graph':<20} | {'Expected Target':<16} | {'Status':<10}")
    print("-" * 77)
    e_all_match = True
    for e_name, exp_cnt in EXPECTED_EDGES.items():
        actual_cnt = e_dict.get(e_name, 0)
        status = "PASSED" if actual_cnt == exp_cnt else "MISMATCH"
        if status == "MISMATCH":
            e_all_match = False
        print(f"{e_name:<25} | {actual_cnt:<20,} | {exp_cnt:<16,} | {status:<10}")

    print("\n" + "=" * 80)
    if v_all_match and e_all_match:
        print("ALL VERTICES, PRIMARY EDGES, AND REVERSE EDGES MATCH 100% WITH ZERO DISCREPANCIES!")
    else:
        print(f"VERIFICATION COMPLETED WITH STATUS: Vertices Match={v_all_match}, Edges Match={e_all_match}")
    print("=" * 80)


if __name__ == "__main__":
    run_cleanup()

