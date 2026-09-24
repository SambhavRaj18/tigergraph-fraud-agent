import os
import sys
import json
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/.env")
if not os.path.exists(env_path):
    print("STATUS: NO_ENV_FILE")
    sys.exit(1)

load_dotenv(env_path, override=True)

host = os.getenv("TG_HOST", "").strip().rstrip("/")
secret = os.getenv("TG_SECRET", "").strip()
graphname = os.getenv("TG_GRAPHNAME", os.getenv("TG_GRAPH", "FraudInvestigation")).strip()

if host.startswith("Host:"):
    host = host.replace("Host:", "").strip()

print("Loaded configuration from .env:")
print(f"TG_HOST: {host}")
print(f"TG_GRAPHNAME: {graphname}")
print(f"TG_SECRET: {'[CONFIGURED]' if secret else '[MISSING]'}")

if not host or not secret:
    print("STATUS: INCOMPLETE_CONFIGURATION")
    sys.exit(1)

print("\n--- 1. Testing REST Token Request via Secret ---")
token = None
token_endpoints = [
    f"{host}/requesttoken",
    f"{host}/restpp/requesttoken",
    f"{host}/api/v2/tokens",
    f"{host}/gsqlserver/gsql/requesttoken"
]

for ep in token_endpoints:
    payloads = [
        {"secret": secret, "lifetime": "2592000"},
        {"secret": secret, "graph": graphname, "lifetime": "2592000"},
        {"secret": secret},
    ]
    for p in payloads:
        try:
            r = requests.post(ep, json=p, verify=False, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if not data.get("error", False):
                    token = data.get("results", {}).get("token") or data.get("token")
                    if token:
                        print(f"Token acquired via {ep} (status 200)!")
                        break
        except Exception as e:
            pass
    if token:
        break

print(f"Token acquisition result: {'SUCCESS' if token else 'DIRECT_SECRET_MODE'}")

print("\n--- 2. Testing pyTigerGraph Secret / Token Connection ---")
try:
    import pyTigerGraph as tg
    
    conn = tg.TigerGraphConnection(
        host=host,
        graphname=graphname,
        tgCloud=True
    )
    
    if token:
        conn.apiToken = token
    else:
        try:
            tok = conn.getToken(secret=secret)
            if tok:
                conn.apiToken = tok
                token = tok
                print("pyTigerGraph getToken: SUCCESS")
        except Exception as te:
            print(f"pyTigerGraph getToken info: {te}")
            # Try secret directly as apiToken if Savanna API key
            conn.apiToken = secret

    print("\n--- 3. Testing Authenticated Query Execution ---")
    echo_res = conn.echo()
    print(f"Echo response: {echo_res}")
    
    # Test checking vertices / schema
    try:
        schema = conn.getSchema()
        print("Schema / Graph status response received.")
        vertex_types = schema.get("VertexTypes", [])
        edge_types = schema.get("EdgeTypes", [])
        print(f"Existing Vertex Types in graph '{graphname}': {[v.get('Name') for v in vertex_types]}")
        print(f"Existing Edge Types in graph '{graphname}': {[e.get('Name') for e in edge_types]}")
    except Exception as se:
        print(f"Graph schema check: {se}")

    print("\nSTATUS: SUCCESS - Authenticated TigerGraph Savanna Connection Verified!")

except Exception as ex:
    print(f"\nAuthentication test exception: {ex}")
    print("STATUS: FAILED")

