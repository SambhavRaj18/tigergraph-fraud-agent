import pandas as pd
df_txns = pd.read_csv('d:/HHHGOA/tigergraph-fraud-agent/data/raw/transactions.csv', low_memory=False)
df_txns['ts'] = pd.to_datetime(df_txns['ts'])
c17 = df_txns[df_txns['customer_id'] == 'C04570'].sort_values('ts')
nov = c17[c17['ts'].dt.month == 11]
for _, t in nov.iterrows():
    tid = int(t['TransactionID'])
    fl = ' <-- FLAGGED' if tid == 3450629 else ''
    print(f"Txn {tid} | {t['ts']} | ${t['TransactionAmt']:>7.2f} | {t['channel']} | {t['ProductCD']} | Reg: {t['addr1']}{fl}")

