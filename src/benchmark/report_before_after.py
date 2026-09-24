"""
Generate Before / After Benchmark Comparison Report.
"""

import os
import json
import pandas as pd

cases_dir = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/cases")
pack_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/case_pack.csv")

pack = pd.read_csv(pack_path)

rows = []
for idx, r in pack.iterrows():
    cid = r["case_id"]
    fpath = os.path.join(cases_dir, f"{cid}.json")
    with open(fpath, "r", encoding="utf-8") as f:
        d = json.load(f)
    c = d["case"]
    sar = d["sar"]
    nba = d["next_best_actions"]
    
    rows.append({
        "Case ID": cid,
        "Trigger Type": r["trigger_type"],
        "Verdict": c["verdict"],
        "Pattern": c["pattern"],
        "Txn Count": len(c["affected_txn_ids"]),
        "First Txn ID": c["first_suspicious_txn_id"],
        "Exposure ($)": f"{c['exposure_usd']:,.2f}",
        "SAR": "YES" if sar["file"] else "NO",
        "Final Next Best Actions": " -> ".join([a["action"] for a in nba["final"]])
    })

df = pd.DataFrame(rows)
print("\n" + "=" * 130)
print("FINAL CORRECTED 20-CASE BENCHMARK DELIVERABLES SUMMARY")
print("=" * 130)
print(df.to_string(index=False))
