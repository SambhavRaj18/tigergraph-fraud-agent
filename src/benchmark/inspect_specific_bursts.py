import pandas as pd
df_txns = pd.read_csv('d:/HHHGOA/tigergraph-fraud-agent/data/raw/transactions.csv', low_memory=False)
df_txns['ts'] = pd.to_datetime(df_txns['ts'])

for cid, tid, cust in [('HHG-002', 3478782, 'C11891'), ('HHG-006', 3476682, 'C07297'), ('HHG-010', 3506725, 'C10434'), ('HHG-014', 3478561, 'C13487'), ('HHG-015', 3464869, 'C03042')]:
    c = df_txns[df_txns['customer_id'] == cust].sort_values('ts')
    fl_ts = c[c['TransactionID'] == tid].iloc[0]['ts']
    w = c[(c['ts'] >= fl_ts - pd.Timedelta(hours=48)) & (c['ts'] <= fl_ts + pd.Timedelta(hours=48))]
    print(f"\n=== {cid} ({cust}) ===")
    for _, t in w.iterrows():
        t_id = int(t['TransactionID'])
        fl = " <-- FLAGGED" if t_id == tid else ""
        print(f"  Txn {t_id} | {t['ts']} | ${t['TransactionAmt']:.2f} | {t['channel']} | Prod: {t['ProductCD']} | Reg: {t['addr1']} | Risk: {t['risk_score']}{fl}")
