# TigerGraph × Hacker House Goa — Agentic Fraud Investigation Agent

An autonomous, agentic fraud investigation system built on **TigerGraph Savanna Cloud**, **Model Context Protocol (MCP)**, and a **Deterministic Policy Decision Engine** with real-time GraphRAG, multi-hop neighborhood analysis, and FinCEN SAR narrative synthesis.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Incoming Fraud Alert    │
                          │   (Case Pack Benchmark)   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Agentic Orchestrator    │
                          │   (Gemini / OpenAI / Det) │
                          └─────────────┬─────────────┘
                                        │ (MCP Protocol / stdio)
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
                                        │ (Evidence Graph Package)
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
        │  Case Deliverable     │               │  Graph Memory Write   │
        │  (20 Verified JSONs)  │               │  (5,585 Closed Cases) │
        └───────────────────────┘               └───────────────────────┘
```

---

## Key Features

1. **TigerGraph Savanna Cloud Multi-Hop Graph Traversal**:
   - Query multi-hop subgraphs across `Customer`, `Card`, `Transaction`, `DeviceProfile`, `BillingRegion`, `EmailDomain`, and `ClosedCase`.
   - Native temporal edge traversal (`NEXT`) to detect rapid transaction bursts and multi-transaction fraud episodes.

2. **Model Context Protocol (MCP) Integration**:
   - Standardized `stdio` transport connecting the agent to `src.mcp.server`.
   - Exposes tools: `investigate_transaction`, `analyze_evidence`, `get_similar_closed_cases`, and `get_policy_rule`.

3. **Autonomous Agentic LLM Layer**:
   - Multi-provider abstraction supporting **Google Gemini**, **OpenAI**, and high-fidelity **Deterministic Provider**.
   - Iterative reasoning, automated tool selection, and factual provenance verification.

4. **Deterministic Policy Decision Engine (Rules R1–R10)**:
   - Strict enforcement of bank policies and FinCEN regulatory requirements.
   - Exact approval routing (`auto`, `L1`, `L2`).
   - Strict factual provenance (all out-of-band simulated customer prompts explicitly labeled `SIMULATED / ASSUMED (not in dataset)`).

5. **Dynamic Episode & SAR Date Calculations**:
   - Dynamic multi-date span calculation `[min_date, max_date]` reflecting actual transaction dates in multi-day episodes (e.g., HHG-004, HHG-008).

---

## 20-Case Benchmark Deliverables Summary

| Case ID | Trigger Type | Verdict | Pattern | Probability | Exposure ($) | SAR Filed | SAR Activity Dates | Primary Policy Actions |
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

## Quick Start & Verification

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your TigerGraph credentials and optional LLM API keys
```

### 2. Run Comprehensive 6-Stage Validation
```bash
python -m src.benchmark.validate_final_deliverables
```

### 3. Run Agent Unit Test Suite
```bash
python -m unittest src.agent.test_agent_suite
```

### 4. Run MCP Regression Suite
```bash
python -m src.benchmark.regression_test
```

### 5. Regenerate Batch Deliverables
```bash
python -m src.benchmark.run_benchmark
```
