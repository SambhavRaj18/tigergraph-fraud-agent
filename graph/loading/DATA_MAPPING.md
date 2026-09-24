# Data Mapping Specification for TigerGraph Fraud Investigation

This document defines the exact mapping between the raw dataset files (`data/raw/`) and the TigerGraph schema (`graph/schema/schema.gsql`).

---

## 1. Source Files Overview

| File | Row Count | Primary Key | Description |
| :--- | :--- | :--- | :--- |
| `transactions.csv` | 590,742 | `TransactionID` | Card transactions over 6 months with risk scores, amounts, timestamps, and anonymized features. |
| `identity.csv` | 144,432 | `TransactionID` | Device and network connection attributes for online transactions (`ProductCD != 'W'`). |
| `closed_cases_history.csv` | 5,565 | `case_id` | Labeled historical investigations (July–Oct 2016) with outcomes, patterns, and involved transaction IDs. |
| `case_pack.csv` | 20 | `case_id` | Benchmark evaluation cases (Nov–Dec 2016) with triggers and flagged transaction IDs. |

---

## 2. Vertex Mappings

### 2.1 Vertex: `Customer`
- **Target Schema**: `Customer(PRIMARY_ID customer_id STRING, customer_id STRING)`
- **Status**: **CONFIRMED**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `transactions.csv` | `customer_id` | `PRIMARY_ID` / `customer_id` | Direct string (e.g., `C12382`). Extract distinct values across all transactions. | **CONFIRMED** |
| `closed_cases_history.csv` | `customer_id` | `PRIMARY_ID` / `customer_id` | Ensure all case customers exist in Customer vertex set. | **CONFIRMED** |
| `case_pack.csv` | `customer_id` | `PRIMARY_ID` / `customer_id` | Ensure all case pack customers exist in Customer vertex set. | **CONFIRMED** |

---

### 2.2 Vertex: `Card`
- **Target Schema**: `Card(PRIMARY_ID card_id STRING, customer_id STRING, card_type STRING)`
- **Status**: **PARTIALLY UNRESOLVED (General Transactions)** / **CONFIRMED (Cases & Case Pack)**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `closed_cases_history.csv` | `card_id` | `PRIMARY_ID` / `card_id` | Direct string (e.g., `C00259-K1`). | **CONFIRMED** |
| `closed_cases_history.csv` | `customer_id` | `customer_id` | Direct string (e.g., `C00259`). | **CONFIRMED** |
| `case_pack.csv` | `card_id` | `PRIMARY_ID` / `card_id` | Direct string (e.g., `C12382-K1`). | **CONFIRMED** |
| `case_pack.csv` | `customer_id` | `customer_id` | Direct string (e.g., `C12382`). | **CONFIRMED** |
| `transactions.csv` | `card4`, `card6` | `card_type` | Combined network and type string (e.g., `visa debit`, `mastercard credit`). | **CONFIRMED** |
| `transactions.csv` | `customer_id`, `card1`..`card6` | `card_id` | **UNRESOLVED for arbitrary transactions**: `transactions.csv` lacks an explicit `card_id` column (`-K1`, `-K2`). Chronological ranking does not reliably reconstruct historical card indices. Transactions in closed cases and case pack are mapped explicitly; remaining transactions use known customer cards or an unassigned/default card placeholder. | **UNRESOLVED** |

---

### 2.3 Vertex: `Transaction`
- **Target Schema**: `Transaction(PRIMARY_ID transaction_id STRING, transaction_id STRING, customer_id STRING, card_id STRING, transaction_amt FLOAT, transaction_dt UINT, ts DATETIME, product_cd STRING, channel STRING, risk_score FLOAT, addr1 STRING, addr2 STRING, p_email_domain STRING, r_email_domain STRING)`
- **Status**: **CONFIRMED** (with card_id assigned where known)

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `transactions.csv` | `TransactionID` | `PRIMARY_ID` / `transaction_id` | Convert integer to string (e.g., `"3000001"`). | **CONFIRMED** |
| `transactions.csv` | `customer_id` | `customer_id` | Direct string (e.g., `"C06075"`). | **CONFIRMED** |
| `closed_cases_history.csv` / `case_pack.csv` | `card_id` | `card_id` | Populated for transactions mapped via closed cases or case pack; empty string `""` if unmapped. | **CONFIRMED (Partial)** |
| `transactions.csv` | `TransactionAmt` | `transaction_amt` | Float in USD (e.g., `77.07`). | **CONFIRMED** |
| `transactions.csv` | `TransactionDT` | `transaction_dt` | Unsigned Integer (seconds offset). | **CONFIRMED** |
| `transactions.csv` | `ts` | `ts` | String to DATETIME format (`YYYY-MM-DD HH:MM:SS`). | **CONFIRMED** |
| `transactions.csv` | `ProductCD` | `product_cd` | Direct string (`W`, `C`, `H`, `R`, `S`). | **CONFIRMED** |
| `transactions.csv` | `channel` | `channel` | Direct string (`in_person`, `online`). | **CONFIRMED** |
| `transactions.csv` | `risk_score` | `risk_score` | Float 0.0–1.0. Nulls preserved as -1.0 or empty. | **CONFIRMED** |
| `transactions.csv` | `addr1` | `addr1` | Cleaned integer string without trailing decimal (e.g., `444.0` -> `"444"`). Null -> `""`. | **CONFIRMED** |
| `transactions.csv` | `addr2` | `addr2` | Cleaned integer string (e.g., `87.0` -> `"87"`). Null -> `""`. | **CONFIRMED** |
| `transactions.csv` | `P_emaildomain` | `p_email_domain` | Lowercase string (e.g., `"gmail.com"`). Null -> `""`. | **CONFIRMED** |
| `transactions.csv` | `R_emaildomain` | `r_email_domain` | Lowercase string (e.g., `"yahoo.com"`). Null -> `""`. | **CONFIRMED** |

---

### 2.4 Vertex: `DeviceProfile`
- **Target Schema**: `DeviceProfile(PRIMARY_ID device_id STRING, device_info STRING, device_type STRING, os STRING, browser STRING, screen STRING, match_status STRING, is_new STRING, is_proxy STRING)`
- **Status**: **CONFIRMED**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `identity.csv` | `DeviceInfo`, `id_30`, `id_31`, `id_33` | `PRIMARY_ID` / `device_id` | Deterministic string profile: `"{DeviceInfo} \| {id_30} \| {id_31} \| {id_33}"` (trimmed, empty components omitted). Enables graph clustering across shared devices. | **CONFIRMED** |
| `identity.csv` | `DeviceInfo` | `device_info` | Direct string (e.g., `SAMSUNG SM-G935F Build/NRD90M`). | **CONFIRMED** |
| `identity.csv` | `DeviceType` | `device_type` | Direct string (`mobile`, `desktop`). | **CONFIRMED** |
| `identity.csv` | `id_30` | `os` | Operating system string (e.g., `Android 7.0`, `iOS 11.1.2`, `Windows 10`). | **CONFIRMED** |
| `identity.csv` | `id_31` | `browser` | Browser string (e.g., `chrome 62.0`, `samsung browser 6.2`). | **CONFIRMED** |
| `identity.csv` | `id_33` | `screen` | Screen resolution string (e.g., `2220x1080`, `1920x1080`). | **CONFIRMED** |
| `identity.csv` | `id_34` | `match_status` | Match status flag (e.g., `match_status:2`). | **CONFIRMED** |
| `identity.csv` | `id_15` | `is_new` | Device familiarity flag (`New`, `Found`). | **CONFIRMED** |
| `identity.csv` | `id_23` | `is_proxy` | Proxy status (e.g., `IP_PROXY:TRANSPARENT`, `IP_PROXY:ANONYMOUS`, `IP_PROXY:HIDDEN`). | **CONFIRMED** |

---

### 2.5 Vertex: `EmailDomain`
- **Target Schema**: `EmailDomain(PRIMARY_ID domain STRING)`
- **Status**: **CONFIRMED**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `transactions.csv` | `P_emaildomain`, `R_emaildomain` | `PRIMARY_ID` / `domain` | Lowercase trimmed domain string (e.g., `gmail.com`, `hotmail.com`). Distinct non-null values. | **CONFIRMED** |

---

### 2.6 Vertex: `BillingRegion`
- **Target Schema**: `BillingRegion(PRIMARY_ID region_id STRING, country_code STRING)`
- **Status**: **CONFIRMED**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `transactions.csv` | `addr1` | `PRIMARY_ID` / `region_id` | String representation without trailing `.0` (e.g., `"444"`). Distinct non-null values. | **CONFIRMED** |
| `transactions.csv` | `addr2` | `country_code` | Associated country code string (e.g., `"87"`). | **CONFIRMED** |

---

### 2.7 Vertex: `ClosedCase`
- **Target Schema**: `ClosedCase(PRIMARY_ID case_id STRING, customer_id STRING, card_id STRING, opened_at DATETIME, closed_at DATETIME, outcome STRING, pattern STRING, first_fraud_txn_id STRING, n_txns UINT, exposure_usd FLOAT, actions_taken STRING, report_filed BOOL, analyst_notes STRING)`
- **Status**: **CONFIRMED**

| Source File | Source Column | Target Attribute | Transformation | Mapping Status |
| :--- | :--- | :--- | :--- | :--- |
| `closed_cases_history.csv` | `case_id` | `PRIMARY_ID` / `case_id` | Direct string (e.g., `"CC-0001"`). | **CONFIRMED** |
| `closed_cases_history.csv` | `customer_id` | `customer_id` | Direct string (e.g., `"C00259"`). | **CONFIRMED** |
| `closed_cases_history.csv` | `card_id` | `card_id` | Direct string (e.g., `"C00259-K1"`). | **CONFIRMED** |
| `closed_cases_history.csv` | `opened_at` | `opened_at` | String to DATETIME (`YYYY-MM-DD HH:MM:SS`). | **CONFIRMED** |
| `closed_cases_history.csv` | `closed_at` | `closed_at` | String to DATETIME (`YYYY-MM-DD HH:MM:SS`). | **CONFIRMED** |
| `closed_cases_history.csv` | `outcome` | `outcome` | Direct string (`confirmed_fraud`, `cleared`). | **CONFIRMED** |
| `closed_cases_history.csv` | `pattern` | `pattern` | Direct string (`card_testing`, `card_not_present_fraud`, etc.). | **CONFIRMED** |
| `closed_cases_history.csv` | `first_fraud_txn_id` | `first_fraud_txn_id` | Integer string (e.g., `"3000120"`). Null -> `""`. | **CONFIRMED** |
| `closed_cases_history.csv` | `n_txns` | `n_txns` | Unsigned Integer (count of transactions). | **CONFIRMED** |
| `closed_cases_history.csv` | `exposure_usd` | `exposure_usd` | Float USD amount. | **CONFIRMED** |
| `closed_cases_history.csv` | `actions_taken` | `actions_taken` | Direct string (pipe-separated actions). | **CONFIRMED** |
| `closed_cases_history.csv` | `report_filed` | `report_filed` | Convert `"Yes"` -> `true`, `"No"` -> `false`. | **CONFIRMED** |
| `closed_cases_history.csv` | `analyst_notes` | `analyst_notes` | Narrative text. | **CONFIRMED** |

---

## 3. Edge Mappings

| Edge Name | Source Vertex (FROM) | Target Vertex (TO) | Edge Attributes | Source Data & Logic | Mapping Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `OWNS` | `Customer` | `Card` | None | Extracted from `closed_cases_history.csv` and `case_pack.csv` (`customer_id` -> `card_id`). | **CONFIRMED** |
| `MADE` | `Card` | `Transaction` | None | Linked for all transactions where `card_id` is known from closed cases or case pack. | **CONFIRMED (Partial)** |
| `FROM_DEVICE` | `Transaction` | `DeviceProfile` | None | Join `transactions.csv` on `TransactionID` with `identity.csv` (`channel == 'online'`). | **CONFIRMED** |
| `PURCHASER_EMAIL`| `Transaction` | `EmailDomain` | None | From `transactions.csv` where `P_emaildomain` is non-null. | **CONFIRMED** |
| `BILLED_IN` | `Transaction` | `BillingRegion` | None | From `transactions.csv` where `addr1` is non-null. | **CONFIRMED** |
| `NEXT` | `Transaction` | `Transaction` | `ts_diff INT` | Chronological order of consecutive transactions for the same customer/card: `ts_diff = ts[i] - ts[i-1]` in seconds. | **CONFIRMED** |
| `INVOLVES` | `ClosedCase` | `Transaction` | None | Split pipe-separated `txn_ids` from `closed_cases_history.csv`. | **CONFIRMED** |
| `ON_CARD` | `ClosedCase` | `Card` | None | From `closed_cases_history.csv` (`case_id` -> `card_id`). | **CONFIRMED** |
| `CONNECTED_TO` | `ClosedCase` | `Card` | None | Split pipe-separated `connected_card_ids` in `closed_cases_history.csv` (when not null). | **CONFIRMED** |

---

## 4. Key Findings & Schema Alignment Notes

1. **Card ID Unresolved for General Transactions**:
   - `transactions.csv` contains `customer_id` and raw columns `card1`..`card6`, but not synthetic card IDs like `C12382-K1`.
   - Chronological sorting of `(card1..card6)` tuples does **not** consistently reconstruct the ground truth `K1`/`K2` indices (`mismatch rate ~67%`).
   - Therefore, `Card` vertices and `MADE` edges are explicitly confirmed for all closed cases and case pack transactions.
2. **DeviceProfile Identification**:
   - Distinct device profiles are constructed from composite strings of `(DeviceInfo, id_30, id_31, id_33)`. This enables graph traversals across shared device profiles.
3. **Data Type Conversions**:
   - `report_filed` in `closed_cases_history.csv` (`"Yes"`/`"No"`) is transformed to boolean `true`/`false`.
   - `addr1` / `addr2` floating-point strings (e.g., `"444.0"`) are normalized to integer strings (`"444"`).

