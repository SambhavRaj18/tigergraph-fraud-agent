"""
Audit multi-transaction exposure for all 13 fraud cases.
"""

import os
import pandas as pd

txns_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/transactions.csv")
pack_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/case_pack.csv")
id_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/identity.csv")

df_txns = pd.read_csv(txns_path, low_memory=False)
df_pack = pd.read_csv(pack_path)
df_id = pd.read_csv(id_path)
df_txns['ts'] = pd.to_datetime(df_txns['ts'])

for idx, row in df_pack.iterrows():
    cid = row['case_id']
    tid = int(row['flagged_txn_id'])
    cust_id = row['customer_id']
    card_id = row['card_id']
    ttype = row['trigger_type']
    
    c_txns = df_txns[df_txns['customer_id'] == cust_id].sort_values('ts').copy()
    flagged = c_txns[c_txns['TransactionID'] == tid].iloc[0]
    flagged_ts = flagged['ts']
    
    # Check 24h window
    near = c_txns[(c_txns['ts'] >= flagged_ts - pd.Timedelta(hours=24)) & (c_txns['ts'] <= flagged_ts + pd.Timedelta(hours=24))]
    
    print(f"\n--- {cid} (Flagged: {tid}, ${flagged['TransactionAmt']:.2f}, {flagged['channel']}, Prod: {flagged['ProductCD']}) ---")
    for _, t in near.iterrows():
        t_id = int(t['TransactionID'])
        id_r = df_id[df_id['TransactionID'] == t_id]
        dev = id_r.iloc[0]['DeviceInfo'] if not id_r.empty else ''
        diff_m = (t['ts'] - flagged_ts).total_seconds() / 60.0
        is_fl = " [FLAGGED]" if t_id == tid else ""
        print(f"  Txn {t_id} | {diff_m:+6.1f}m | ${t['TransactionAmt']:>7.2f} | {t['channel']} | Prod: {t['ProductCD']} | Reg: {str(t['addr1']):<5} | Dev: {dev}{is_fl}")
