# Industrial AI Analyst 🏦

> **Developer's Note**: I built this because most "Chat with Data" tools are too hallucination-prone for real industrial use. This setup uses a two-pass RAG system to make sure the AI actually understands the domain rules *before* it touches the SQL.

A 100% local, high-precision AI Data Analyst. No cloud, no leaks, and no fake data.

## ✨ Why this is different
- **Domain-First RAG**: It checks the `fintech_knowledge_base.md` first. If the rules say "use derived columns for totals", that's exactly what it does.
- **Self-Correcting SQL Agent**: If the SQL fails, the agent gets the raw SQLite error and has to fix its own mistake (up to 3 retries).
- **Zero-Trust**: Runs entirely on your machine. Perfect for sensitive fintech data.

## 🚀 Getting Started
1.  **Initialize**: 
    ```bash
    python initialize_system.py
    ```
    *This wipes the old DB and sets up a fresh one with 'Mr X' for testing.*
    
2.  **Launch**:
    ```bash
    streamlit run streamlit_app.py
    ```

## 🛠️ Performance Tips
- Use a decent GPU if you can; the **Qwen2.5 3B** model is fast, but it loves VRAM.
- If the RAG feels "off", hit the **Nuke & Rebuild** button in the sidebar.

## 📂 What's inside?
- `streamlit_app.py`: The UI (built with some vertical alignment hacks).
- `local_rag_schema_manager.py`: The RAG "brain".
- `local_self_correcting_agent.py`: The SQL logic.
- `hydrate_db.py`: Seeds the database so you're not starting empty.
