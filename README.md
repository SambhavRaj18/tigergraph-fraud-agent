# TigerGraph × Hacker House Goa — Autonomous Fraud Investigation Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TigerGraph Savanna](https://img.shields.io/badge/TigerGraph-Savanna%20Cloud-orange.svg)](https://savanna.tgcloud.io)
[![MCP Protocol](https://img.shields.io/badge/Protocol-MCP%20stdio-green.svg)](https://github.com/tigergraph/tigergraph-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **One-Paragraph Pitch:**  
> The **Autonomous Fraud Investigation Agent** is a production-grade, GraphRAG investigation system that pairs **TigerGraph Savanna Cloud's** native graph analytics with an **Agentic LLM Layer (via Model Context Protocol)** and an authoritative **Deterministic Policy Decision Engine**. Investigating across **590,742 transactions**, **13,553 customers**, and **5,585 closed cases**, the system autonomously gathers multi-hop graph evidence, detects complex fraud syndicates, enforces strict regulatory policies (R1–R10), dynamically calculates multi-day fraud episodes, and generates publication-ready **FinCEN Suspicious Activity Reports (SARs)** with 100% factual provenance.

---

## 📊 Key Benchmark Numbers at a Glance

| Metric | Measured Value | Verification Method |
| :--- | :---: | :--- |
| **Benchmark Cases Solved** | **20 / 20 (100%)** | Validated against official benchmark specification |
| **Total Graph Transactions** | **590,742** | Native TigerGraph Savanna Cloud vertex storage |
| **Graph Case Memory** | **5,585 Cases** | 5,565 historical training cases + 20 closed benchmark investigations |
| **Policy Compliance (R1–R10)**| **100% Strict** | Deterministic Decision Engine approval routing (`auto`, `L1`, `L2`) |
| **Schema & Provenance Errors**| **0 Errors** | Automated 6-stage referential integrity and provenance audit |
| **Unit & MCP Regression Suite**| **10 / 10 Passed** | Real TigerGraph MCP server stdio transport verification |
| **Average Decision Latency** | **< 1.0s / Case** | High-throughput deterministic orchestration & query execution |

---

## 🧠 Why This Is Agentic

Traditional fraud systems rely either on static rule engines that miss multi-hop connections or monolithic black-box LLMs prone to hallucination. Our system is genuinely **agentic**:

1. **Autonomous Tool Selection via MCP**: The LLM iteratively reasons over the investigation state and selects specialized graph tools via the **Model Context Protocol (MCP)** using `stdio` transport.
2. **Multi-Hop GraphRAG Traversal**: Rather than ingesting raw text, the agent issues dynamic graph queries into TigerGraph to retrieve customer baselines, device syndicates, and temporal `NEXT` transaction sequences.
3. **Stateful Graph Memory**: Closed cases are immediately written back into TigerGraph (`ClosedCase` vertices and `INVOLVES`/`ON_CARD` incident edges), enabling the agent to cite precedent cases in future investigations.
4. **Out-of-Band Evidence Queuing**: When evidence is ambiguous, the agent queues structured customer validation requests without blocking or fabricating customer replies.
5. **Separation of Reasoning & Enforcement**: The LLM handles tool selection, evidence synthesis, and FinCEN narrative writing, while the **Deterministic Policy Engine** retains final, immutable authority over verdicts and actions.

---

## ⚖️ Division of Responsibilities: LLM vs. TigerGraph vs. Policy Engine

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                SYSTEM RESPONSIBILITY MATRIX                            │
├─────────────────────────┬───────────────────────────────┬──────────────────────────────┤
│    TigerGraph Savanna   │        Agentic LLM Layer      │   Policy Decision Engine     │
│   (The Graph Database)  │        (The Investigator)     │       (The Authority)        │
├─────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ • 590k+ Transaction Hub │ • Iterative Tool Selection    │ • Strict Rules R1 to R10     │
│ • Multi-Hop Traversal   │ • Hypothesis Evaluation       │ • Action Approval Routing    │
│ • Temporal NEXT Bursts  │ • Multi-Hop Evidence Synthesis│ • SAR Threshold Enforcement  │
│ • Device/Region Sharing │ • Graph Precedent Reasoning   │ • Immutable Action Ordering  │
│ • 5,585 Case Vertices   │ • FinCEN SAR Narrative Gen    │ • Factual Provenance Guard   │
└─────────────────────────┴───────────────────────────────┴──────────────────────────────┘
```

---

## 🏗️ System Architecture

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

Below is the verified summary of all 20 official benchmark investigation deliverables:

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

## ⚡ Quick Start (Developer Path < 3 Minutes)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/SambhavRaj18/tigergraph-fraud-agent.git
cd tigergraph-fraud-agent
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your TigerGraph Savanna Cloud credentials
```

### 3. Run Validation Suite (6-Stage Integrity Check)
```bash
python -m src.benchmark.validate_final_deliverables
```

### 4. Run Unit Test Suite
```bash
python -m unittest src.agent.test_agent_suite
```

### 5. Run MCP Regression Suite
```bash
python -m src.benchmark.regression_test
```

---

## 🔬 Reproducibility & Validation

To reproduce all 20 benchmark deliverables from scratch:

```bash
# Execute batch investigation across all 20 cases and regenerate cases/*.json
python -m src.benchmark.run_benchmark
```

### Verification Checklist:
- ✅ **Schema Compliance**: All 20 JSONs adhere strictly to the schema specification.
- ✅ **Dynamic Date Spans**: Multi-day episodes (HHG-004, HHG-008) span exact dates (`["2016-12-28", "2016-12-30"]`, `["2016-12-18", "2016-12-20"]`).
- ✅ **Graph Memory Integrity**: Exactly **5,585** `ClosedCase` vertices present in TigerGraph Savanna Cloud.

---

## 📁 Repository Structure

```text
tigergraph-fraud-agent/
├── .env.example                    # Sanitized environment configuration template
├── .gitignore                      # Security & dataset ignore rules (protects credentials)
├── README.md                       # Comprehensive architecture & benchmark guide
├── requirements.txt                # Production dependency manifest
├── cases/                          # 20 Official Benchmark JSON Deliverables
│   ├── HHG-001.json
│   ├── ...
│   └── HHG-020.json
├── data/
│   └── raw/
│       ├── README.md               # Official task specification & policy definitions
│       └── case_pack.csv           # 20 Benchmark alert triggers
├── docs/
│   └── AGENT_ARCHITECTURE.md       # GraphRAG & Multi-Hop Reasoning design
├── graph/
│   ├── schema/
│   │   ├── schema.gsql             # TigerGraph GSQL Schema Definition
│   │   └── deploy_schema.py        # Schema deployment utility
│   ├── queries/
│   │   └── investigate_transaction.gsql # Installed multi-hop investigation query
│   └── loading/                    # Graph preprocessing & verification scripts
└── src/
    ├── graph_client.py             # TigerGraph Savanna Cloud REST++ Client
    ├── agent/
    │   ├── investigation_agent.py  # Agentic investigation orchestrator
    │   ├── llm_provider.py         # Multi-provider LLM abstraction (Gemini/OpenAI/Det)
    │   ├── tools.py                # Agent investigation tools
    │   └── test_agent_suite.py     # Unit test suite
    ├── mcp/
    │   ├── server.py               # TigerGraph Model Context Protocol (MCP) server
    │   ├── client.py               # MCP stdio client
    │   └── test_mcp.py             # MCP protocol test suite
    ├── analysis/
    │   └── evidence_analyzer.py    # Baseline stats, Z-scores & episode analyzer
    ├── policy/
    │   └── decision_engine.py      # Deterministic Policy Engine (Rules R1–R10)
    └── benchmark/
        ├── run_benchmark.py        # Batch benchmark runner
        ├── validate_final_deliverables.py # 6-stage validation suite
        ├── audit_provenance.py     # Factual provenance auditor
        └── regression_test.py      # MCP regression test runner
```

---

## ⚠️ Limitations & Factual Assumptions

1. **Dataset Provenance**: The dataset is derived from the IEEE-CIS Fraud Detection dataset (Vesta Corporation) augmented with customer baselines and calendar events.
2. **Customer & Analyst Responses**: The raw dataset contains no live customer replies or dispute interactions. Under Rule R1, when an investigation requires customer validation, the assumed response is strictly labeled as `SIMULATED / ASSUMED (not in dataset)`. The system never fabricates unobserved customer statements as observed facts.
3. **Feature Provenance**: Encoded Vesta features ($V, C, D, M$) and identity fields ($id\_01$ to $id\_38$) are treated strictly as anonymized statistical signals without pretending to know unpublished proprietary definitions.

---

## 🎥 Demo & Walkthrough

*(Demo video walkthrough and interactive console trace placeholder)*

- **CLI Trace**: Run `python -m src.agent.run_case --case_id HHG-006` to inspect real-time tool selection, graph queries, and SAR synthesis.
- **Savanna Graph Visualizer**: Open TigerGraph GraphStudio on the `FraudInvestigation` graph to inspect multi-hop cardholder clusters and incident edges.

---

## 📜 License & Acknowledgments

This project is licensed under the MIT License. Built for the **TigerGraph × Hacker House Goa 2026** Fraud Investigation Challenge.
