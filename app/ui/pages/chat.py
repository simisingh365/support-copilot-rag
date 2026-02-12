"""
Streamlit chat page for the RAG Support System.

Provides:
- Chat interface for querying the RAG system
- Display of answers with sources and metrics
"""

import streamlit as st
import requests
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the chat page."""
    st.title("💬 Chat with RAG System")
    st.markdown("Ask questions and get answers from the knowledge base with source citations.")
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources and metrics if available
            if "sources" in message and message["sources"]:
                with st.expander(f"📚 Sources ({len(message['sources'])})"):
                    for j, source in enumerate(message["sources"], 1):
                        st.markdown(f"**Source [{j}]** (Score: {source.get('score', 0):.2f})")
                        st.text(source.get("text", ""))
            
            if "metrics" in message and message["metrics"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Retrieval Time",
                        f"{message['metrics'].get('retrieval_time_ms', 0):.0f} ms"
                    )
                with col2:
                    st.metric(
                        "Response Time",
                        f"{message['metrics'].get('response_time_ms', 0):.0f} ms"
                    )
    
    # Chat input
    st.divider()
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_area(
            "Your Question:",
            placeholder="Type your question here...",
            height=100,
            key="user_input"
        )
    
    with col2:
        k = st.number_input(
            "Context Chunks",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of context chunks to retrieve"
        )
    
    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not user_input or not user_input.strip():
            st.warning("Please enter a question.")
            return
        
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Show loading spinner
        with st.spinner("Searching knowledge base and generating answer..."):
            try:
                # Call RAG API
                response = requests.post(
                    f"{API_BASE_URL}/api/rag/query",
                    json={
                        "query": user_input,
                        "k": k
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display assistant message
                    with st.chat_message("assistant"):
                        st.markdown(data.get("answer", "No answer generated."))
                        
                        # Show sources
                        if data.get("sources"):
                            with st.expander(f"📚 Sources ({len(data['sources'])})"):
                                for i, source in enumerate(data["sources"], 1):
                                    st.markdown(f"**Source [{i}]** (Score: {source.get('score', 0):.2f})")
                                    st.text(source.get("text", ""))
                        
                        # Show metrics
                        if data.get("metrics"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Retrieval Time",
                                    f"{data['metrics'].get('retrieval_time_ms', 0):.0f} ms"
                                )
                            with col2:
                                st.metric(
                                    "Response Time",
                                    f"{data['metrics'].get('response_time_ms', 0):.0f} ms"
                                )
                            with col3:
                                st.metric(
                                    "Chunks Retrieved",
                                    data['metrics'].get('num_chunks_retrieved', 0)
                                )
                    
                    # Add assistant message to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": data.get("answer", ""),
                        "sources": data.get("sources", []),
                        "metrics": data.get("metrics", {})
                    })
                    
                    # Rerun to update the display
                    st.rerun()
                    
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    st.error(f"Error: {error_msg}")
                    
            except requests.exceptions.Timeout:
                logger.error("Request timed out")
                st.error("Request timed out. Please try again.")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
                st.error(f"API URL: {API_BASE_URL}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                st.error(f"An error occurred: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")
                with st.expander("View full error details"):
                    st.code(traceback.format_exc())
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    # API health check
    with st.expander("🔧 API Status"):
        try:
            response = requests.get(f"{API_BASE_URL}/api/rag/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                st.success(f"✅ API is healthy")
                st.json(health)
            else:
                st.warning(f"⚠️ API returned status code: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Could not connect to API: {str(e)}")
