import os
from local_rag_schema_manager import SchemaRAG
from hydrate_db import hydrate
import sqlite3

def initialize():
    print("Starting the Industrial AI Analyst setup...")
    
    # First, we need the RAG engine ready to roll
    rag = SchemaRAG()
    
    # Next, we index the knowledge base - this gives the AI its 'business brain'
    kb_path = "fintech_knowledge_base.md"
    if os.path.exists(kb_path):
        rag.add_knowledge_base(kb_path)
        print("Knowledge Base indexed successfully.")
    else:
        print("Heads up: Knowledge Base file missing.")

    # Now the technical part: indexing the actual SQL schema
    schema_path = "fineract_core_banking/core_schema.sql"
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            ddl = f.read()
        rag.add_schema("Apache Fineract", ddl)
        print("Fineract Schema indexed.")
    else:
        print("Error: fineract_core_banking/core_schema.sql not found.")

    # Finally, make sure the database is hydrated with some test data
    db_path = "fineract.db"
    hydrate()
    print("Local database is ready with test records (Mr X, etc).")

    print("\nAll set! You're good to go. Run: streamlit run streamlit_app.py")

if __name__ == "__main__":
    initialize()
