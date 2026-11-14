# Screenshot Submission Guide & Checklist

This folder contains execution evidence and screenshots for the **From Git to Gold** Data Engineering Assignment.

**Student Name:** Golla Teja  
**Roll Number:** 23BCS091  
**Repository:** https://github.com/teja-0311/freshcart-pipeline  

---

## Required Screenshots Checklist

| Ref # | Component | Description / Target Window | Filename |
| :--- | :--- | :--- | :--- |
| **A-1** | Part A: CI Passing | Green passing run in GitHub Actions tab (`test (3.12)` passed). | `part_a_ci_green.png` |
| **A-2** | Part A: CI Failing | Red failing run in GitHub Actions tab (`test_size = 0.3` failure). | `part_a_ci_red.png` |
| **B-1** | Part B: Snowflake Baseline | Snowflake worksheet / notebook showing 8 bronze, 6 silver clean, 2 quarantine rows. | `part_b_baseline_counts.png` |
| **B-2** | Part B: Quarantine Orders | Output showing quarantined orders `ORD-1004` and `ORD-1006` with reasons array. | `part_b_quarantine_reasons.png` |
| **B-3** | Part B: Gold Fact Table | Final gold table showing 4 orders, ₹7,785.00 revenue, 126 loyalty points. | `part_b_gold_table.png` |
| **B-4** | Part B: Currency Validation | `quarantine.orders` showing `unsupported_currency` for `ORD-1006`. | `part_b_currency_validation.png` |
| **B-5** | Part B: Customer SCD2 | `dim.customers_scd2` showing 2 rows for `CUST-02` (Arjun Gold effective 2026-08-15). | `part_b_scd2_customers.png` |
| **B-6** | Part B: Quality Check Failure | Output showing Check 6 deliberate failure reporting `PROBLEM`. | `part_b_quality_check_fail.png` |
| **B-7** | Part B: Quality Check Recovery| Output showing Check 6 returning to `OK (0)` after cleanup. | `part_b_quality_check_pass.png` |
| **C-1** | Part C: Mage Graph | Mage pipeline DAG showing `load_iris -> validate_data -> prepare_data -> train_model` branching into `save_results` and `evaluate_model`. | `part_c_mage_graph.png` |
| **C-2** | Part C: Test Gate Failing | Console/UI showing pipeline blocked at `max_depth = 1` by `@test` gate. | `part_c_test_gate_fail.png` |
| **C-3** | Part C: Test Gate Passing | Console/UI showing pipeline passing at `max_depth = 3` and writing CSV. | `part_c_test_gate_pass.png` |
| **C-4** | Part C: Evaluation Branch | Confusion matrix and metrics classification report output. | `part_c_evaluation_metrics.png` |
| **D-1** | Part D: Dispatcher Console | Dispatcher terminal output sending orders every 2s with malformed messages. | `part_d_dispatcher_console.png` |
| **D-2** | Part D: Driver Ravi Console | Terminal running `python driver.py Ravi "bangalore.koramangala.*"`. | `part_d_driver_ravi.png` |
| **D-3** | Part D: Driver Arjun Console | Terminal running `python driver.py Arjun "bangalore.*.ride"`. | `part_d_driver_arjun.png` |
| **D-4** | Part D: Driver Control Console| Terminal running `python driver.py Control "bangalore.#"`. | `part_d_driver_control.png` |
| **D-5** | Part D: ACK/NACK Demonstration | Console showing `[ACK]` for valid orders and `[NACK]` (requeue=False) for missing zone. | `part_d_ack_nack.png` |
