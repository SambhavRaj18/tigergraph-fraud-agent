"""
Comprehensive 6-Stage Final Deliverables & Integrity Audit.
"""

import os
import json
import glob
import pandas as pd
import requests
from src.graph_client import TigerGraphClient

def run_validation():
    cases_dir = "cases"
    files = sorted(glob.glob(os.path.join(cases_dir, "HHG-*.json")))
    print("=" * 110)
    print(f"RUNNING COMPREHENSIVE 6-STAGE VALIDATION ACROSS {len(files)} CASE DELIVERABLES")
    print("=" * 110)

    # 1. JSON Schema Validation
    schema_errors = []
    required_keys = ["case_id", "case", "sar", "next_best_actions", "evidence_requests", "stop_reason", "tool_calls", "latency_s"]
    case_required_keys = ["status", "verdict", "fraud_probability", "pattern", "pattern_description", "affected_txn_ids", "first_suspicious_txn_id", "exposure_usd", "evidence", "summary"]
    sar_required_keys = ["file", "total_amount_usd", "activity_dates", "subjects", "narrative"]
    nba_required_keys = ["initial", "final", "what_changed"]

    for fp in files:
        cid = os.path.basename(fp).replace(".json", "")
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k in required_keys:
            if k not in d: schema_errors.append(f"{cid}: missing top-level key {k}")
        for k in case_required_keys:
            if k not in d.get("case", {}): schema_errors.append(f"{cid}: missing case key {k}")
        for k in sar_required_keys:
            if k not in d.get("sar", {}): schema_errors.append(f"{cid}: missing sar key {k}")
        for k in nba_required_keys:
            if k not in d.get("next_best_actions", {}): schema_errors.append(f"{cid}: missing nba key {k}")

    print(f"1. JSON Schema Validation:        {len(schema_errors)} errors")
    if schema_errors:
        for e in schema_errors: print(f"   - {e}")

    # 2. Provenance Audit
    prov_errors = []
    for fp in files:
        cid = os.path.basename(fp).replace(".json", "")
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        for req in d.get("evidence_requests", []):
            resp = req.get("assumed_response", "")
            if resp and not resp.startswith("SIMULATED / ASSUMED (not in dataset)"):
                prov_errors.append(f"{cid}: un-annotated assumed_response: {resp}")
        for act in d.get("next_best_actions", {}).get("final", []):
            r = act.get("reason", "").lower()
            if "customer denied" in r or "customer confirmed" in r:
                prov_errors.append(f"{cid}: action reason contains unobserved customer statement: {act.get('reason')}")

    print(f"2. Factual Provenance Audit:       {len(prov_errors)} errors")
    if prov_errors:
        for e in prov_errors: print(f"   - {e}")

    # 3. Policy Audit
    policy_errors = []
    for fp in files:
        cid = os.path.basename(fp).replace(".json", "")
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        sar_file = d["sar"]["file"]
        actions = [a["action"] for a in d["next_best_actions"]["final"]]
        if sar_file and "FILE_REPORT" not in actions:
            policy_errors.append(f"{cid}: SAR filed but FILE_REPORT missing in final actions")
        if not sar_file and "FILE_REPORT" in actions:
            policy_errors.append(f"{cid}: FILE_REPORT in final actions but SAR.file is false")

    print(f"3. Policy Alignment Audit:         {len(policy_errors)} errors")
    if policy_errors:
        for e in policy_errors: print(f"   - {e}")

    # 4. ID Referential Integrity Audit
    ref_errors = []
    df_pack = pd.read_csv("data/raw/case_pack.csv")
    valid_case_ids = set(df_pack["case_id"].astype(str))
    for fp in files:
        cid = os.path.basename(fp).replace(".json", "")
        if cid not in valid_case_ids:
            ref_errors.append(f"{cid}: invalid case ID not in case_pack.csv")

    print(f"4. ID Referential-Integrity Audit: {len(ref_errors)} errors")
    if ref_errors:
        for e in ref_errors: print(f"   - {e}")

    # 5. Graph Case-Memory Count
    client = TigerGraphClient()
    token = client.get_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{client.host}/restpp/graph/{client.graph}/vertices/ClosedCase?count_only=true", headers=headers, verify=False)
    cnt = r.json()["results"][0]["count"]
    print(f"5. Graph Case-Memory Count:        {cnt} ClosedCase vertices (Target: exactly 5,585)")

    # 6. Benchmark Summary Table
    print("\n" + "=" * 110)
    print("6. FINAL 20-CASE BENCHMARK SUMMARY TABLE")
    print("=" * 110)
    print(f"{'Case':<10} {'Trigger':<16} {'Verdict':<12} {'Pattern':<28} {'Prob':<6} {'Exposure':<12} {'SAR':<6} {'Dates'}")
    print("-" * 110)
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        dates_str = str(d["sar"]["activity_dates"]) if d["sar"]["file"] else "-"
        exp_str = f"${d['case']['exposure_usd']:.2f}"
        trig = df_pack.loc[df_pack["case_id"]==d["case_id"], "trigger_type"].values[0]
        print(f"{d['case_id']:<10} {trig:<16} {d['case']['verdict']:<12} {d['case']['pattern']:<28} {d['case']['fraud_probability']:^6.2f} {exp_str:>12} {str(d['sar']['file']):<6} {dates_str}")

    print("=" * 110)

if __name__ == "__main__":
    run_validation()
