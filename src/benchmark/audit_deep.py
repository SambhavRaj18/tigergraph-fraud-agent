"""
Deep audit script to inspect transaction windows, device links, and exposure for all 20 cases.
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

print("=" * 90)
print("AUDIT: TRANSACTION SEQUENCES & BURSTS FOR ALL 20 CASES")
print("=" * 90)

for idx, row in df_pack.iterrows():
    cid = row['case_id']
    tid = int(row['flagged_txn_id'])
    cust_id = row['customer_id']
    card_id = row['card_id']
    ttype = row['trigger_type']
    ttext = row['trigger_text']
    
    c_txns = df_txns[df_txns['customer_id'] == cust_id].sort_values('ts').copy()
    flagged_rows = c_txns[c_txns['TransactionID'] == tid]
    if flagged_rows.empty:
        print(f"Case {cid}: Txn {tid} not found!")
        continue
    
    flagged = flagged_rows.iloc[0]
    flagged_ts = flagged['ts']
    
    # 48h before and 48h after
    w_start = flagged_ts - pd.Timedelta(hours=48)
    w_end = flagged_ts + pd.Timedelta(hours=48)
    near = c_txns[(c_txns['ts'] >= w_start) & (c_txns['ts'] <= w_end)]
    
    # Check identity
    id_row = df_id[df_id['TransactionID'] == tid]
    dev_info = "None"
    if not id_row.empty:
        dev_info = f"DeviceInfo={id_row.iloc[0].get('DeviceInfo')}, OS={id_row.iloc[0].get('id_30')}, is_new={id_row.iloc[0].get('id_15')}, is_proxy={id_row.iloc[0].get('id_23')}"

    print("-" * 90)
    print(f"CASE: {cid} | Customer: {cust_id} | Card: {card_id} | Trigger: {ttype}")
    print(f"Flagged Txn: {tid} (${flagged['TransactionAmt']:.2f}, {flagged['channel']}, Prod: {flagged['ProductCD']}, Reg: {flagged['addr1']}, Risk: {flagged['risk_score']}) at {flagged_ts}")
    print(f"Identity: {dev_info}")
    print(f"Trigger text: {ttext}")
    print(f"Total customer txns: {len(c_txns)} | Near txns (+-48h): {len(near)}")
    
    for _, t in near.iterrows():
        t_id = int(t['TransactionID'])
        is_fl = " <-- FLAGGED" if t_id == tid else ""
        diff_h = (t['ts'] - flagged_ts).total_seconds() / 3600.0
        print(f"  [{diff_h:+6.1f}h] Txn {t_id} | {t['ts']} | ${t['TransactionAmt']:>8.2f} | {t['channel']:<9} | Prod: {t['ProductCD']} | Reg: {str(t['addr1']):<5} | Risk: {t['risk_score']}{is_fl}")

