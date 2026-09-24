import pandas as pd
df_txns = pd.read_csv('d:/HHHGOA/tigergraph-fraud-agent/data/raw/transactions.csv', low_memory=False)
df_txns['ts'] = pd.to_datetime(df_txns['ts'])

for cid, tid, cust in [('HHG-008', 3558054, 'C13171'), ('HHG-009', 3581141, 'C08299'), ('HHG-011', 3583368, 'C11923'), ('HHG-016', 3534820, 'C09988'), ('HHG-018', 3491361, 'C02354')]:
    c = df_txns[df_txns['customer_id'] == cust].sort_values('ts')
    fl_ts = c[c['TransactionID'] == tid].iloc[0]['ts']
    w = c[(c['ts'] >= fl_ts - pd.Timedelta(hours=24)) & (c['ts'] <= fl_ts + pd.Timedelta(hours=24))]
    print(f"\n=== {cid} ({cust}) ===")
    for _, t in w.iterrows():
        t_id = int(t['TransactionID'])
        fl = " <-- FLAGGED" if t_id == tid else ""
        print(f"  Txn {t_id} | {t['ts']} | ${t['TransactionAmt']:.2f} | {t['channel']} | Prod: {t['ProductCD']} | Reg: {t['addr1']} | Risk: {t['risk_score']}{fl}")
