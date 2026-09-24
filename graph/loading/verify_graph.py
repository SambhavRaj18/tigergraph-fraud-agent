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

# Vertices
v_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_vertex_number", "type": "*"}, verify=False)
v_dict = {item["v_type"]: item["count"] for item in v_resp.json().get("results", [])}

# Edges
e_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_edge_number", "type": "*"}, verify=False)
e_dict = {item["e_type"]: item["count"] for item in e_resp.json().get("results", [])}

print("=" * 80)
print("FINAL LIVE GRAPH VERIFICATION SUMMARY (FraudInvestigation)")
print("=" * 80)
print(f"{'Vertex Type':<25} | {'Live Count in Graph':<22} | {'Prepared Target':<18} | {'Status':<10}")
print("-" * 80)
exp_v = {
    "Customer": 13553,
    "Card": 1927,
    "Transaction": 590742,
    "DeviceProfile": 9705,
    "EmailDomain": 60,
    "BillingRegion": 332,
    "ClosedCase": 5565
}
for v, exp_cnt in exp_v.items():
    actual_cnt = v_dict.get(v, 0)
    status = "EXACT MATCH" if actual_cnt == exp_cnt else "MISMATCH"
    print(f"{v:<25} | {actual_cnt:<22,} | {exp_cnt:<18,} | {status:<10}")

print("\n" + "=" * 80)
print(f"{'Edge Type':<25} | {'Live Count in Graph':<22} | {'Prepared Target':<18} | {'Status':<10}")
print("-" * 80)
exp_e = {
    "OWNS": 1927,
    "OWNED_BY (reverse)": 1927,
    "MADE": 14975,
    "TRANSACTION_OF (rev)": 14975,
    "FROM_DEVICE": 140784,
    "DEVICE_OF (reverse)": 140784,
    "PURCHASER_EMAIL": 496262,
    "EMAIL_OF (reverse)": 496262,
    "BILLED_IN": 525003,
    "REGION_OF (reverse)": 525003,
    "PERFORMED": 590742,
    "PERFORMED_BY (rev)": 590742,
    "INVOLVES": 14955,
    "ON_CARD": 5565,
    "CONNECTED_TO": 92,
    "NEXT": 577189,
    "RECIPIENT_EMAIL": 137453,
    "RECIPIENT_OF (rev)": 137453
}
for e, exp_cnt in exp_e.items():
    clean_e = e.split(" ")[0]
    actual_cnt = e_dict.get(clean_e, 0)
    status = "EXACT MATCH" if actual_cnt == exp_cnt else "MISMATCH"
    print(f"{e:<25} | {actual_cnt:<22,} | {exp_cnt:<18,} | {status:<10}")

print("=" * 80)
