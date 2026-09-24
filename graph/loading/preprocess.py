"""
Preprocessing and graph-ready data preparation script for TigerGraph Fraud Investigation Agent.
Streams large CSV files in chunks to avoid high memory consumption.
"""

import os
import csv
import logging
from typing import Dict, Set, Tuple, List, Optional
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DataPreprocessor")


def clean_int_str(val) -> str:
    """Format float or string to integer string (e.g. 444.0 -> '444')."""
    if pd.isna(val) or val is None or val == "" or str(val).lower() == "nan":
        return ""
    try:
        return str(int(float(val)))
    except (ValueError, TypeError):
        return str(val).strip()


def build_device_id(device_info: str, os_name: str, browser: str, screen: str) -> str:
    """Construct deterministic DeviceProfile ID from identity features."""
    parts = []
    for p in [device_info, os_name, browser, screen]:
        p_clean = str(p).strip() if pd.notna(p) and str(p).lower() != "nan" else ""
        parts.append(p_clean)
    if not any(parts):
        return ""
    return " | ".join(parts)


def run_preprocessing(
    raw_dir: str = "data/raw",
    output_dir: str = "graph/loading/data_prepared",
    chunk_size: int = 50000
):
    """
    Reads raw CSVs, normalizes fields, and produces TigerGraph-ready vertex and edge CSVs.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Starting graph data preparation...")
    logger.info(f"Raw data directory: {raw_dir}")
    logger.info(f"Output directory: {output_dir}")

    # 1. Load Closed Cases History & Case Pack
    cc_path = os.path.join(raw_dir, "closed_cases_history.csv")
    cp_path = os.path.join(raw_dir, "case_pack.csv")

    df_cc = pd.read_csv(cc_path)
    df_cp = pd.read_csv(cp_path)

    logger.info(f"Loaded {len(df_cc)} closed cases and {len(df_cp)} case pack records.")

    # Build known TransactionID -> card_id map
    txn_to_card: Dict[str, str] = {}
    known_cards: Set[Tuple[str, str, str]] = set()  # (card_id, customer_id, card_type)
    customer_set: Set[str] = set()

    for _, r in df_cc.iterrows():
        cid = str(r["customer_id"]).strip()
        card_id = str(r["card_id"]).strip()
        customer_set.add(cid)
        known_cards.add((card_id, cid, ""))
        for t in str(r["txn_ids"]).split("|"):
            t_clean = clean_int_str(t)
            if t_clean:
                txn_to_card[t_clean] = card_id
        if pd.notna(r.get("connected_card_ids")):
            for conn_card in str(r["connected_card_ids"]).split("|"):
                conn_clean = conn_card.strip()
                if conn_clean:
                    conn_cid = conn_clean.split("-")[0] if "-" in conn_clean else ""
                    if conn_cid:
                        customer_set.add(conn_cid)
                    known_cards.add((conn_clean, conn_cid, ""))

    for _, r in df_cp.iterrows():
        cid = str(r["customer_id"]).strip()
        card_id = str(r["card_id"]).strip()
        t_clean = clean_int_str(r["flagged_txn_id"])
        customer_set.add(cid)
        known_cards.add((card_id, cid, ""))
        if t_clean:
            txn_to_card[t_clean] = card_id

    logger.info(f"Collected {len(txn_to_card)} explicit Transaction->Card mappings from cases.")

    # 2. Process Identity Records into DeviceProfiles
    id_path = os.path.join(raw_dir, "identity.csv")
    df_id = pd.read_csv(id_path)
    logger.info(f"Loaded {len(df_id)} identity records.")

    device_profiles: Dict[str, Dict[str, str]] = {}
    txn_to_device: Dict[str, str] = {}

    for _, r in df_id.iterrows():
        tid = clean_int_str(r["TransactionID"])
        d_info = str(r["DeviceInfo"]) if pd.notna(r["DeviceInfo"]) else ""
        d_type = str(r["DeviceType"]) if pd.notna(r["DeviceType"]) else ""
        os_val = str(r["id_30"]) if pd.notna(r["id_30"]) else ""
        browser = str(r["id_31"]) if pd.notna(r["id_31"]) else ""
        screen = str(r["id_33"]) if pd.notna(r["id_33"]) else ""
        match_st = str(r["id_34"]) if pd.notna(r["id_34"]) else ""
        is_new = str(r["id_15"]) if pd.notna(r["id_15"]) else ""
        is_proxy = str(r["id_23"]) if pd.notna(r["id_23"]) else ""

        dev_id = build_device_id(d_info, os_val, browser, screen)
        if dev_id:
            txn_to_device[tid] = dev_id
            if dev_id not in device_profiles:
                device_profiles[dev_id] = {
                    "device_id": dev_id,
                    "device_info": d_info,
                    "device_type": d_type,
                    "os": os_val,
                    "browser": browser,
                    "screen": screen,
                    "match_status": match_st,
                    "is_new": is_new,
                    "is_proxy": is_proxy,
                }

    logger.info(f"Identified {len(device_profiles)} unique DeviceProfile vertices.")

    # 3. Stream Transactions & Generate Vertex / Edge Tables
    tx_path = os.path.join(raw_dir, "transactions.csv")
    
    email_domains: Set[str] = set()
    billing_regions: Dict[str, str] = {}  # region_id -> country_code
    
    # Track sequence data for NEXT edge: list of (customer_id, TransactionDT, TransactionID)
    seq_records: List[Tuple[str, int, str]] = []

    # File writers
    f_tx = open(os.path.join(output_dir, "vertices_transaction.csv"), "w", newline="", encoding="utf-8")
    tx_writer = csv.writer(f_tx)
    tx_writer.writerow([
        "transaction_id", "customer_id", "card_id", "transaction_amt",
        "transaction_dt", "ts", "product_cd", "channel", "risk_score",
        "addr1", "addr2", "p_email_domain", "r_email_domain"
    ])

    f_from_dev = open(os.path.join(output_dir, "edges_from_device.csv"), "w", newline="", encoding="utf-8")
    from_dev_writer = csv.writer(f_from_dev)
    from_dev_writer.writerow(["transaction_id", "device_id"])

    f_pemail = open(os.path.join(output_dir, "edges_purchaser_email.csv"), "w", newline="", encoding="utf-8")
    pemail_writer = csv.writer(f_pemail)
    pemail_writer.writerow(["transaction_id", "domain"])

    f_billed = open(os.path.join(output_dir, "edges_billed_in.csv"), "w", newline="", encoding="utf-8")
    billed_writer = csv.writer(f_billed)
    billed_writer.writerow(["transaction_id", "region_id"])

    f_made = open(os.path.join(output_dir, "edges_made.csv"), "w", newline="", encoding="utf-8")
    made_writer = csv.writer(f_made)
    made_writer.writerow(["card_id", "transaction_id"])

    total_tx = 0
    matched_cards_tx = 0
    matched_device_tx = 0

    tx_cols = [
        "TransactionID", "customer_id", "TransactionAmt", "TransactionDT", "ts",
        "ProductCD", "channel", "risk_score", "addr1", "addr2",
        "P_emaildomain", "R_emaildomain", "card4", "card6"
    ]

    for chunk in pd.read_csv(tx_path, usecols=tx_cols, chunksize=chunk_size):
        for _, row in chunk.iterrows():
            total_tx += 1
            tid = clean_int_str(row["TransactionID"])
            cid = str(row["customer_id"]).strip() if pd.notna(row["customer_id"]) else ""
            if cid:
                customer_set.add(cid)

            card_id = txn_to_card.get(tid, "")
            if card_id:
                matched_cards_tx += 1
                made_writer.writerow([card_id, tid])
                c_type = f"{row.get('card4', '')} {row.get('card6', '')}".strip()
                known_cards.add((card_id, cid, c_type))

            amt = float(row["TransactionAmt"]) if pd.notna(row["TransactionAmt"]) else 0.0
            dt = int(row["TransactionDT"]) if pd.notna(row["TransactionDT"]) else 0
            ts_val = str(row["ts"]).strip() if pd.notna(row["ts"]) else ""
            p_cd = str(row["ProductCD"]).strip() if pd.notna(row["ProductCD"]) else ""
            chan = str(row["channel"]).strip() if pd.notna(row["channel"]) else ""
            r_score = float(row["risk_score"]) if pd.notna(row["risk_score"]) else -1.0
            a1 = clean_int_str(row["addr1"])
            a2 = clean_int_str(row["addr2"])
            p_email = str(row["P_emaildomain"]).strip().lower() if pd.notna(row["P_emaildomain"]) else ""
            r_email = str(row["R_emaildomain"]).strip().lower() if pd.notna(row["R_emaildomain"]) else ""

            if p_email:
                email_domains.add(p_email)
                pemail_writer.writerow([tid, p_email])
            if r_email:
                email_domains.add(r_email)

            if a1:
                billing_regions[a1] = a2
                billed_writer.writerow([tid, a1])

            if tid in txn_to_device:
                matched_device_tx += 1
                from_dev_writer.writerow([tid, txn_to_device[tid]])

            seq_records.append((cid, dt, tid))

            tx_writer.writerow([
                tid, cid, card_id, amt, dt, ts_val, p_cd, chan, r_score,
                a1, a2, p_email, r_email
            ])

    f_tx.close()
    f_from_dev.close()
    f_pemail.close()
    f_billed.close()
    f_made.close()

    logger.info(f"Processed {total_tx:,} transactions.")
    logger.info(f"Transactions mapped to known cards: {matched_cards_tx:,}")
    logger.info(f"Transactions mapped to devices: {matched_device_tx:,}")

    # 4. Generate NEXT Edge Table
    logger.info("Computing chronological NEXT edges per customer...")
    df_seq = pd.DataFrame(seq_records, columns=["customer_id", "dt", "tid"])
    df_seq = df_seq.sort_values(by=["customer_id", "dt", "tid"])
    
    df_seq["next_tid"] = df_seq.groupby("customer_id")["tid"].shift(-1)
    df_seq["next_dt"] = df_seq.groupby("customer_id")["dt"].shift(-1)
    
    df_next = df_seq.dropna(subset=["next_tid", "next_dt"]).copy()
    df_next["ts_diff"] = (df_next["next_dt"] - df_next["dt"]).astype(int)
    
    next_path = os.path.join(output_dir, "edges_next.csv")
    df_next[["tid", "next_tid", "ts_diff"]].to_csv(
        next_path,
        index=False,
        header=["from_txn", "to_txn", "ts_diff"],
        encoding="utf-8"
    )
    logger.info(f"Wrote {len(df_next):,} NEXT edges to edges_next.csv.")

    # 5. Write Customer Vertices
    with open(os.path.join(output_dir, "vertices_customer.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id"])
        for c in sorted(customer_set):
            w.writerow([c])
    logger.info(f"Wrote {len(customer_set):,} Customer vertices.")

    # 6. Write Card Vertices & OWNS Edges
    with open(os.path.join(output_dir, "vertices_card.csv"), "w", newline="", encoding="utf-8") as f_card, \
         open(os.path.join(output_dir, "edges_owns.csv"), "w", newline="", encoding="utf-8") as f_owns:
        w_card = csv.writer(f_card)
        w_owns = csv.writer(f_owns)
        w_card.writerow(["card_id", "customer_id", "card_type"])
        w_owns.writerow(["customer_id", "card_id"])

        card_dict: Dict[str, Tuple[str, str]] = {}
        for card_id, cid, c_type in known_cards:
            if card_id not in card_dict or (not card_dict[card_id][1] and c_type):
                card_dict[card_id] = (cid, c_type)

        for card_id, (cid, c_type) in sorted(card_dict.items()):
            w_card.writerow([card_id, cid, c_type])
            w_owns.writerow([cid, card_id])
    logger.info(f"Wrote {len(card_dict):,} Card vertices and OWNS edges.")

    # 7. Write DeviceProfile Vertices
    with open(os.path.join(output_dir, "vertices_device_profile.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "device_id", "device_info", "device_type", "os", "browser",
            "screen", "match_status", "is_new", "is_proxy"
        ])
        for dev in device_profiles.values():
            w.writerow([
                dev["device_id"], dev["device_info"], dev["device_type"],
                dev["os"], dev["browser"], dev["screen"], dev["match_status"],
                dev["is_new"], dev["is_proxy"]
            ])
    logger.info(f"Wrote {len(device_profiles):,} DeviceProfile vertices.")

    # 8. Write EmailDomain Vertices
    with open(os.path.join(output_dir, "vertices_email_domain.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain"])
        for d in sorted(email_domains):
            w.writerow([d])
    logger.info(f"Wrote {len(email_domains):,} EmailDomain vertices.")

    # 9. Write BillingRegion Vertices
    with open(os.path.join(output_dir, "vertices_billing_region.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["region_id", "country_code"])
        for r_id, c_code in sorted(billing_regions.items()):
            w.writerow([r_id, c_code])
    logger.info(f"Wrote {len(billing_regions):,} BillingRegion vertices.")

    # 10. Write ClosedCase Vertices & Related Edges (Explicit status: closed_fraud / closed_legitimate)
    with open(os.path.join(output_dir, "vertices_closed_case.csv"), "w", newline="", encoding="utf-8") as f_cc_out, \
         open(os.path.join(output_dir, "edges_involves.csv"), "w", newline="", encoding="utf-8") as f_inv, \
         open(os.path.join(output_dir, "edges_on_card.csv"), "w", newline="", encoding="utf-8") as f_oncard, \
         open(os.path.join(output_dir, "edges_connected_to.csv"), "w", newline="", encoding="utf-8") as f_conn:
        
        w_cc = csv.writer(f_cc_out)
        w_inv = csv.writer(f_inv)
        w_oncard = csv.writer(f_oncard)
        w_conn = csv.writer(f_conn)

        w_cc.writerow([
            "case_id", "customer_id", "card_id", "opened_at", "closed_at",
            "status", "outcome", "pattern", "first_fraud_txn_id", "n_txns",
            "exposure_usd", "actions_taken", "report_filed", "analyst_notes"
        ])
        w_inv.writerow(["case_id", "transaction_id"])
        w_oncard.writerow(["case_id", "card_id"])
        w_conn.writerow(["case_id", "card_id"])

        for _, r in df_cc.iterrows():
            case_id = str(r["case_id"]).strip()
            cid = str(r["customer_id"]).strip()
            card_id = str(r["card_id"]).strip()
            opened_at = str(r["opened_at"]).strip()
            closed_at = str(r["closed_at"]).strip()
            outcome = str(r["outcome"]).strip()
            
            # Map status explicitly from outcome
            if outcome == "confirmed_fraud":
                status_val = "closed_fraud"
            elif outcome == "cleared":
                status_val = "closed_legitimate"
            else:
                status_val = outcome

            pattern = str(r["pattern"]).strip()
            first_fraud = clean_int_str(r["first_fraud_txn_id"])
            n_txns = int(r["n_txns"]) if pd.notna(r["n_txns"]) else 0
            exposure = float(r["exposure_usd"]) if pd.notna(r["exposure_usd"]) else 0.0
            actions = str(r["actions_taken"]).strip() if pd.notna(r["actions_taken"]) else ""
            rep_filed = True if str(r["report_filed"]).strip().lower() == "yes" else False
            notes = str(r["analyst_notes"]).strip() if pd.notna(r["analyst_notes"]) else ""

            w_cc.writerow([
                case_id, cid, card_id, opened_at, closed_at,
                status_val, outcome, pattern, first_fraud, n_txns, exposure,
                actions, rep_filed, notes
            ])

            w_oncard.writerow([case_id, card_id])

            for t in str(r["txn_ids"]).split("|"):
                t_clean = clean_int_str(t)
                if t_clean:
                    w_inv.writerow([case_id, t_clean])

            if pd.notna(r.get("connected_card_ids")):
                for conn_card in str(r["connected_card_ids"]).split("|"):
                    conn_clean = conn_card.strip()
                    if conn_clean:
                        w_conn.writerow([case_id, conn_clean])

    logger.info(f"Wrote {len(df_cc):,} ClosedCase vertices (with explicit status) and associated edges.")
    logger.info("Graph data preparation complete!")


if __name__ == "__main__":
    run_preprocessing()
