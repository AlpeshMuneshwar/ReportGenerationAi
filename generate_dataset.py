import os
import json
import re

def extract_schema(sql_file):
    """
    Extracts a simplified schema representation (Tables and Columns) 
    from a SQL DDL file for LLM context.
    """
    with open(sql_file, 'r') as f:
        content = f.read()

    # Find CREATE TABLE segments
    tables = re.findall(r'CREATE TABLE `(\w+)` \((.*?)\) ENGINE', content, re.DOTALL)
    
    schema = {}
    for table_name, columns_block in tables:
        # Extract column names
        cols = re.findall(r'`(\w+)`', columns_block)
        # Filter out common SQL keywords caught by regex if any
        schema[table_name] = cols
        
    return schema

def generate_synthetic_prompts(schema):
    """
    Generates sample Question/SQL pairs for the Fineract schema.
    In a real scenario, you would use a larger LLM (GPT-4) to 
    generate 1000s of these. This is a template generator.
    """
    dataset = []
    
    # Example 1: Simple Select
    if 'm_client' in schema:
        dataset.append({
            "instruction": "Find all columns for a client with account number '12345'",
            "input": f"Table: m_client. Columns: {', '.join(schema['m_client'])}",
            "output": "SELECT * FROM m_client WHERE account_no = '12345';"
        })
        
    # Example 2: Join
    if 'm_client' in schema and 'm_loan' in schema:
        dataset.append({
            "instruction": "Get the first name and loan amount for all clients who have a loan.",
            "input": f"Tables: m_client, m_loan. Columns: {', '.join(schema['m_client'])}, {', '.join(schema['m_loan'])}",
            "output": "SELECT c.firstname, l.principal_amount FROM m_client c JOIN m_loan l ON c.id = l.client_id;"
        })

    # Example 3: Aggregation
    if 'm_loan' in schema:
        dataset.append({
            "instruction": "What is the total principal amount disbursed across all loans?",
            "input": f"Table: m_loan. Columns: {', '.join(schema['m_loan'])}",
            "output": "SELECT SUM(principal_disbursed_derived) FROM m_loan;"
        })

    return dataset

if __name__ == "__main__":
    sql_path = "fineract_core_banking/core_schema.sql"
    if os.path.exists(sql_path):
        schema = extract_schema(sql_path)
        dataset = generate_synthetic_prompts(schema)
        
        with open("dataset.jsonl", "w") as f:
            for entry in dataset:
                f.write(json.dumps(entry) + "\n")
        
        print(f"Generated {len(dataset)} sample entries in dataset.jsonl")
        print("NOTE: Use this script as a starting point. For best results, use GPT-4 to expand this to 1000+ complex queries.")
    else:
        print(f"Error: {sql_path} not found. Please run the script in the directory containing the cloned schema.")
