"""
Detailed burst analysis for all 20 benchmark cases.
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
    
    # +- 24h window
    near = c_txns[(c_txns['ts'] >= flagged_ts - pd.Timedelta(hours=24)) & (c_txns['ts'] <= flagged_ts + pd.Timedelta(hours=24))]
    id_row = df_id[df_id['TransactionID'] == tid]
    dev = id_row.iloc[0].get('DeviceInfo') if not id_row.empty else 'None'
    is_new = id_row.iloc[0].get('id_15') if not id_row.empty else 'None'
    
    print(f"\n=== {cid} | Cust: {cust_id} | Card: {card_id} | Flagged: {tid} (${flagged['TransactionAmt']:.2f}, {flagged['channel']}, Prod: {flagged['ProductCD']}, Risk: {flagged['risk_score']}) | Dev: {dev} (New={is_new}) ===")
    print(f"Trigger: {ttype} | Text: {row['trigger_text']}")
    for _, t in near.iterrows():
        t_id = int(t['TransactionID'])
        is_fl = " <-- FLAGGED" if t_id == tid else ""
        diff_h = (t['ts'] - flagged_ts).total_seconds() / 3600.0
        print(f"  [{diff_h:+5.1f}h] Txn {t_id} | {t['ts']} | ${t['TransactionAmt']:>7.2f} | {t['channel']:<9} | Prod: {t['ProductCD']} | Reg: {str(t['addr1']):<5} | Risk: {t['risk_score']}{is_fl}")

