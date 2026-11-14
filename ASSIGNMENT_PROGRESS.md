# Assignment Progress: From Git to Gold

**Student Name:** Golla Teja  
**Roll Number:** 23BCS091  
**Course:** Data Engineering - Pipeline Orchestration  
**Repository:** https://github.com/teja-0311/freshcart-pipeline  
**Date:** November 2026  

---

## Progress Overview

| Phase / Part | Component | Marks | Status | Verification Summary |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Repository Audit & Materials Check | - | **Completed** | Full repository audit performed, source notebooks and assignment spec extracted. |
| **Phase 1 (Part A)** | Git and CI/CD | 15 | **Completed** | Directory structure, .gitignore, 7-commit history with intentional CI failure and fix verified. 4/4 pytest tests passing. |
| **Phase 2 (Part B)** | FreshCart ELT using Snowflake | 30 | **Completed** | Full `elt/freshcart_elt.ipynb` notebook implemented with baseline, currency rule, SCD2 Arjun event, custom DQ check, and tracing. `.env.example` created. |
| **Phase 3 (Part C)** | Iris ML pipeline using Mage | 20 | **In Progress** | Implementing Mage pipeline blocks and runtime parameter experiments in `iris_project/`. |
| **Phase 4 (Part D)** | Food-order streaming with RabbitMQ | 20 | **Not Started** | Pending Part C completion. |
| **Phase 5 (Part E)** | Final Report, Architecture & Viva | 15 | **Not Started** | Target: `23BCS091_Golla_Teja_Pipelines.pdf`. |
| **Bonus** | RabbitMQ to Snowflake Lakehouse | +10 | **Deferred** | Scheduled after Parts A-E. |

---

## Detailed Task Checklist

### Part A: Git and CI/CD (15 Marks)
- [x] **A1. Repository Structure:** Required directories and files exist.
- [x] **A1. Gitignore:** Verifies ignoring `.env`, `*.pkl`, `*.csv`, `mage.log`, `__pycache__/`, etc.
- [x] **A1. Meaningful Commits:** 7 commits present covering initialization, CI setup, failing CI demonstration, and fix.
- [x] **A2. Git Command Table & Explanation:** Conceptual documentation drafted for report.
- [x] **A3. Pytest Unit Tests:** 4 tests in `tests/test_prepare_data.py` passing locally.
- [x] **A3. GitHub Actions CI:** Workflow configured in `.github/workflows/ci.yml`.

### Part B: FreshCart ELT with Snowflake (30 Marks)
- [x] **B1. Baseline Pipeline Notebook:** Implemented in `elt/freshcart_elt.ipynb`.
- [x] **B2. Record Tracing Documentation:** Traced ORD-1003 (field normalization, dedup QUALIFY ROW_NUMBER, arithmetic) and ORD-1005 (Priya customer tier join).
- [x] **B3. Currency Validation Rule:** Added `unsupported_currency` to `SQL_10_ORDERS_CLEAN` inside `ARRAY_CONSTRUCT_COMPACT()`.
- [x] **B4. SCD Type 2 Update & Idempotency:** Added Arjun event (`effective_from = '2026-08-15'`), documented pre-run predictions vs actuals, explained `row_hash` & `MERGE`.
- [x] **B5. Sixth Data-Quality Check:** Added new check to `quality_checks()`, demonstrated deliberate failure, and recovery. Answered ELT vs ETL.
- [x] **B6. Standalone Execution & Verification:** Provided `.env.example` and safe execution instructions.

### Part C: Mage Iris ML Pipeline (20 Marks)
- [ ] **C1. Pipeline Blocks:** `load_iris`, `prepare_data`, `train_model`, `save_results` with `@test` decorators and `metadata.yaml`.
- [ ] **C2. Parameter Experiments:** Run `max_depth = 1..5`, record accuracy and CSV creation. Explain gating mechanism.
- [ ] **C3. Evaluation Branch:** Add `evaluate_model` with confusion matrix and metrics table.
- [ ] **C4. Custom Block:** Add custom transformer/exporter with `@test`, update CI to ensure pytest compatibility.

### Part D: Food-Order Event Streaming with RabbitMQ (20 Marks)
- [ ] **D1. Paper Routing Table:** Complete matching analysis for binding patterns vs routing keys.
- [ ] **D2. Dispatcher Script:** Implement `stream/dispatcher.py` for `rapido-dispatch` topic exchange.
- [ ] **D3. Driver Script:** Implement `stream/driver.py` with private queues, pattern bindings, and consumption.
- [ ] **D4. ACK / NACK Handling:** Handle malformed messages (`zone` missing) with `basic_nack(requeue=False)` and valid messages with `basic_ack()`.

### Part E: Final Report & Architecture (15 Marks)
- [ ] Comprehensive report document (`23BCS091_Golla_Teja_Pipelines.pdf`, <= 8 pages excluding screenshot appendix).
- [ ] End-to-end architecture diagram covering Git, CI, Snowflake ELT, Mage ML, and RabbitMQ.
- [ ] Half-page implementation reflection (root cause, identification, fix).
- [ ] Genuine execution screenshot guidance and captures.

---

## Log of Identified Issues & Fixes
- *Issue 1 (Part A history):* Intentional test failure (`test_size = 0.3`) caused CI to fail with split counts 105/45 instead of 120/30.
  - *Root Cause:* Stratified split proportion changed.
  - *Fix:* Reverted `test_size` to 0.2 in commit `2650637`.
