"""
Edge discrepancy investigation script.
Queries edges connected to the header vertices and test vertices.
"""

import os
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env")
host = os.getenv("TG_HOST").rstrip("/")
secret = os.getenv("TG_SECRET")
graph = os.getenv("TG_GRAPHNAME", "FraudInvestigation")

r = requests.post(f"{host}/gsql/v1/tokens", json={"secret": secret, "graph": graph, "lifetime": 1000000}, verify=False)
jwt_token = r.json().get("token")
headers = {"Authorization": f"Bearer {jwt_token}"}

print("=" * 80)
print("INVESTIGATING EXTRA EDGES CONNECTED TO HEADER/TEST VERTICES")
print("=" * 80)

# Check edges for known extra vertices
test_vertices = [
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

for v_type, v_id in test_vertices:
    url = f"{host}/restpp/graph/{graph}/vertices/{v_type}/{v_id}"
    resp = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"\n--- Vertex {v_type} ID: '{v_id}' ---")
    if resp.status_code == 200:
        data = resp.json().get("results", [])
        if data:
            print("Vertex Attributes:", data[0].get("attributes"))
        else:
            print("Vertex data empty.")
    else:
        print(f"Status: {resp.status_code}")

    # Check outgoing edges
    url_edges = f"{host}/restpp/graph/{graph}/edges/{v_type}/{v_id}"
    resp_e = requests.get(url_edges, headers=headers, verify=False, timeout=10)
    if resp_e.status_code == 200:
        edges = resp_e.json().get("results", [])
        print(f"Connected Edges ({len(edges)}):")
        for edge in edges:
            print(f"  -> Edge: {edge.get('e_type')} to {edge.get('to_type')}:{edge.get('to_id')}")
    else:
        print(f"Edge query status: {resp_e.status_code}")

