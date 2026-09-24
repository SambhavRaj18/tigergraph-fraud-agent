import os
import sys
import json
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Load .env
env_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/.env")
if not os.path.exists(env_path):
    print("STATUS: NO_ENV_FILE")
    sys.exit(1)

load_dotenv(env_path, override=True)

host = os.getenv("TG_HOST", "").replace("Host:", "").strip().rstrip("/")
secret = os.getenv("TG_SECRET", "").strip()
graphname = os.getenv("TG_GRAPHNAME", os.getenv("TG_GRAPH", "FraudInvestigation")).strip()
username = os.getenv("TG_USERNAME", "tigergraph").strip()
password = os.getenv("TG_PASSWORD", "").strip()

print(f"Connecting to TigerGraph Savanna at: {host}")
print(f"Target Graph: {graphname}")

# 2. Read schema.gsql
schema_file = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/graph/schema/schema.gsql")
with open(schema_file, "r", encoding="utf-8") as f:
    schema_gsql = f.read()

print(f"Read schema.gsql ({len(schema_gsql)} chars, {len(schema_gsql.splitlines())} lines).")

# 3. Deploy Schema via pyTigerGraph / GSQL
try:
    import pyTigerGraph as tg
    
    is_tgcloud = ".tgcloud.io" in host.lower()
    conn = tg.TigerGraphConnection(
        host=host,
        graphname=graphname,
        username=username if username else None,
        password=password if password else None,
        tgCloud=is_tgcloud
    )
    
    print("\n--- Deploying GSQL Schema ---")
    res = conn.gsql(schema_gsql)
    print("GSQL Output:")
    print(res)

except Exception as e:
    print(f"GSQL Deployment Exception: {e}")

# 4. Verify Deployed Schema via RESTPP
print("\n--- Verifying Schema via RESTPP ---")
try:
    url = f"{host}/restpp/schema/{graphname}"
    headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    resp = requests.get(url, headers=headers, verify=False, timeout=15)
    
    print(f"RESTPP Schema Endpoint Status: {resp.status_code}")
    data = resp.json()
    
    if not data.get("error", False):
        results = data.get("results", data)
        vertex_types = [v.get("Name") for v in results.get("VertexTypes", [])]
        edge_types = [e.get("Name") for e in results.get("EdgeTypes", [])]
        
        print("\n=== DEPLOYED SCHEMA VERIFICATION ===")
        print(f"Total Vertex Types: {len(vertex_types)}")
        print(f"Vertices: {vertex_types}")
        print(f"\nTotal Edge Types: {len(edge_types)}")
        print(f"Edges: {edge_types}")
        print("\nSTATUS: SCHEMA DEPLOYMENT SUCCESSFUL!")
    else:
        print("RESTPP Schema Response:")
        print(json.dumps(data, indent=2))
except Exception as ve:
    print(f"Schema Verification Error: {ve}")

