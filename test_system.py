from local_self_correcting_agent import IndustrialSQLAgent
import os

def test_system():
    model_path = "models/Qwen2.5-3B-Instruct.Q4_K_M.gguf"
    db_path = "fineract.db"
    
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return

    agent = IndustrialSQLAgent(model_path, db_path)
    
    # Test Query
    question = "Who are my top 5 customers by savings balance?"
    print(f"\n--- Testing Query: {question} ---\n")
    
    # Generate SQL (this will trigger RAG)
    sql = agent.generate_sql(question)
    print(f"Generated SQL:\n{sql}\n")
    
    # Retrieve Context directly for verification
    context = agent.rag.retrieve_advanced_context("Apache Fineract", question)
    print("--- Retrieved Domain rules ---")
    print(context['domain_rules'])
    print("\n--- Retrieved Schema snippets ---")
    print(context['schema_details'])

if __name__ == "__main__":
    test_system()
