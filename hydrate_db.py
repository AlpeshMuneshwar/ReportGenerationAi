import sqlite3
import os

def hydrate():
    db_path = "fineract.db"
    
    # Simple check - if it exists, we just overwrite for a clean start
    # TODO: In production, we'd probably want to migrate instead of nuke
    if os.path.exists(db_path):
        os.remove(db_path)
        
    print(f"Creating fresh DB at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # 1. Create the core tables
    # Just the essentials for now to prove the RAG works
    print("Setting up m_office, m_client, and m_savings_account...")
    conn.executescript("""
    CREATE TABLE m_office (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        external_id TEXT
    );
    CREATE TABLE m_client (
        id INTEGER PRIMARY KEY,
        account_no TEXT UNIQUE,
        office_id INTEGER,
        firstname TEXT,
        lastname TEXT,
        display_name TEXT,
        FOREIGN KEY (office_id) REFERENCES m_office(id)
    );
    CREATE TABLE m_savings_account (
        id INTEGER PRIMARY KEY,
        account_no TEXT UNIQUE,
        client_id INTEGER,
        account_balance REAL,
        currency_digits INTEGER,
        FOREIGN KEY (client_id) REFERENCES m_client(id)
    );
    """)

    # 2. Seed some test data so the user isn't looking at an empty screen
    # Adding the 'Mr X' user as requested
    print("Seeding test records...")
    conn.execute("INSERT INTO m_office VALUES (1, 'Head Office', 'HO-001')")
    
    clients = [
        (1, 'CL001', 1, 'Mr.', 'X', 'Mr X'),
        (2, 'CL002', 1, 'Jane', 'Smith', 'Jane Smith'),
        (3, 'CL003', 1, 'Bob', 'Builder', 'Bob Builder')
    ]
    conn.executemany("INSERT INTO m_client VALUES (?,?,?,?,?,?)", clients)
    
    # Let's give Mr X a healthy balance
    savings = [
        (1, 'SA001', 1, 125000.50, 2),
        (2, 'SA002', 2, 450.00, 2),
        (3, 'SA003', 3, 98000.75, 2)
    ]
    conn.executemany("INSERT INTO m_savings_account VALUES (?,?,?,?,?)", savings)
    
    conn.commit()
    conn.close()
    print("Hydration complete.")

if __name__ == "__main__":
    hydrate()
