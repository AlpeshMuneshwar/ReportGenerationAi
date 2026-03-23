import chromadb
from chromadb.utils import embedding_functions
import os
import re

# --- Developer's Note ---
# This class is the "brain" of our schema awareness. 
# It uses ChromaDB to map natural language questions to actual SQL tables.
# I've split it into two collections: one for raw schema (DDL) and one for business rules (KB).
# ------------------------

class SchemaRAG:
    def __init__(self, persist_directory="./chroma_db"):
        # Initialize the persistent client so we don't lose our index on every restart
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Grab or spin up our collections
        self.schema_collection = self._get_kb_or_schema("schema_coll")
        self.kb_collection = self._get_kb_or_schema("business_rules_coll")

    def _get_kb_or_schema(self, name):
        # Quick helper to keep __init__ clean
        return self.client.get_or_create_collection(
            name=name, 
            embedding_function=self.embedding_function
        )

    def add_knowledge_base(self, file_path):
        # Only index if the file actually exists, obviously.
        if not os.path.exists(file_path):
            print(f"Skipping KB index: {file_path} not found.")
            return

        print(f"Indexing Domain Knowledge: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        # We split by '##' to treat each section as a separate context chunk
        sections = raw_text.split("\n## ")
        for i, chunk in enumerate(sections):
            if not chunk.strip(): continue
            
            section_title = chunk.split("\n")[0].strip()
            # Making the ID unique and searchable
            doc_id = f"rule_{i}_{section_title.lower().replace(' ', '_')}"
            
            self.kb_collection.upsert(
                documents=[chunk],
                metadatas=[{"title": section_title, "source": "fintech_kb"}],
                ids=[doc_id[:60]] # Chroma can be picky about long IDs
            )

    def add_schema(self, software_name, ddl):
        # This part is a bit of a regex playground to parse the SQL dump
        print(f"Updating schema index for: {software_name}")
        
        # Split by CREATE TABLE to isolate each table block
        blocks = re.split(r'CREATE TABLE', ddl, flags=re.IGNORECASE)
        docs, metas, ids = [], [], []
        seen = set()

        for block in blocks[1:]:
            # Find the table name
            name_match = re.search(r'`?(\w+)`?\s*\(', block)
            if not name_match: continue
            table = name_match.group(1).lower()

            # Unique ID for this table's metadata
            t_id = re.sub(r'\W+', '_', f"{software_name}_{table}")

            # Grab the inner details of the columns
            lines = block.split(",")
            for line in lines:
                # Look for column name + type
                col_match = re.search(r'^\s*`?(\w+)`?\s+(\w+)', line)
                if col_match:
                    col = col_match.group(1).lower()
                    dtype = col_match.group(2)

                    # Filter out SQL noise
                    if col in ["primary", "key", "constraint", "unique", "index", "foreign"]:
                        continue

                    c_id = f"{t_id}_{col}"
                    if c_id not in seen:
                        # Find comments if they exist
                        comment_match = re.search(r"COMMENT\s+'(.+?)'", line, re.IGNORECASE)
                        note = comment_match.group(1) if comment_match else "No description"
                        
                        docs.append(f"Table: {table}, Column: {col}, Type: {dtype}, Bio: {note}")
                        metas.append({"sw": software_name, "tbl": table, "obj": "column"})
                        ids.append(c_id)
                        seen.add(c_id)

        # Fire and forget (upsert)
        if docs:
            print(f"Pushing {len(docs)} schema elements to Chroma...")
            self.schema_collection.upsert(documents=docs, metadatas=metas, ids=ids)

    def retrieve_advanced_context(self, software_name, query):
        # Step 1: Check our business rules first to understand the context
        kb_results = self.kb_collection.query(query_texts=[query], n_results=2)
        rules = "\n---\n".join(kb_results['documents'][0]) if kb_results['documents'] else "No matching rules."

        # Step 2: Find the actual technical schema parts
        schema_results = self.schema_collection.query(
            query_texts=[query], 
            n_results=10, 
            where={"sw": software_name}
        )
        
        # Group by table so the LLM doesn't get confused by random columns
        tables = {}
        for i, meta in enumerate(schema_results['metadatas'][0]):
            t_name = meta['tbl']
            content = schema_results['documents'][0][i]
            if t_name not in tables: tables[t_name] = []
            tables[t_name].append(content)
            
        # Build the final context string
        schema_dump = ""
        for t_name, info in tables.items():
            schema_dump += f"\n[TABLE: {t_name}]\n- " + "\n- ".join(info) + "\n"
            
        return {
            "domain_rules": rules,
            "schema_details": schema_dump,
            "table_names": list(tables.keys())
        }

if __name__ == "__main__":
    # Test drive
    brain = SchemaRAG()
    print("Schema Manager is live.")
