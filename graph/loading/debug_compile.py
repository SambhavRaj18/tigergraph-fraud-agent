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
headers = {'Authorization': f'Bearer {jwt_token}', 'Content-Type': 'text/plain'}

def test_job(body: str, name="test_j"):
    full = f"""
    USE GRAPH FraudInvestigation
    DROP JOB {name}
    CREATE LOADING JOB {name} FOR GRAPH FraudInvestigation {{
        {body}
    }}
    """
    res = requests.post(f'{host}/gsql/v1/statements?graph={graph}', headers=headers, data=full, verify=False)
    print(f"--- Test {name} ---")
    print(res.text[:300])

# Test 1: WHERE $0 IS NOT EMPTY
test_job("DEFINE FILENAME f; LOAD f TO EDGE MADE VALUES ($0, $1) WHERE $0 IS NOT EMPTY USING header=\"true\", separator=\",\";", "w1")

# Test 2: WHERE $0 != ""
test_job("DEFINE FILENAME f; LOAD f TO EDGE MADE VALUES ($0, $1) WHERE $0 != \"\" USING header=\"true\", separator=\",\";", "w2")

# Test 3: WHERE clause with USING before WHERE
test_job("DEFINE FILENAME f; LOAD f TO EDGE MADE VALUES ($0, $1) USING header=\"true\", separator=\",\" WHERE $0 IS NOT EMPTY;", "w3")

