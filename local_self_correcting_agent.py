import sqlite3
from llama_cpp import Llama
from local_rag_schema_manager import SchemaRAG

# Main SQL Agent class. 
# It handles the LLM calls and has a basic self-correction loop if the SQL is junk.
class IndustrialSQLAgent:
    def __init__(self, model_path, db_path="fineract.db"):
        # Load up the GGUF model. Make sure you have enough RAM!
        self.llm = Llama(model_path=model_path, n_ctx=4096, n_threads=8)
        self.db_path = db_path
        self.rag = SchemaRAG()

    def generate_sql(self, question, context_packet, error_msg=None):
        # Construct the prompt. We give it the domain rules and the schema we found in RAG.
        system_prompt = f"""You are a senior SQL expert. 
Current System Context:
{context_packet['domain_rules']}

Relevant Tables:
{context_packet['schema_details']}

Rules:
1. Use SQLite syntax.
2. Return ONLY the SQL query inside ```sql blocks.
3. If I provide an error, fix your previous logic.
"""
        user_prompt = f"Question: {question}"
        if error_msg:
            user_prompt += f"\n\nI got an error with your last query: {error_msg}\n\nHere was your previous query:\n{question}"

        prompt = f"""### System:
{system_prompt}

### User:
{user_prompt}

### Response:
"""
        output = self.llm(prompt, max_tokens=512, stop=["###", "<|im_end|>"])
        return output['choices'][0]['text'].strip()

    def run_query(self, question, context_packet, max_retries=3):
        # We try a few times if the LLM spits out bad SQL
        error_msg = None
        for attempt in range(max_retries):
            raw_response = self.generate_sql(question, context_packet, error_msg)
            sql = self._extract_sql(raw_response)
            
            try:
                # Standard SQLite connection
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql)
                results = cursor.fetchall()
                conn.close()
                
                # Convert to list of dicts for easier use in Streamlit/Pandas
                return [dict(row) for row in results]
                
            except sqlite3.Error as e:
                error_msg = str(e)
                print(f"--- Correction Loop: Attempt {attempt + 1} failed ---")
                print(f"Error: {error_msg}")
                # The next iteration will include this error_msg in the prompt
        
        # If we're here, we failed 3 times. Return None so the UI knows.
        return None

    def _extract_sql(self, text):
        # Human-written helper to pull SQL out of markdown blocks
        # We're looking for ```sql ... ```
        if "```sql" in text:
            try:
                return text.split("```sql")[1].split("```")[0].strip()
            except IndexError:
                return text.strip() # Fallback if they forgot to close the block
        return text.strip()

if __name__ == "__main__":
    # Just a placeholder for local testing
    print("Industrial SQL Agent is ready. Load a GGUF model and pass a context packet to start.")
