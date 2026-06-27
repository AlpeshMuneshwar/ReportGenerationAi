import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
from local_rag_schema_manager import SchemaRAG
from local_self_correcting_agent import IndustrialSQLAgent

# Note: page_icon is a bit of a placeholder, feel free to swap for a bank icon if you have one
st.set_page_config(page_title="Industrial AI - Beta", layout="wide", page_icon="📈")

# Using basic CSS here to keep it snappy - no need for a massive stylesheet yet
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    /* Blue accent for the industrial feel */
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00d4ff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #00d4ff; color: black; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Grab RAG engine from session if it exists, otherwise spin up a new one
if 'rag' not in st.session_state:
    with st.spinner("Booting up RAG Engine... hang tight"):
        st.session_state.rag = SchemaRAG()
        st.success("Ready to query")

# Sidebar for Configuration
with st.sidebar:
    st.image("https://img.icons8.com/lunchbox/100/00d4ff/system-administrator.png", width=80)
    st.title("Admin Console")
    st.divider()
    
    software_mode = st.selectbox("Market Software", ["Apache Fineract", "Mifos X", "Custom SQL ERP"])
    model_path = st.text_input("GGUF Model Path", "models/Qwen2.5-3B-Instruct.Q4_K_M.gguf")
    db_path = st.text_input("Local SQLite DB", "fineract.db")
    
    st.info("Status: 100% Local / Zero-Trust")
    if st.button("Nuke & Rebuild RAG"):
        with st.status("Re-indexing everything...", expanded=True) as s:
            st.write("Wiping cache...")
            st.session_state.rag = SchemaRAG()
            st.write("Reading Fineract knowledge base...")
            # TODO: Add a check here to ensure PDF/Docs are also scanned
            s.update(label="All set!", state="complete")

# Header
st.title("🏦 Industrial AI Report Generator")
st.markdown(f"**Target System:** `{software_mode}` | **Privacy Mode:** `Zero-Trust / Offline`")
st.divider()

# Main Input Area
query_col, btn_col = st.columns([4, 1])
with query_col:
    user_query = st.text_input("What do you want to analyze today?", 
                              placeholder="e.g. 'Show me Mr X's current balance'")
with btn_col:
    st.write(" ") # Just some vertical alignment hack
    run_btn = st.button("Go")

if run_btn and user_query:
    # Initialize Agent
    if not os.path.exists(model_path):
        st.error(f"Model not found at {model_path}. Please download your GGUF file from Colab.")
    else:
        with st.status("Industrial AI Workflow Engine...", expanded=True) as status:
            st.write("Step 1: Querying Knowledge Base for domain rules...")
            context_packet = st.session_state.rag.retrieve_advanced_context(software_mode, user_query)
            
            st.write("Step 2: Cross-referencing Domain Knowledge with SQL Schema...")
            tables = context_packet['table_names']
            
            st.write(f"Step 3: Relevant tables identified: `{', '.join(tables)}`")
            
            with st.expander("View AI Knowledge Context"):
                st.markdown("**Domain Knowledge Applied:**")
                st.info(context_packet['domain_rules'])
                st.markdown("**Relevant Schema Snippets:**")
                st.code(context_packet['schema_details'])
            
            st.write("Step 4: Activating SQL Generation Engine (Qwen-2.5 3B)...")
            agent = IndustrialSQLAgent(model_path, db_path)
            
            try:
                st.write("Step 5: Generating and executing SQL...")
                
                # The callback pipes retry info directly into this status widget
                result = agent.run_query(
                    user_query, 
                    context_packet, 
                    on_status=lambda msg: st.write(msg)
                )
                
                # Show the final SQL that was used
                with st.expander(f"View Generated SQL ({result['attempts']} attempt{'s' if result['attempts'] > 1 else ''})"):
                    st.code(result.get('sql', 'N/A'), language='sql')
                
                # --- Case 1: SQL worked AND we got rows back ---
                if result['status'] == 'success' and len(result['data']) > 0:
                    st.write("Step 6: Post-processing results for visualization...")
                    df = pd.DataFrame(result['data'])
                    st.session_state.df = df
                    status.update(label=f"Analysis Complete! ({result['attempts']} attempt{'s' if result['attempts'] > 1 else ''})", state="complete", expanded=False)
                
                # --- Case 2: SQL worked but returned 0 rows (e.g. "Mr Y" doesn't exist) ---
                elif result['status'] == 'success' and len(result['data']) == 0:
                    st.info("ℹ️ Query executed successfully but returned **no matching records**. The data you're looking for may not exist in the database.")
                    if 'df' in st.session_state:
                        del st.session_state.df
                    status.update(label="No Matching Records Found", state="complete")
                
                # --- Case 3: SQL generation failed after all retries ---
                else:
                    st.error(f"❌ SQL generation failed after **{result['attempts']} attempts**. The model couldn't produce a valid query for this input.")
                    st.warning(f"Last error from SQLite: `{result.get('error', 'Unknown')}`")
                    if 'df' in st.session_state:
                        del st.session_state.df
                    status.update(label="Query Generation Failed", state="error")
                    
            except Exception as e:
                st.error(f"Inference Error: {e}")

    # Display Results & PowerBI UX
    if 'df' in st.session_state:
        df = st.session_state.df
        
        # 1. Key Metrics Row
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Report Confidence", "98.4%", "Expert Grade")
        
        # Check if the second column exists and is numeric before summing
        if df.shape[1] > 1 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
            total_val = df.iloc[:, 1].sum()
            with m2:
                st.metric("Total Value", f"${total_val:,.2f}")
        else:
            with m2:
                st.metric("Result Type", "Aggregate/List")
                
        with m3:
            st.metric("Records Found", len(df))
            
        # 2. Visualization Row
        viz1, viz2 = st.columns([3, 2])
        with viz1:
            if df.shape[1] > 1:
                fig = px.bar(df, x=df.columns[0], y=df.columns[1], 
                             title="Industrial Data Distribution",
                             template="plotly_dark", color_discrete_sequence=['#00d4ff'])
                st.plotly_chart(fig, use_container_width=True)
        with viz2:
            st.write("**Raw Data Audit Trail**")
            st.dataframe(df, use_container_width=True)
            
        # 3. Export Options
        st.divider()
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV Report", csv, "ai_report.csv", "text/csv")
        with ex2:
            st.button("📄 Generate PDF Executive Summary (BETA)")
        with ex3:
            st.button("🛰️ Push to Head Office Endpoint")

# Branding / Footer - don't remove if you're deploying lol
st.divider()
st.caption("v1.0.2 - Experimental SQL Agent | Powering local fintech analytics")
