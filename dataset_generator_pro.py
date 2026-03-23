import json
import random

def generate_mega_dataset():
    dataset = []
    
    # --- COMPLEX CATEGORIES ---
    
    # 1. Multi-Table Joins (Loan + Client + Office + Staff)
    offices = ["Head Office", "Regional Branch", "Downtown", "Rural Unit"]
    for office in offices:
        dataset.append({
            "instruction": f"Which loan officers in {office} have more than 50 active loans?",
            "input": "Tables: m_staff, m_office, m_loan. Columns: s.display_name, o.name, l.loan_status_id",
            "output": f"SELECT s.display_name, COUNT(l.id) FROM m_staff s JOIN m_office o ON s.office_id = o.id JOIN m_loan l ON s.id = l.loan_officer_id WHERE o.name = '{office}' AND l.loan_status_id = 300 GROUP BY s.id HAVING COUNT(l.id) > 50;"
        })

    # 2. Date Math & Filtering
    dataset.append({
        "instruction": "Clients who joined in the last 6 months but have no savings account.",
        "input": "Tables: m_client, m_savings_account. Columns: c.display_name, c.joined_date, s.id",
        "output": "SELECT c.display_name FROM m_client c LEFT JOIN m_savings_account s ON c.id = s.client_id WHERE c.joined_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND s.id IS NULL;"
    })

    # 3. Financial Totals (Aggregations)
    dataset.append({
        "instruction": "Average interest rate across all active home loan products.",
        "input": "Tables: m_product_loan, m_loan. Columns: p.name, l.nominal_interest_rate_per_period",
        "output": "SELECT AVG(l.nominal_interest_rate_per_period) FROM m_loan l JOIN m_product_loan p ON l.product_id = p.id WHERE p.name LIKE '%Home%' AND l.loan_status_id = 300;"
    })

    # 4. Transaction Trends (Temporal)
    dataset.append({
        "instruction": "Daily deposit totals for the current month.",
        "input": "Table: m_savings_account_transaction. Columns: transaction_date, amount, transaction_type_enum",
        "output": "SELECT transaction_date, SUM(amount) FROM m_savings_account_transaction WHERE transaction_type_enum = 1 AND MONTH(transaction_date) = MONTH(CURDATE()) AND YEAR(transaction_date) = YEAR(CURDATE()) GROUP BY transaction_date;"
    })

    # --- MASSIVE SCALING (1200+ ROWS) ---
    templates = [
        ("account balance of client {id}", "m_savings_account.account_balance_derived", "SELECT account_balance_derived FROM m_savings_account WHERE client_id = {id};"),
        ("total repayments for loan {id}", "m_loan.total_repayment_derived", "SELECT total_repayment_derived FROM m_loan WHERE id = {id};"),
        ("who is the loan officer for client {id}?", "m_loan, m_staff", "SELECT s.display_name FROM m_staff s JOIN m_loan l ON s.loan_officer_id = s.id WHERE l.client_id = {id};"),
        ("all transactions for savings ID {id}", "m_savings_account_transaction", "SELECT * FROM m_savings_account_transaction WHERE savings_account_id = {id};"),
        ("count clients in office {id}", "m_client", "SELECT COUNT(*) FROM m_client WHERE office_id = {id};"),
        ("loans disbursed after {date}", "m_loan", "SELECT * FROM m_loan WHERE disbursedon_date > '{date}';"),
        ("clients with more than {amt} in savings", "m_savings_account", "SELECT client_id FROM m_savings_account WHERE account_balance_derived > {amt};")
    ]

    for i in range(1200):
        t_q, t_inc, t_sql = random.choice(templates)
        val = random.randint(1, 10000)
        date = f"202{random.randint(0,4)}-{random.randint(1,12):02d}-01"
        amt = random.randint(1000, 50000)
        
        instruction = t_q.format(id=val, date=date, amt=amt)
        sql = t_sql.format(id=val, date=date, amt=amt)
        
        dataset.append({
            "instruction": instruction,
            "input": f"Tables/Columns: {t_inc}",
            "output": sql
        })

    return dataset

def generate_test_dataset(count=100):
    dataset = []
    templates = [
        ("total balance for client {id}", "m_savings_account", "SELECT SUM(account_balance_derived) FROM m_savings_account WHERE client_id = {id};"),
        ("list staff in office {id}", "m_staff", "SELECT * FROM m_staff WHERE office_id = {id};"),
        ("loans created after {date}", "m_loan", "SELECT id FROM m_loan WHERE created_date > '{date}';")
    ]
    for i in range(count):
        t_q, t_inc, t_sql = random.choice(templates)
        val = random.randint(10001, 20000) # Use different range for test ids
        date = f"2025-01-01"
        instruction = t_q.format(id=val, date=date)
        sql = t_sql.format(id=val, date=date)
        dataset.append({"instruction": instruction, "input": f"Tables: {t_inc}", "output": sql})
    return dataset

if __name__ == "__main__":
    # Training Data
    train_data = generate_mega_dataset()
    with open("dataset_pro.jsonl", "w") as f:
        for entry in train_data:
            f.write(json.dumps(entry) + "\n")
    
    # Validation Data (Held-out)
    test_data = generate_test_dataset(150)
    with open("test_dataset_pro.jsonl", "w") as f:
        for entry in test_data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"🌍 Generated {len(train_data)} train rows and {len(test_data)} test rows.")
