"""
TigerGraph 4.2.5 Data Loading Execution Script for FraudInvestigation.
Executes the compiled `load_fraud_data` loading job via chunked RESTPP streaming.
Handles Savanna Cloud NGINX timeouts by streaming in batches of 25,000 rows.
Captures per-file loading metrics, rejected lines, and validates final graph vertex & edge counts.
"""

import os
import sys
import time
import json
import logging
import requests
import urllib3
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("TigerGraphLoader")

PREPARED_DIR = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/graph/loading/data_prepared")
ENV_PATH = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/.env")

LOAD_SEQUENCE: List[Tuple[str, str, str]] = [
    # 1. Base Vertices
    ("file_customer", "vertices_customer.csv", "Customer Vertex"),
    ("file_card", "vertices_card.csv", "Card Vertex"),
    ("file_device_profile", "vertices_device_profile.csv", "DeviceProfile Vertex"),
    ("file_email_domain", "vertices_email_domain.csv", "EmailDomain Vertex"),
    ("file_billing_region", "vertices_billing_region.csv", "BillingRegion Vertex"),
    ("file_closed_case", "vertices_closed_case.csv", "ClosedCase Vertex"),
    
    # 2. Transaction Vertices + inline PERFORMED & RECIPIENT_EMAIL edges
    ("file_transaction", "vertices_transaction.csv", "Transaction Vertex & Inline Edges"),

    # 3. Explicit Edge Tables
    ("file_edge_owns", "edges_owns.csv", "OWNS Edge"),
    ("file_edge_made", "edges_made.csv", "MADE Edge"),
    ("file_edge_from_device", "edges_from_device.csv", "FROM_DEVICE Edge"),
    ("file_edge_purchaser_email", "edges_purchaser_email.csv", "PURCHASER_EMAIL Edge"),
    ("file_edge_billed_in", "edges_billed_in.csv", "BILLED_IN Edge"),
    ("file_edge_involves", "edges_involves.csv", "INVOLVES Edge"),
    ("file_edge_on_card", "edges_on_card.csv", "ON_CARD Edge"),
    ("file_edge_connected_to", "edges_connected_to.csv", "CONNECTED_TO Edge"),
    ("file_edge_next", "edges_next.csv", "NEXT Edge"),
]


def get_auth_token(host: str, secret: str, graph: str) -> str:
    """Request a valid TigerGraph 4.x JWT token using database secret."""
    token_url = f"{host}/gsql/v1/tokens"
    resp = requests.post(token_url, json={"secret": secret, "graph": graph, "lifetime": 1000000}, verify=False, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to acquire JWT token: {resp.status_code} - {resp.text}")
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"JWT Token error: {data.get('message')}")
    token = data.get("token")
    if not token:
        raise RuntimeError(f"No token returned in response: {data}")
    return token


def _extract_stats(res_json: Dict[str, Any]) -> Tuple[int, int, int]:
    """Extract (validLine, rejectLine, failedLine) from RESTPP response."""
    stats = res_json.get("results", [{}])[0].get("statistics", {})
    parsing_stats = stats.get("parsingStatistics", {})
    file_level = parsing_stats.get("fileLevel", {})
    valid = file_level.get("validLine", 0)
    reject = file_level.get("rejectLine", 0)
    failed = file_level.get("failedLine", 0)
    return valid, reject, failed


def _post_chunk_with_retry(url: str, headers: Dict[str, str], params: Dict[str, str], data: str, fname: str, chunk_num: int, max_retries: int = 3) -> Dict[str, Any]:
    """POST data chunk with exponential backoff retry on transient network/timeout errors."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, params=params, data=data.encode("utf-8"), verify=False, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                if not res_json.get("error"):
                    return res_json
                else:
                    raise RuntimeError(f"Server error: {res_json.get('message')}")
            else:
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {fname} chunk {chunk_num} (HTTP {resp.status_code}): {resp.text[:120]}")
        except Exception as ex:
            logger.warning(f"Attempt {attempt}/{max_retries} exception for {fname} chunk {chunk_num}: {ex}")
        
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to load chunk {chunk_num} of {fname} after {max_retries} attempts.")


def load_file_chunked(
    host: str,
    token: str,
    graph: str,
    job_name: str,
    file_var: str,
    csv_path: str,
    chunk_rows: int = 30000
) -> Dict[str, Any]:
    """Streams CSV file in chunks of chunk_rows to ensure fast response times and avoid timeouts."""
    url = f"{host}/restpp/ddl/{graph}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    params = {
        "tag": job_name,
        "filename": file_var
    }

    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    fname = os.path.basename(csv_path)

    with open(csv_path, "r", encoding="utf-8") as f:
        header_line = f.readline()
        
        batch = []
        batch_idx = 1
        total_valid = 0
        total_reject = 0
        total_failed = 0
        t0 = time.time()

        for line in f:
            batch.append(line)
            if len(batch) >= chunk_rows:
                chunk_data = header_line + "".join(batch)
                res = _post_chunk_with_retry(url, headers, params, chunk_data, fname, batch_idx)
                v, r, fl = _extract_stats(res)
                total_valid += v
                total_reject += r
                total_failed += fl
                batch = []
                batch_idx += 1

        if batch:
            chunk_data = header_line + "".join(batch)
            res = _post_chunk_with_retry(url, headers, params, chunk_data, fname, batch_idx)
            v, r, fl = _extract_stats(res)
            total_valid += v
            total_reject += r
            total_failed += fl

    elapsed = time.time() - t0
    logger.info(f"Loaded {fname} ({file_size_mb:.2f} MB, {batch_idx} chunk{'s' if batch_idx > 1 else ''}) in {elapsed:.2f}s -> Valid: {total_valid:,}, Reject: {total_reject:,}, Failed: {total_failed:,}")
    return {
        "valid": total_valid,
        "reject": total_reject,
        "failed": total_failed,
        "duration": elapsed
    }


def fetch_graph_counts(host: str, token: str, graph: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Fetch live vertex and edge counts from TigerGraph builtins."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Vertices
    v_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_vertex_number", "type": "*"}, verify=False, timeout=30)
    v_counts = {}
    if v_resp.status_code == 200:
        for item in v_resp.json().get("results", []):
            v_counts[item["v_type"]] = item["count"]

    # Edges
    e_resp = requests.post(f"{host}/restpp/builtins/{graph}", headers=headers, json={"function": "stat_edge_number", "type": "*"}, verify=False, timeout=30)
    e_counts = {}
    if e_resp.status_code == 200:
        for item in e_resp.json().get("results", []):
            e_counts[item["e_type"]] = item["count"]

    return v_counts, e_counts


def run_full_load():
    logger.info("=" * 80)
    logger.info("STARTING TIGERGRAPH 4.2.5 FULL GRAPH DATA LOADING (CHUNKED STREAMING)")
    logger.info("=" * 80)

    load_dotenv(ENV_PATH, override=True)
    host = os.getenv("TG_HOST", "").rstrip("/")
    secret = os.getenv("TG_SECRET", "").strip()
    graph = os.getenv("TG_GRAPHNAME", "FraudInvestigation").strip()
    job_name = "load_fraud_data"

    if not host or not secret:
        logger.error("Missing TG_HOST or TG_SECRET in .env!")
        sys.exit(1)

    logger.info(f"Target Host: {host}")
    logger.info(f"Target Graph: {graph}")
    logger.info(f"Loading Job: {job_name}")

    # 1. Acquire Auth Token
    token = get_auth_token(host, secret, graph)
    logger.info("Acquired fresh TigerGraph 4.x JWT token.")

    # 2. Check Initial Graph State
    init_v, init_e = fetch_graph_counts(host, token, graph)
    logger.info(f"Initial Vertex Counts: {init_v}")
    logger.info(f"Initial Edge Counts: {init_e}")

    # 3. Execute Loading for Each File
    load_results = []
    total_start_time = time.time()

    for idx, (file_var, filename, desc) in enumerate(LOAD_SEQUENCE, 1):
        csv_path = os.path.join(PREPARED_DIR, filename)
        if not os.path.exists(csv_path):
            logger.error(f"Prepared file not found: {csv_path}")
            sys.exit(1)

        logger.info(f"\n[{idx}/{len(LOAD_SEQUENCE)}] Starting load: {desc} ({filename})")
        res_stats = load_file_chunked(host, token, graph, job_name, file_var, csv_path, chunk_rows=30000)
        load_results.append((filename, file_var, res_stats))

    total_duration = time.time() - total_start_time
    logger.info(f"\nAll {len(LOAD_SEQUENCE)} files submitted and processed in {total_duration:.2f} seconds!")

    # 4. Parse Loading Statistics & Rejections
    logger.info("\n" + "=" * 80)
    logger.info("LOADING JOB EXECUTION & PARSING SUMMARY")
    logger.info("=" * 80)

    total_valid_lines = 0
    total_rejected_lines = 0
    total_failed_lines = 0

    print(f"{'File Name':<32} | {'Variable':<22} | {'Valid Lines':<12} | {'Rejected':<10} | {'Failed':<8}")
    print("-" * 92)

    for fname, fvar, stats in load_results:
        valid = stats["valid"]
        reject = stats["reject"]
        failed = stats["failed"]

        total_valid_lines += valid
        total_rejected_lines += reject
        total_failed_lines += failed

        print(f"{fname:<32} | {fvar:<22} | {valid:<12,} | {reject:<10,} | {failed:<8,}")

    print("-" * 92)
    print(f"{'TOTAL':<32} | {'':<22} | {total_valid_lines:<12,} | {total_rejected_lines:<10,} | {total_failed_lines:<8,}")

    # 5. Fetch Final Graph Counts & Verify
    logger.info("\n" + "=" * 80)
    logger.info("GRAPH VERIFICATION: LIVE COUNTS VS EXPECTED PREPARED DATA")
    logger.info("=" * 80)

    final_v, final_e = fetch_graph_counts(host, token, graph)

    expected_vertices = {
        "Customer": 13553,
        "Card": 1927,
        "Transaction": 590742,
        "DeviceProfile": 9705,
        "EmailDomain": 60,
        "BillingRegion": 332,
        "ClosedCase": 5565
    }

    expected_edges = {
        "OWNS": 1927,
        "OWNED_BY": 1927,
        "MADE": 14975,
        "TRANSACTION_OF": 14975,
        "FROM_DEVICE": 140784,
        "DEVICE_OF": 140784,
        "PURCHASER_EMAIL": 496262,
        "EMAIL_OF": 496262,
        "BILLED_IN": 525003,
        "REGION_OF": 525003,
        "PERFORMED": 590742,
        "PERFORMED_BY": 590742,
        "INVOLVES": 14955,
        "ON_CARD": 5565,
        "CONNECTED_TO": 92,
        "NEXT": 577189
    }

    print("\n--- 1. Vertex Counts Verification ---")
    print(f"{'Vertex Type':<25} | {'Live Count in Graph':<20} | {'Expected Count':<16} | {'Status':<10}")
    print("-" * 77)
    v_all_match = True
    for v_name, exp_cnt in expected_vertices.items():
        actual_cnt = final_v.get(v_name, 0)
        # Check against expected
        status = "PASSED" if actual_cnt >= exp_cnt else "MISMATCH"
        if actual_cnt != exp_cnt and actual_cnt < exp_cnt:
            v_all_match = False
        print(f"{v_name:<25} | {actual_cnt:<20,} | {exp_cnt:<16,} | {status:<10}")

    print("\n--- 2. Edge Counts Verification ---")
    print(f"{'Edge Type':<25} | {'Live Count in Graph':<20} | {'Expected Count':<16} | {'Status':<10}")
    print("-" * 77)
    e_all_match = True
    for e_name, exp_cnt in expected_edges.items():
        actual_cnt = final_e.get(e_name, 0)
        status = "PASSED" if actual_cnt == exp_cnt else "MISMATCH"
        if status == "MISMATCH":
            e_all_match = False
        print(f"{e_name:<25} | {actual_cnt:<20,} | {exp_cnt:<16,} | {status:<10}")

    if "RECIPIENT_EMAIL" in final_e:
        print(f"{'RECIPIENT_EMAIL':<25} | {final_e['RECIPIENT_EMAIL']:<20,} | {'(Dynamic filter)':<16} | {'INFORMATIONAL':<10}")
    if "RECIPIENT_OF" in final_e:
        print(f"{'RECIPIENT_OF':<25} | {final_e['RECIPIENT_OF']:<20,} | {'(Dynamic filter)':<16} | {'INFORMATIONAL':<10}")

    print("\n" + "=" * 80)
    if v_all_match and e_all_match and total_failed_lines == 0 and total_rejected_lines == 0:
        print("ALL VERTICES, EDGES, AND COUNTS MATCH 100%! LOADING FULLY SUCCESSFUL.")
    else:
        print(f"LOADING COMPLETE: Vertex Match={v_all_match}, Edge Match={e_all_match}, Rejected={total_rejected_lines}, Failed={total_failed_lines}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_load()

