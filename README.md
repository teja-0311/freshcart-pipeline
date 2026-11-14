# From Git to Gold: Data Engineering Pipeline Orchestration

[![Python CI](https://github.com/teja-0311/freshcart-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/teja-0311/freshcart-pipeline/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Snowflake](https://img.shields.io/badge/Snowflake-ELT-29B5E8.svg)](https://www.snowflake.com/)
[![Mage AI](https://img.shields.io/badge/Mage-Orchestration-5847F8.svg)](https://www.mage.ai/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Streaming-FF6600.svg)](https://www.rabbitmq.com/)

**Student Name:** Golla Teja  
**Roll Number:** 23BCS091  
**Course:** Data Engineering - Pipeline Orchestration  
**Repository:** [https://github.com/teja-0311/freshcart-pipeline](https://github.com/teja-0311/freshcart-pipeline)  

---

## 1. Project Overview

**"From Git to Gold"** is an end-to-end Data Engineering pipeline demonstration integrating version control, cloud lakehouse ELT on Snowflake, machine learning DAG orchestration with test-driven quality gates in Mage AI, and high-throughput asynchronous event streaming with RabbitMQ.

The project is structured into five core components:
1. **Part A: Git & CI/CD** — Version control hygiene, branch governance, and automated regression testing via GitHub Actions.
2. **Part B: FreshCart ELT on Snowflake** — Ingesting heterogeneous API payloads into Snowflake Bronze (VARIANT), Silver deduplication/quarantine, SCD Type 2 customer history, and idempotent Gold dimensional reporting.
3. **Part C: Iris ML Pipeline using Mage** — Orchestrated classification DAG featuring automated data validation, quality test circuit-breakers, model training, evaluation metrics, and test-gated artifact export.
4. **Part D: Food-Order Event Streaming with RabbitMQ** — Dynamic message dispatching and driver consumption using topic exchanges (`rapido-dispatch`), wildcard binding patterns, and strict ACK/NACK fault tolerance.
5. **Part E: Final Submission Report** — Technical report (`23BCS091_Golla_Teja_Pipelines.pdf`), architecture diagrams, engineering reflections, and screenshot checklist.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Governance ["Code Governance & CI/CD (Part A)"]
        DEV["Local Working Tree"] -->|git commit| REPO["Local Repository (.git)"]
        REPO -->|git push| GITHUB["GitHub Remote (main)"]
        GITHUB -->|on: push| GHA["GitHub Actions (Python 3.12)"]
        GHA -->|pytest -v| TESTS["16 Unit Tests (Quality Gates)"]
    end

    subgraph Lakehouse ["FreshCart Snowflake ELT (Part B)"]
        RAW_API["API Mock Data (Web, Mobile, CRM, FX)"] -->|Extract| LANDING["Landing JSON.GZ Files"]
        LANDING -->|PUT + COPY INTO| BRONZE["bronze.orders_raw (VARIANT)"]
        BRONZE -->|Cleanse & Validate| SILVER_CHECK["silver.orders_checked"]
        SILVER_CHECK -->|ARRAY_SIZE(reasons) > 0| QUARANTINE["quarantine.orders (Anti-Join Guard)"]
        SILVER_CHECK -->|ARRAY_SIZE(reasons) == 0| SILVER_CLEAN["silver.orders_clean"]
        SILVER_CLEAN -->|QUALIFY ROW_NUMBER()| SILVER_DEDUP["silver.orders_dedup"]
        SILVER_DEDUP -->|Point-in-Time Join| GOLD["gold.fct_orders (Idempotent MERGE on row_hash)"]
        CRM["bronze.customers_raw"] -->|SCD Type 2| DIM_CUST["dim.customers_scd2"]
        DIM_CUST -.-> GOLD
    end

    subgraph ML_Orchestration ["Mage ML Pipeline (Part C)"]
        LOAD["load_iris (data_loader)"] -->|@test test_output| VAL["validate_data (custom transformer)"]
        VAL -->|@test test_no_nulls| PREP["prepare_data (stratified 80/20)"]
        PREP -->|@test test_split| TRAIN["train_model (DecisionTreeClassifier)"]
        TRAIN -->|Gate: test_accuracy >= 90%| EXPORT["save_results (data_exporter)"]
        TRAIN -->|Branch| EVAL["evaluate_model (confusion matrix & metrics)"]
    end

    subgraph Streaming ["Food-Order Event Streaming (Part D)"]
        DISPATCHER["stream/dispatcher.py"] -->|Publish (city.zone.type)| EXCH["Topic Exchange: rapido-dispatch"]
        EXCH -->|bangalore.koramangala.*| RAVI["Queue: Ravi"]
        EXCH -->|bangalore.indiranagar.*| PRIYA["Queue: Priya"]
        EXCH -->|bangalore.*.ride| ARJUN["Queue: Arjun"]
        EXCH -->|bangalore.*.food| MEENA["Queue: Meena"]
        EXCH -->|chennai.tnagar.food| KARTHIK["Queue: Karthik"]
        EXCH -->|bangalore.#| CONTROL["Queue: Control"]
        RAVI -->|zone missing? NACK : ACK| DRIVER_CLIENT["driver.py consumer"]
    end
```

---

## 3. Technology Stack

- **Version Control & CI/CD:** Git, GitHub Actions, Ubuntu runners, Python 3.12.
- **Data Warehouse & Cloud ELT:** Snowflake, SQL, SnowSQL, `snowflake-connector-python`.
- **Pipeline Orchestration & ML:** Mage AI, Scikit-learn, Pandas, NumPy.
- **Event Streaming & Message Broker:** RabbitMQ, AMQP 0-9-1, Pika.
- **Testing & Verification:** Pytest, ReportLab (PDF generation).

---

## 4. Repository Structure

```text
freshcart-pipeline/
|-- .github/
|   `-- workflows/
|       `-- ci.yml                   # Automated Python 3.12 pytest CI workflow
|-- elt/
|   `-- freshcart_elt.ipynb          # End-to-end Snowflake ELT pipeline notebook (B1-B6)
|-- iris_project/
|   |-- data_loaders/load_iris.py    # Iris dataset loader with @test
|   |-- transformers/
|   |   |-- validate_data.py         # Custom block checking nulls & classes (C4)
|   |   |-- prepare_data.py          # Stratified 80/20 train/test split with @test
|   |   |-- train_model.py           # Decision tree trainer with 90% accuracy gate
|   |   `-- evaluate_model.py        # Confusion matrix & classification report (C3)
|   |-- data_exporters/save_results.py# Predictions CSV exporter
|   |-- metadata.yaml                # Mage pipeline DAG specification
|   `-- run_pipeline.py              # Standalone CLI runner with parameter support
|-- stream/
|   |-- dispatcher.py                # RabbitMQ order dispatcher (rapido-dispatch)
|   `-- driver.py                    # RabbitMQ driver consumer with ACK/NACK
|-- tests/
|   |-- test_prepare_data.py         # Unit tests for data splitting
|   |-- test_iris_pipeline.py        # Unit tests for all Mage DAG blocks
|   `-- test_stream_routing.py       # Unit tests for topic routing & ACK/NACK logic
|-- screenshots/
|   `-- README.md                    # Screenshot submission guide and evidence list
|-- .env.example                     # Template for environment variables (safe)
|-- .gitignore                       # Protects secrets, CSVs, PKLs, logs, and venvs
|-- 23BCS091_Golla_Teja_Pipelines.pdf# Comprehensive assignment report (<= 8 pages)
|-- ASSIGNMENT_PROGRESS.md           # Persistent assignment task checklist
|-- requirements.txt                 # Project dependencies
`-- README.md                        # Documentation
```

---

## 5. Setup & Installation

### Prerequisites
- Python 3.12+ installed
- Git installed
- (Optional for Part B) Snowflake trial account
- (Optional for Part D) Local RabbitMQ server, Docker, or CloudAMQP free instance

### Clone & Install
```bash
git clone https://github.com/teja-0311/freshcart-pipeline.git
cd freshcart-pipeline

# Create virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

---

## 6. How to Run Each Component

### A. Run Automated Unit Tests (CI/CD)
To execute all 16 unit tests across Parts A, C, and D:
```bash
python -m pytest -v
```

### B. Run FreshCart ELT (Part B)
Open `elt/freshcart_elt.ipynb` in VS Code or JupyterLab:
1. Ensure `.env` contains valid Snowflake credentials.
2. Run cells sequentially from top to bottom.
3. Observe baseline counts:
   - Bronze raw orders: 8
   - Silver clean orders: 6
   - Quarantined orders: 2 (`ORD-1004`, `ORD-1006`)
   - Deduplicated orders: 4
   - Gold: 4 orders, revenue ₹7,785.00, 126 loyalty points, 25% rejected share.
4. Inspect Part B4 SCD Type 2 updates for Arjun (points increase to 161).

### C. Run Mage ML Pipeline (Part C)
Execute the complete pipeline with default parameters:
```bash
python -m iris_project.run_pipeline
```

Run test-gate experiment with custom `max_depth`:
```bash
# This will fail the 90% gate (accuracy = 66.7%) and block iris_predictions.csv
python -m iris_project.run_pipeline --runtime-vars '{"max_depth": 1}'

# This will pass the gate (accuracy = 96.7%) and generate iris_predictions.csv
python -m iris_project.run_pipeline --runtime-vars '{"max_depth": 3}'
```

### D. Run RabbitMQ Food-Order Streaming (Part D)
Start consumers in separate terminal windows:
```bash
# Window 1: Driver Ravi (Koramangala orders)
python stream/driver.py Ravi "bangalore.koramangala.*"

# Window 2: Driver Arjun (All Bangalore rides)
python stream/driver.py Arjun "bangalore.*.ride"

# Window 3: Driver Control (All Bangalore activity)
python stream/driver.py Control "bangalore.#"
```

Start the dispatcher in a 4th terminal window:
```bash
python stream/dispatcher.py --interval 2.0
```
- Valid orders are processed with `[ACK]`.
- Every 10th message is malformed (missing zone) and discarded with `[NACK] (requeue=False)`.

---

## 7. Submission Checklist Verification

| Part | Component | Status | Verified Evidence |
| :--- | :--- | :--- | :--- |
| **Part A** | Git & CI/CD | **PASS** | 7 meaningful commits, green & red CI demonstration, 4 passing tests. |
| **Part B** | FreshCart Snowflake ELT | **PASS** | `elt/freshcart_elt.ipynb` (B1-B6 verified, currency rule, SCD2, DQ check). |
| **Part C** | Mage Iris ML Pipeline | **PASS** | 6 blocks in `iris_project/`, gate experiments verified, evaluation branch active. |
| **Part D** | RabbitMQ Streaming | **PASS** | `dispatcher.py` & `driver.py`, routing patterns verified, ACK/NACK handling. |
| **Part E** | Final Report | **PASS** | `23BCS091_Golla_Teja_Pipelines.pdf` generated (4 pages, strictly <= 8 pages). |

---

## Author
**Golla Teja** (Roll No: 23BCS091)  
Department of Computer Science & Engineering  
Course: Data Engineering - Pipeline Orchestration