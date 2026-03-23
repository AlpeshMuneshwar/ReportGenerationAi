from local_self_correcting_agent import IndustrialSQLAgent
import sqlite3
import os

def debug_query():
    model_path = "models/Qwen2.5-3B-Instruct.Q4_K_M.gguf"
    db_path = "fineract.db"
    agent = IndustrialSQLAgent(model_path, db_path)
    
    question = "can you tell me the balance of mr x's savings account"
    print(f"Question: {question}")
    
    sql = agent.generate_sql(question)
    print(f"Generated SQL:\n{sql}")
    
    # Check if tables exist in DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nTables currently in SQLite: {tables}")
    conn.close()

if __name__ == "__main__":
    debug_query()
