"""
Installer and test execution script for investigate_transaction query on benchmark case HHG-001.
"""

import os
import sys
import json
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env", override=True)
host = os.getenv("TG_HOST", "").rstrip("/")
secret = os.getenv("TG_SECRET", "").strip()
graph = os.getenv("TG_GRAPHNAME", "FraudInvestigation").strip()

print(f"Connecting to {host} on graph {graph}...")

# 1. Acquire Token
token_url = f"{host}/gsql/v1/tokens"
resp = requests.post(token_url, json={"secret": secret, "graph": graph, "lifetime": 1000000}, verify=False, timeout=15)
if resp.status_code != 200:
    print(f"Token acquisition failed: {resp.status_code} - {resp.text}")
    sys.exit(1)

jwt_token = resp.json().get("token")
print("Acquired fresh JWT token.")

headers_gsql = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "text/plain"}
headers_rest = {"Authorization": f"Bearer {jwt_token}"}

# 2. Deploy & Install Query
query_path = "d:/HHHGOA/tigergraph-fraud-agent/graph/queries/investigate_transaction.gsql"
with open(query_path, "r", encoding="utf-8") as f:
    query_gsql = f.read()

print("\n--- Compiling and Installing investigate_transaction query ---")
res_install = requests.post(f"{host}/gsql/v1/statements?graph={graph}", headers=headers_gsql, data=query_gsql, verify=False, timeout=180)
print("Installation output:")
print(res_install.text)

# 3. Execute Query on HHG-001 (Transaction 3514030)
flagged_txn_id = "3514030"
print(f"\n--- Executing investigate_transaction for HHG-001 (txn={flagged_txn_id}) ---")
query_url = f"{host}/restpp/query/{graph}/investigate_transaction?target_txn={flagged_txn_id}"
resp_q = requests.get(query_url, headers=headers_rest, verify=False, timeout=30)
print(f"Query Response Status: {resp_q.status_code}")

if resp_q.status_code == 200:
    res_data = resp_q.json()
    print("\nStructured Evidence Retrieved (JSON):")
    print(json.dumps(res_data, indent=2))
else:
    print(f"Query error: {resp_q.text}")
