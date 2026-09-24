import os
import sys
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/.env")
if not os.path.exists(env_path):
    print("STATUS: NO_ENV_FILE")
    sys.exit(0)

load_dotenv(env_path, override=True)

host = os.getenv("TG_HOST", "").strip()
username = os.getenv("TG_USERNAME", "").strip()
password = os.getenv("TG_PASSWORD", "").strip()
graph = os.getenv("TG_GRAPH", os.getenv("TG_GRAPHNAME", "FraudInvestigation")).strip()
secret = os.getenv("TG_SECRET", "").strip()

print("Loaded .env successfully.")
print(f"TG_HOST: {host if host else '[MISSING]'}")
print(f"TG_USERNAME: {username if username else '[MISSING]'}")
print(f"TG_PASSWORD: {'[CONFIGURED]' if password else '[NOT_SET]'}")
print(f"TG_GRAPH: {graph if graph else '[MISSING]'}")
print(f"TG_SECRET: {'[CONFIGURED]' if secret else '[NOT_SET]'}")

print("\n--- 1. Testing Host Reachability ---")
try:
    norm_host = host if host.startswith("http") else f"https://{host}"
    print(f"Connecting to host: {norm_host}")
    r = requests.get(norm_host, timeout=15, verify=False)
    print(f"Host HTTP status: {r.status_code}")
except Exception as e:
    print(f"Direct HTTP check result: {e}")

print("\n--- 2. Testing pyTigerGraph Connectivity & Authentication ---")
try:
    import pyTigerGraph as tg
    is_tgcloud = ".tgcloud.io" in host.lower()
    
    conn = tg.TigerGraphConnection(
        host=host,
        graphname=graph if graph else None,
        username=username if username else None,
        password=password if password else None,
        tgCloud=is_tgcloud
    )
    
    echo_res = conn.echo()
    print(f"Echo response: {echo_res}")
    
    # Query database status / catalog via GSQL
    print("\n--- 3. Querying Database Catalog & Graph Status ---")
    try:
        ls_res = conn.gsql("ls")
        print("Database Status (GSQL catalog):")
        print(ls_res)
    except Exception as ge:
        print(f"GSQL status check: {ge}")
        
    print("\nSTATUS: SUCCESS - Connection and Authentication Verified!")
except Exception as te:
    print(f"\nConnection / Authentication Detail: {te}")
    print("STATUS: FAILED")
