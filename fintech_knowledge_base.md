# Fintech AI Analyst: Core Knowledge Base (Fineract Edition)

This document provides the "Business Brain" for the AI Analyst. Injecting these definitions into the RAG context or prompt ensures the model understands banking jargon and logic.

## 1. Domain Overview: Double-Entry Accounting
Every financial movement in Fineract hits the General Ledger (`acc_gl_journal_entry`).

- **DR / CR (Type Enum)**:
  - `1` = Credit (CR)
  - `2` = Debit (DR)
- **Accounting Reconciliation**: To verify a loan disbursement, compare `m_loan.principal_disbursed_derived` with the sum of journal entries tagged to that loan's transaction ID.

## 2. Loan Status & Lifecycle Enums
The `loan_status_id` column determines where the loan is in the pipeline:
- `100`: Submitted (Pending Approval)
- `200`: Approved
- `300`: **Active** (Disbursed and earning interest)
- `400`: Withdrawn by Client
- `500`: Rejected
- `600`: Closed (Fully Repaid)
- `601`: Written Off
- `700`: Overpaid

## 3. "Derived" vs. "Transaction" Tables
- **Derived Columns** (e.g., `principal_repaid_derived`): Stored directly on the table for **High Performance**. Use these for high-level summaries (Total Portfolio, PAR).
- **Transaction Tables** (e.g., `m_loan_transaction`): Use these for **Time-Based Trends** (e.g., "Repayments this week").

## 4. Key Metrics (Ratios)
- **PAR (Portfolio at Risk)**: `SUM(principal_outstanding_derived)` where the loan is overdue.
- **Disbursement YTD**: `SUM(principal_disbursed_derived)` filtered by `YEAR(disbursedon_date)`.

## 5. Office Hierarchy
The `m_office` table is a **Self-Referencing Parent-Child** tree.
- To get all activity for a region, you must join `m_office` by `parent_id` or join the target table to `m_office` directly.

---
*Note: This Knowledge Base should be loaded into the RAG `SchemaRAG.add_schema` method alongside the DDL.*
