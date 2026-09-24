# TigerGraph × Hacker House Goa — Autonomous Fraud Investigation Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TigerGraph Savanna](https://img.shields.io/badge/TigerGraph-Savanna%20Cloud-orange.svg)](https://savanna.tgcloud.io)
[![MCP Protocol](https://img.shields.io/badge/Protocol-MCP%20stdio-green.svg)](https://github.com/tigergraph/tigergraph-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Project Pitch:**  
> The **Autonomous Fraud Investigation Agent** is a policy-constrained agentic fraud investigation system that pairs **TigerGraph Savanna Cloud** with an **Agentic LLM Layer (via Model Context Protocol)** and an authoritative **Deterministic Policy Decision Engine**. Operating over 590k+ transactions and 5.5k+ historical cases, the agent traverses multi-hop graph subgraphs, evaluates behavioral baselines, detects multi-transaction burst episodes, enforces strict bank policy rules (R1–R10), and synthesizes policy-driven SAR narratives with explicit evidence provenance and simulated-evidence labeling.

---

## 📊 Benchmark at a Glance

| Benchmark Dimension | Measured Metric | Description / Verification |
| :--- | :---: | :--- |
| **Benchmark Cases Evaluated** | **20 / 20** | All 20 exam cases investigated and generated in `cases/*.json` |
| **Total Graph Transactions** | **590,742** | Native TigerGraph Savanna Cloud vertex storage |
| **Historical Closed Cases** | **5,565** | Historical training investigations (July–October) |
| **Graph Case-Memory Total** | **5,585** | 5,565 historical + 20 closed benchmark investigations written to graph |
| **Deliverable Validation Errors** | **0 Errors** | 6-stage schema, provenance, and policy referential integrity audit |
| **Agent Suite Unit Tests** | **10 / 10 (OK)** | Full test coverage over MCP tools, episode grouping, and policies |

---

## 🧠 Why This Is Agentic

Rather than running a monolithic script or relying on an unconstrained LLM, the investigation executes as a **policy-constrained agentic, stateful loop**:

```
Case Trigger (risk score, customer dispute, analyst request)
   ↓
Agentic LLM Layer (reasons over investigation state)
   ↓
Tool Selection (selects next best tool via MCP stdio transport)
   ↓
TigerGraph Evidence Retrieval (executes multi-hop GSQL query for transaction neighborhood)
   ↓
Evidence Analysis (computes customer baseline statistics, Z-scores, and burst episodes)
   ↓
Historical Case Retrieval (retrieves precedent cases from 5,565 closed cases in graph)
   ↓
Policy Retrieval & Evaluation (evaluates deterministic rules R1–R10 against evidence)
   ↓
Need More Evidence?
   ├── YES → Queue out-of-band validation → re-evaluate
   └── NO  → Stop Decision (signals termination with stop rationale)
                    ↓
             Policy Decision Engine (authoritative actions + approval routes)
                    ↓
             FinCEN SAR Generation (when required by policy thresholds)
                    ↓
             Graph Case-Memory Write (persists ClosedCase vertex & incident edges)
```

---

## ⚖️ System Responsibilities Matrix

Clear separation of concerns guarantees explainability, compliance, and zero hallucinated policy actions:

| Component | Core Responsibility |
| :--- | :--- |
| **TigerGraph Savanna Cloud** | **Graph Evidence & Retrieval**: Stores 590k+ transactions, 13k+ customers, 5.5k+ cases, and executes multi-hop neighborhood queries and `NEXT` temporal edge traversals. |
| **Model Context Protocol (MCP)** | **Standardized Tool Interface**: Exposes graph investigation, evidence analysis, case retrieval, and policy tools over standard `stdio` transport. |
| **Agentic LLM Layer** | **Reasoning & Tool Selection**: Dynamically selects tools based on case context, evaluates hypotheses, and synthesizes executive summaries and FinCEN SAR narratives. |
| **Policy Decision Engine** | **Deterministic Policy Enforcement**: Authority over verdicts, approval routes (`auto`, `L1`, `L2`), SAR thresholds, and Rules R1–R10. Never bypassed. |
| **Graph Case Memory** | **Persistent Knowledge Record**: Upserts closed investigations back into TigerGraph (`ClosedCase` vertices and `INVOLVES`/`ON_CARD` edges) to serve as precedent for future cases. |

---

## 🎥 Demo Video

*(Placeholder for 3–5 minute final walkthrough video demonstrating live MCP tool execution, TigerGraph multi-hop neighborhood traversal, and automated FinCEN SAR generation)*

- **CLI Trace Inspection**: Run `python -m src.agent.run_case --case_id HHG-006` to observe real-time tool selection, graph query responses, and policy evaluation.
- **TigerGraph GraphStudio**: Open the `FraudInvestigation` graph on Savanna Cloud to visually inspect cardholder transaction subgraphs and incident links.

---

## 🏗️ Technical Architecture

```
                          ┌───────────────────────────┐
                          │   Incoming Fraud Alert    │
                          │   (Case Pack Benchmark)   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Agentic Orchestrator    │
                          │ (Gemini / OpenAI / Det.)  │
                          └─────────────┬─────────────┘
                                        │ (MCP stdio protocol)
                                        ▼
                          ┌───────────────────────────┐
                          │  TigerGraph MCP Server    │
                          │ (investigate, baseline)   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  TigerGraph Savanna Cloud │
                          │  (590k Txns, 5.5k Cases)  │
                          └─────────────┬─────────────┘
                                        │ (Structured Graph Package)
                                        ▼
                          ┌───────────────────────────┐
                          │ Evidence & Episode Engine │
                          │ (Baseline, Z-score, Dates)│
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  Deterministic Policy     │
                          │  Decision Engine (R1–R10) │
                          └─────────────┬─────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │ 20 Case Deliverables  │               │  Graph Memory Storage │
        │ (Official JSON Files) │               │ (5,585 Closed Cases)  │
        └───────────────────────┘               └───────────────────────┘
```

---

## 📋 20-Case Benchmark Deliverables Summary

| Case ID | Trigger | Verdict | Pattern | Prob | Exposure ($) | SAR Filed | Activity Dates | Primary Policy Actions |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **HHG-001** | `risk_score` | `legitimate` | `none` | 0.12 | \$0.00 | NO | - | `ALLOW_TRANSACTION -> CLOSE_NO_FRAUD` |
| **HHG-002** | `risk_score` | `fraud` | `card_not_present_fraud` | 0.80 | \$292.36 | NO | - | `DECLINE_TRANSACTION -> BLOCK_CARD -> CREATE_CASE` |
| **HHG-003** | `customer_report` | `fraud` | `out_of_region_use` | 0.85 | \$49.00 | NO | - | `DECLINE_TRANSACTION -> BLOCK_CARD -> CREATE_CASE` |
| **HHG-004** | `customer_report` | `fraud` | `card_not_present_new_device` | 0.88 | \$343.58 | YES | `2016-12-28` to `2016-12-30` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-005** | `risk_score` | `uncertain` | `none` | 0.35 | \$0.00 | NO | - | `VERIFY_WITH_CUSTOMER -> MONITOR_CARD` |
| **HHG-006** | `customer_report` | `fraud` | `card_not_present_fraud` | 0.85 | \$1,906.07 | YES | `2016-11-21` to `2016-11-21` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-007** | `risk_score` | `legitimate` | `none` | 0.12 | \$0.00 | NO | - | `ALLOW_TRANSACTION -> CLOSE_NO_FRAUD` |
| **HHG-008** | `customer_report` | `fraud` | `card_not_present_new_device` | 0.88 | \$284.65 | YES | `2016-12-18` to `2016-12-20` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-009** | `customer_report` | `fraud` | `card_not_present_fraud` | 0.85 | \$30.02 | NO | - | `DECLINE_TRANSACTION -> BLOCK_CARD -> CREATE_CASE` |
| **HHG-010** | `risk_score` | `fraud` | `card_not_present_new_device` | 0.92 | \$1,000.03 | YES | `2016-12-02` to `2016-12-02` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-011** | `customer_report` | `fraud` | `card_not_present_new_device` | 0.88 | \$470.97 | YES | `2016-12-29` to `2016-12-29` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-012** | `risk_score` | `legitimate` | `none` | 0.12 | \$0.00 | NO | - | `ALLOW_TRANSACTION -> CLOSE_NO_FRAUD` |
| **HHG-013** | `risk_score` | `legitimate` | `none` | 0.12 | \$0.00 | NO | - | `ALLOW_TRANSACTION -> CLOSE_NO_FRAUD` |
| **HHG-014** | `analyst_request` | `fraud` | `card_not_present_new_device` | 0.90 | \$74.96 | YES | `2016-11-22` to `2016-11-22` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-015** | `risk_score` | `fraud` | `card_not_present_new_device` | 0.92 | \$599.94 | YES | `2016-11-17` to `2016-11-17` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-016** | `customer_report` | `fraud` | `card_not_present_new_device` | 0.88 | \$59.67 | YES | `2016-12-11` to `2016-12-11` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-017** | `risk_score` | `uncertain` | `card_not_present_fraud` | 0.35 | \$300.14 | NO | - | `VERIFY_WITH_CUSTOMER -> MONITOR_CARD` |
| **HHG-018** | `customer_report` | `fraud` | `out_of_region_use` | 0.85 | \$39.08 | NO | - | `DECLINE_TRANSACTION -> BLOCK_CARD -> CREATE_CASE` |
| **HHG-019** | `risk_score` | `fraud` | `card_not_present_new_device` | 0.88 | \$99.92 | YES | `2016-12-01` to `2016-12-01` | `DECLINE -> BLOCK -> CREATE_CASE -> FILE_REPORT -> MONITOR` |
| **HHG-020** | `risk_score` | `legitimate` | `none` | 0.08 | \$0.00 | NO | - | `ALLOW_TRANSACTION -> CLOSE_NO_FRAUD` |

---

## ⚡ Quick Start & Reproducibility

### 1. Installation & Environment Setup
Clone repository and install minimal dependencies from [requirements.txt](requirements.txt):
```bash
git clone https://github.com/SambhavRaj18/tigergraph-fraud-agent.git
cd tigergraph-fraud-agent
pip install -r requirements.txt
```

Configure credentials from template (see [.env.example](.env.example)):
```bash
cp .env.example .env
# Fill in TG_HOST, TG_SECRET, TG_TOKEN, and optional LLM API keys
```

### 2. Launch Streamlit Analyst Dashboard
Start the interactive UI dashboard to review benchmark cases, multi-hop graph evidence, and SAR filings:
```bash
streamlit run app.py
```

### 3. Run Comprehensive 6-Stage Validation
Verify all 20 deliverable JSON files against schema, provenance, policy alignment, and referential integrity:
```bash
python -m src.benchmark.validate_final_deliverables
```

### 4. Run Agent Unit Test Suite
Execute unit tests for tool queuing, policy boundaries, and case episode handling:
```bash
python -m unittest src.agent.test_agent_suite
```

### 5. Run MCP Regression Suite
Verify real TigerGraph MCP client execution over `stdio` transport:
```bash
python -m src.benchmark.regression_test
```

### 6. Reproduce All 20 Cases
Regenerate all 20 benchmark case JSON deliverables from scratch:
```bash
python -m src.benchmark.run_benchmark
```

---

## 📁 Repository Structure

```text
tigergraph-fraud-agent/
├── .env.example                          # Sanitized environment configuration template
├── .gitignore                            # Secret & large-dataset protection rules
├── README.md                             # Architectural, benchmark & reproducibility guide
├── requirements.txt                      # Minimal production dependency manifest
├── app.py                                # Streamlit Analyst Investigation Dashboard
├── cases/                                # 20 Official Benchmark JSON Deliverables
│   ├── HHG-001.json
│   ├── ...
│   └── HHG-020.json
├── data/
│   └── raw/
│       ├── README.md                     # Official task specification & policy definitions
│       └── case_pack.csv                 # 20 Benchmark alert triggers
├── docs/
│   └── AGENT_ARCHITECTURE.md             # GraphRAG & Multi-Hop Reasoning design
├── graph/
│   ├── schema/
│   │   ├── schema.gsql                   # Formal TigerGraph GSQL Schema Definition
│   │   └── deploy_schema.py              # Schema deployment script
│   ├── queries/
│   │   ├── investigate_transaction.gsql  # Installed multi-hop investigation query
│   │   └── run_investigation.py          # Query execution helper
│   └── loading/                          # Graph preprocessing & loading pipeline
└── src/
    ├── graph_client.py                   # TigerGraph Savanna Cloud REST++ Client
    ├── agent/
    │   ├── investigation_agent.py        # Agentic investigation orchestrator
    │   ├── llm_provider.py               # Multi-provider LLM abstraction (Gemini/OpenAI/Det)
    │   ├── tools.py                      # Agent investigation tools
    │   └── test_agent_suite.py           # Unit test suite
    ├── mcp/
    │   ├── server.py                     # TigerGraph Model Context Protocol (MCP) server
    │   ├── client.py                     # MCP stdio transport client
    │   └── test_mcp.py                   # MCP protocol test suite
    ├── analysis/
    │   └── evidence_analyzer.py          # Baseline stats, Z-scores & episode analyzer
    ├── policy/
    │   └── decision_engine.py            # Deterministic Policy Engine (Rules R1–R10)
    └── benchmark/
        ├── run_benchmark.py              # Batch benchmark runner
        ├── validate_final_deliverables.py # 6-stage validation suite
        ├── audit_provenance.py           # Factual provenance auditor
        └── regression_test.py            # MCP regression test runner
```

---

## ⚠️ Limitations & Factual Assumptions

1. **Dataset Provenance**: The underlying dataset is derived from the IEEE-CIS Fraud Detection benchmark (Vesta Corporation) augmented with customers, calendar timestamps, channels, and bank detection risk scores.
2. **Factual Customer Provenance**: The raw dataset contains no live customer replies or dispute interactions. Under Policy Rule R1, when an investigation requires customer validation, the assumed response is strictly labeled as `SIMULATED / ASSUMED (not in dataset)`. The agent never asserts simulated statements as observed facts.
3. **Proprietary Features**: Engineered Vesta columns ($V, C, D, M$) and identity codes ($id\_01$ to $id\_38$) are treated strictly as anonymized statistical signals without pretending to know unpublished proprietary definitions.

---

## 📜 License

This project is licensed under the MIT License. Built for the **TigerGraph × Hacker House Goa 2026** Fraud Investigation Challenge.
