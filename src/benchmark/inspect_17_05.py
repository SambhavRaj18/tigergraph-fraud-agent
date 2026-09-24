"""
Inspect all transactions for HHG-017 (C04570) and HHG-005 (C02923).
"""

import os
import pandas as pd

txns_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/transactions.csv")
id_path = os.path.abspath("d:/HHHGOA/tigergraph-fraud-agent/data/raw/identity.csv")

df_txns = pd.read_csv(txns_path, low_memory=False)
df_id = pd.read_csv(id_path)
df_txns['ts'] = pd.to_datetime(df_txns['ts'])

print("=== ALL TRANSACTIONS FOR HHG-017 (C04570) ===")
c17 = df_txns[df_txns['customer_id'] == 'C04570'].sort_values('ts')
for _, t in c17.iterrows():
    tid = int(t['TransactionID'])
    id_r = df_id[df_id['TransactionID'] == tid]
    dev = id_r.iloc[0].get('DeviceInfo') if not id_r.empty else ''
    is_new = id_r.iloc[0].get('id_15') if not id_r.empty else ''
    fl = " <-- FLAGGED" if tid == 3450629 else ""
    print(f"Txn {tid} | {t['ts']} | ${t['TransactionAmt']:>7.2f} | {t['channel']:<9} | {t['ProductCD']} | Reg: {str(t['addr1']):<5} | Dev: {dev} ({is_new}){fl}")

print("\n=== ALL TRANSACTIONS FOR HHG-005 (C02923) ===")
c05 = df_txns[df_txns['customer_id'] == 'C02923'].sort_values('ts')
for _, t in c05.iterrows():
    tid = int(t['TransactionID'])
    id_r = df_id[df_id['TransactionID'] == tid]
    dev = id_r.iloc[0].get('DeviceInfo') if not id_r.empty else ''
    is_new = id_r.iloc[0].get('id_15') if not id_r.empty else ''
    fl = " <-- FLAGGED" if tid == 3523199 else ""
    print(f"Txn {tid} | {t['ts']} | ${t['TransactionAmt']:>7.2f} | {t['channel']:<9} | {t['ProductCD']} | Reg: {str(t['addr1']):<5} | Dev: {dev} ({is_new}){fl}")

