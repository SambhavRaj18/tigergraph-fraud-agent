# TigerGraph Data Loading Guide

This guide details the step-by-step process for creating the schema, creating the loading job, and loading prepared graph data into TigerGraph for the **FraudInvestigation** graph.

---

## 1. Prerequisites & Environment Setup

Ensure your TigerGraph instance (Savanna or Community Edition) is running and accessible. Configure your credentials in `.env` or set environment variables:

```bash
# Verify GSQL CLI connectivity
gsql version
```

Make sure the prepared CSV files exist under `graph/loading/data_prepared/`. (If not already generated, run `python graph/loading/preprocess.py`).

---

## 2. Exact Order of Execution

### Step 1: Create Graph Schema
Execute `schema.gsql` to define all vertex types, edge types, reverse edges, and the `FraudInvestigation` graph:

```bash
gsql graph/schema/schema.gsql
```

*Verification output*: `The graph FraudInvestigation is created.`

---

### Step 2: Define and Install Loading Job
Execute `loading_jobs.gsql` to register the loading job on the graph:

```bash
gsql -g FraudInvestigation graph/loading/loading_jobs.gsql
```

*Verification output*: `Successfully created loading jobs: [load_fraud_data].`

---

### Step 3: Run the Loading Job
Run the loading job, passing the absolute path to `data_prepared`:

```bash
# On Linux / macOS / TigerGraph Server:
gsql -g FraudInvestigation 'RUN LOADING JOB load_fraud_data USING data_dir="/absolute/path/to/graph/loading/data_prepared"'

# On Windows (adjust path as appropriate):
gsql -g FraudInvestigation 'RUN LOADING JOB load_fraud_data USING data_dir="d:/HHHGOA/tigergraph-fraud-agent/graph/loading/data_prepared"'
```

Alternatively, using **pyTigerGraph** in Python:

```python
import os
from dotenv import load_dotenv
import pyTigerGraph as tg

load_dotenv()

conn = tg.TigerGraphConnection(
    host=os.getenv("TG_HOST", "http://localhost"),
    graphname="FraudInvestigation",
    username=os.getenv("TG_USERNAME", "tigergraph"),
    password=os.getenv("TG_PASSWORD", "tigergraph"),
    secret=os.getenv("TG_SECRET", "")
)
conn.getToken()

data_dir = os.path.abspath("graph/loading/data_prepared").replace("\\", "/")
res = conn.runLoadingJobWithFile(
    filePath=data_dir,
    fileTag="data_dir",
    jobName="load_fraud_data"
)
print("Loading result:", res)
```

---

## 3. Expected Vertex and Edge Counts

| Entity Type | Entity Name | Expected Count | Source Reference |
| :--- | :--- | :--- | :--- |
| **Vertex** | `Customer` | 13,553 | `vertices_customer.csv` |
| **Vertex** | `Card` | 1,917 | `vertices_card.csv` |
| **Vertex** | `Transaction` | 590,742 | `vertices_transaction.csv` |
| **Vertex** | `DeviceProfile` | 9,705 | `vertices_device_profile.csv` |
| **Vertex** | `EmailDomain` | 60 | `vertices_email_domain.csv` |
| **Vertex** | `BillingRegion` | 332 | `vertices_billing_region.csv` |
| **Vertex** | `ClosedCase` | 5,565 | `vertices_closed_case.csv` |
| **Edge** | `OWNS` / `OWNED_BY` | 1,917 | `edges_owns.csv` |
| **Edge** | `MADE` / `TRANSACTION_OF` | 14,975 | `edges_made.csv` |
| **Edge** | `FROM_DEVICE` / `DEVICE_OF` | 140,784 | `edges_from_device.csv` |
| **Edge** | `PURCHASER_EMAIL` / `EMAIL_OF` | 496,262 | `edges_purchaser_email.csv` |
| **Edge** | `RECIPIENT_EMAIL` / `RECIPIENT_OF` | ~174,000 | `vertices_transaction.csv` (r_email_domain) |
| **Edge** | `BILLED_IN` / `REGION_OF` | 525,003 | `edges_billed_in.csv` |
| **Edge** | `PERFORMED` / `PERFORMED_BY` | 590,742 | `vertices_transaction.csv` (customer_id) |
| **Edge** | `INVOLVES` | 14,955 | `edges_involves.csv` |
| **Edge** | `ON_CARD` | 5,565 | `edges_on_card.csv` |
| **Edge** | `CONNECTED_TO` | 92 | `edges_connected_to.csv` |

---

## 4. Post-Loading Validation Queries

Run the following GSQL queries / REST endpoints to verify graph completeness:

### 1. Vertex & Edge Count Verification
```gsql
USE GRAPH FraudInvestigation

INTERPRET QUERY () FOR GRAPH FraudInvestigation {
    PRINT Customer.size() AS Total_Customers;
    PRINT Card.size() AS Total_Cards;
    PRINT Transaction.size() AS Total_Transactions;
    PRINT DeviceProfile.size() AS Total_DeviceProfiles;
    PRINT EmailDomain.size() AS Total_EmailDomains;
    PRINT BillingRegion.size() AS Total_BillingRegions;
    PRINT ClosedCase.size() AS Total_ClosedCases;
}
```

### 2. Verify Case Pack Flagged Transactions Exist
```gsql
USE GRAPH FraudInvestigation

INTERPRET QUERY () FOR GRAPH FraudInvestigation {
    SetAccum<STRING> @@case_pack_txns = ("3514030", "3478782", "3530164", "3583227", "3523199", 
                                         "3476682", "3514948", "3558054", "3581141", "3506725", 
                                         "3583368", "3553342", "3526826", "3478561", "3464869", 
                                         "3534820", "3450629", "3491361", "3503878", "3509359");
    
    T = SELECT s FROM Transaction:s WHERE s.transaction_id IN @@case_pack_txns;
    PRINT T.size() AS Found_CasePack_Txns; // Must return 20
}
```

### 3. Verify Shared Device Reverse Traversal (Ring Detection)
```gsql
USE GRAPH FraudInvestigation

INTERPRET QUERY (STRING dev_id="SAMSUNG SM-G935F Build/NRD90M | Android 7.0 | chrome 62.0 for android | 2220x1080") FOR GRAPH FraudInvestigation {
    Seed = { DeviceProfile.* };
    TargetDev = SELECT s FROM Seed:s WHERE s.device_id == dev_id;
    Txns = SELECT t FROM TargetDev:s -(DEVICE_OF)-> Transaction:t;
    Customers = SELECT c FROM Txns:t -(PERFORMED_BY)-> Customer:c;
    PRINT TargetDev, Txns.size() AS Linked_Txns, Customers.size() AS Linked_Customers;
}
```

