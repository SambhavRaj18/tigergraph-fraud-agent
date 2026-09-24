import requests
import urllib3
import os
from dotenv import load_dotenv

urllib3.disable_warnings()

load_dotenv('d:/HHHGOA/tigergraph-fraud-agent/.env')
host = os.getenv('TG_HOST').rstrip('/')
secret = os.getenv('TG_SECRET')
graph = os.getenv('TG_GRAPHNAME', 'FraudInvestigation')

r = requests.post(f'{host}/gsql/v1/tokens', json={'secret': secret, 'graph': graph, 'lifetime': 1000000}, verify=False)
jwt_token = r.json().get('token')
headers_gsql = {'Authorization': f'Bearer {jwt_token}', 'Content-Type': 'text/plain'}
headers_rest = {'Authorization': f'Bearer {jwt_token}'}

def run_gsql(stmt: str):
    res = requests.post(f'{host}/gsql/v1/statements?graph={graph}', headers=headers_gsql, data=stmt, verify=False)
    return res.text

# Test with positional indexing
job4 = """
USE GRAPH FraudInvestigation
DROP JOB load_test_4
CREATE LOADING JOB load_test_4 FOR GRAPH FraudInvestigation {
    DEFINE FILENAME file_customer;
    LOAD file_customer TO VERTEX Customer VALUES ($0) USING header="true", separator=",";
}
"""
print("1. Creating Job 4:")
print(run_gsql(job4))

# Test loading a few customers via RESTPP DDL endpoint
sample_csv = "customer_id\nC99999\nC99998\n"
url_ddl = f"{host}/restpp/ddl/{graph}?tag=file_customer&filename=load_test_4"
print("\n2. Streaming data to RESTPP DDL endpoint:")
res_load = requests.post(url_ddl, headers=headers_rest, data=sample_csv, verify=False)
print("Load status:", res_load.status_code)
print("Load response:", res_load.text)

# Check vertex count
res_cnt = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers_rest, json={"function": "stat_vertex_number", "type": "Customer"}, verify=False)
print("\n3. Customer count check:")
print(res_cnt.text)

