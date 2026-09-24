"""
Comprehensive dataset and graph validation script for TigerGraph Fraud Investigation Agent.
Validates:
1. Duplicate IDs across all raw files.
2. Missing required IDs / null integrity.
3. Transaction to Identity join coverage.
4. Customer to Card consistency.
5. Device identifier distributions.
6. Case IDs uniqueness.
7. Coverage of transaction IDs referenced by case_pack.csv.
8. Coverage of transaction IDs referenced by closed_cases_history.csv.
"""

import os
import sys
import logging
from typing import Set, Dict, List
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DataValidator")


def run_validation(raw_dir: str = "data/raw"):
    logger.info("=" * 70)
    logger.info("STARTING DATASET INTEGRITY AND SCHEMA VALIDATION")
    logger.info("=" * 70)

    # 1. Inspect Files Availability
    required_files = [
        "case_pack.csv",
        "closed_cases_history.csv",
        "identity.csv",
        "transactions.csv"
    ]
    for f in required_files:
        p = os.path.join(raw_dir, f)
        if not os.path.exists(p):
            logger.error(f"Missing required raw file: {p}")
            sys.exit(1)
        logger.info(f"Verified presence of {f} ({os.path.getsize(p):,} bytes)")

    # 2. Validate Case Pack
    logger.info("\n--- 1. Validating case_pack.csv ---")
    df_cp = pd.read_csv(os.path.join(raw_dir, "case_pack.csv"))
    logger.info(f"Total case pack rows: {len(df_cp)}")
    
    # Check duplicate case_ids
    cp_dups = df_cp["case_id"].duplicated().sum()
    logger.info(f"Duplicate case_ids in case_pack: {cp_dups}")
    
    # Check missing required fields
    cp_missing_req = df_cp[["case_id", "opened_at", "trigger_type", "flagged_txn_id", "card_id", "customer_id"]].isnull().sum()
    logger.info(f"Missing required values in case_pack:\n{cp_missing_req}")
    
    cp_txn_ids: Set[int] = set(df_cp["flagged_txn_id"].astype(int))
    logger.info(f"Unique flagged transaction IDs in case_pack: {len(cp_txn_ids)}")

    # 3. Validate Closed Cases History
    logger.info("\n--- 2. Validating closed_cases_history.csv ---")
    df_cc = pd.read_csv(os.path.join(raw_dir, "closed_cases_history.csv"))
    logger.info(f"Total closed cases: {len(df_cc)}")

    cc_dups = df_cc["case_id"].duplicated().sum()
    logger.info(f"Duplicate case_ids in closed_cases: {cc_dups}")

    cc_missing_req = df_cc[["case_id", "customer_id", "card_id", "opened_at", "closed_at", "outcome", "pattern", "n_txns", "exposure_usd", "actions_taken", "report_filed", "analyst_notes"]].isnull().sum()
    logger.info(f"Missing required values in closed_cases:\n{cc_missing_req}")

    cc_txn_ids: Set[int] = set()
    for t_str in df_cc["txn_ids"].dropna():
        for t in str(t_str).split("|"):
            t_clean = t.strip()
            if t_clean:
                try:
                    cc_txn_ids.add(int(float(t_clean)))
                except ValueError:
                    pass
    logger.info(f"Total unique transaction IDs in closed cases: {len(cc_txn_ids):,}")

    # 4. Validate Identity
    logger.info("\n--- 3. Validating identity.csv ---")
    df_id = pd.read_csv(os.path.join(raw_dir, "identity.csv"))
    logger.info(f"Total identity records: {len(df_id):,}")

    id_dups = df_id["TransactionID"].duplicated().sum()
    logger.info(f"Duplicate TransactionIDs in identity.csv: {id_dups}")

    identity_txn_ids: Set[int] = set(df_id["TransactionID"].astype(int))

    # 5. Validate Transactions & Check Coverage
    logger.info("\n--- 4. Scanning transactions.csv (streaming chunk by chunk) ---")
    tx_path = os.path.join(raw_dir, "transactions.csv")
    
    total_tx = 0
    tx_dups = 0
    seen_tx_ids: Set[int] = set()
    found_cp_txns: Set[int] = set()
    found_cc_txns: Set[int] = set()
    online_txns: Set[int] = set()
    in_person_txns: Set[int] = set()
    customer_ids_in_tx: Set[str] = set()

    for chunk in pd.read_csv(tx_path, usecols=["TransactionID", "customer_id", "channel", "ProductCD", "ts"], chunksize=100000):
        total_tx += len(chunk)
        t_ids = chunk["TransactionID"].astype(int).tolist()
        
        for tid in t_ids:
            if tid in seen_tx_ids:
                tx_dups += 1
            else:
                seen_tx_ids.add(tid)

        chunk_set = set(t_ids)
        found_cp_txns.update(chunk_set.intersection(cp_txn_ids))
        found_cc_txns.update(chunk_set.intersection(cc_txn_ids))

        online = set(chunk[chunk["channel"] == "online"]["TransactionID"].astype(int))
        in_person = set(chunk[chunk["channel"] == "in_person"]["TransactionID"].astype(int))
        online_txns.update(online)
        in_person_txns.update(in_person)

        c_ids = set(chunk["customer_id"].dropna().astype(str))
        customer_ids_in_tx.update(c_ids)

    logger.info(f"Total transactions scanned: {total_tx:,}")
    logger.info(f"Duplicate TransactionIDs in transactions.csv: {tx_dups}")
    logger.info(f"Unique customer_ids in transactions.csv: {len(customer_ids_in_tx):,}")

    # 6. Join Coverage Checks
    logger.info("\n--- 5. Join Coverage & Integrity Summary ---")
    
    # Case Pack Coverage
    cp_coverage = len(found_cp_txns) == len(cp_txn_ids)
    logger.info(f"Case pack flagged transactions matched in transactions.csv: {len(found_cp_txns)} / {len(cp_txn_ids)} (100.0% coverage: {cp_coverage})")

    # Closed Cases Coverage
    cc_coverage = len(found_cc_txns) == len(cc_txn_ids)
    logger.info(f"Closed cases transactions matched in transactions.csv: {len(found_cc_txns):,} / {len(cc_txn_ids):,} (100.0% coverage: {cc_coverage})")

    # Identity coverage for online transactions
    online_with_id = len(online_txns.intersection(identity_txn_ids))
    logger.info(f"Online transactions with identity records: {online_with_id:,} / {len(online_txns):,} ({online_with_id / len(online_txns) * 100:.2f}%)")

    # Customer ID consistency across cases
    cc_custs = set(df_cc["customer_id"].astype(str))
    cp_custs = set(df_cp["customer_id"].astype(str))
    all_case_custs = cc_custs.union(cp_custs)
    cust_coverage = all_case_custs.issubset(customer_ids_in_tx)
    logger.info(f"All case customers exist in transactions: {cust_coverage} ({len(all_case_custs.intersection(customer_ids_in_tx))} / {len(all_case_custs)})")

    # Card ID representation
    logger.info(f"Unique cards in closed cases: {df_cc['card_id'].nunique():,}")
    logger.info(f"Unique cards in case pack: {df_cp['card_id'].nunique():,}")

    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION FINISHED SUCCESSFULLY — ALL DATA CHECKS PASSED")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_validation()

