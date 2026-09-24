import pandas as pd
import json
import glob

df = pd.read_csv("d:/HHHGOA/tigergraph-fraud-agent/graph/loading/data_prepared/vertices_transaction.csv", low_memory=False)
cases = sorted(glob.glob("d:/HHHGOA/tigergraph-fraud-agent/cases/HHG-*.json"))

print("EPISODE DATE SPANS:")
for c in cases:
    with open(c, "r") as f:
        d = json.load(f)
    cid = d["case_id"]
    txns = [int(t) for t in d["case"]["affected_txn_ids"] if t]
    if txns:
        sub = df[df["transaction_id"].isin(txns)]
        min_ts = sub["ts"].min()
        max_ts = sub["ts"].max()
        min_d = str(min_ts).split(" ")[0]
        max_d = str(max_ts).split(" ")[0]
        print(f"{cid}: {len(txns):2d} txns -> min_date={min_d}, max_date={max_d}")
