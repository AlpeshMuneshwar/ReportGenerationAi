import sqlalchemy
from sqlalchemy import text
from llama_cpp import Llama
from local_rag_schema_manager import SchemaRAG

# Main SQL Agent class. 
# It handles the LLM calls and has a basic self-correction loop if the SQL is junk.
class IndustrialSQLAgent:
    def __init__(self, model_path, db_uri="sqlite:///fineract.db"):
        # Load up the GGUF model. Make sure you have enough RAM!
        self.llm = Llama(model_path=model_path, n_ctx=4096, n_threads=8)
        self.db_uri = db_uri
        self.engine = sqlalchemy.create_engine(db_uri)
        self.dialect = self.engine.name # e.g., 'sqlite', 'mysql', 'postgresql'
        self.rag = SchemaRAG()

    def generate_sql(self, question, context_packet, error_msg=None):
        # Construct the prompt. We give it the domain rules and the schema we found in RAG.
        system_prompt = f"""You are a senior SQL expert. 
Current System Context:
{context_packet['domain_rules']}

Relevant Tables:
{context_packet['schema_details']}

Rules:
1. Use {self.dialect.upper()} syntax.
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

    def run_query(self, question, context_packet, max_retries=3, on_status=None):
        # on_status is a callback so the UI can show what's happening in real time
        error_msg = None
        last_sql = ""

        for attempt in range(max_retries):
            if on_status:
                if attempt == 0:
                    on_status(f"Generating SQL (attempt {attempt + 1}/{max_retries})...")
                else:
                    on_status(f"Self-correcting SQL (attempt {attempt + 1}/{max_retries})...")

            raw_response = self.generate_sql(question, context_packet, error_msg)
            last_sql = self._extract_sql(raw_response)

            if on_status:
                on_status(f"SQL: `{last_sql[:100]}{'...' if len(last_sql) > 100 else ''}`")

            try:
                with self.engine.connect() as conn:
                    result_proxy = conn.execute(text(last_sql))
                    # SQLAlchemy returns Row objects which act like tuples, 
                    # we use mapping() to get dictionary-like behavior
                    results = [dict(row._mapping) for row in result_proxy]
                
                # Query ran fine - return success with whatever data we got (could be empty)
                return {
                    "status": "success",
                    "data": results,
                    "sql": last_sql,
                    "attempts": attempt + 1
                }

            except sqlalchemy.exc.SQLAlchemyError as e:
                # Get the actual string error from the driver
                error_msg = str(e.__dict__.get('orig', e))
                if on_status:
                    on_status(f"Error: {error_msg}")
                print(f"--- Attempt {attempt + 1} failed: {error_msg} ---")

        # Exhausted all retries — SQL generation is fundamentally broken for this query
        return {
            "status": "failed",
            "data": None,
            "sql": last_sql,
            "error": error_msg,
            "attempts": max_retries
        }

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
