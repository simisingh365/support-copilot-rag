"""
Streamlit knowledge page for the RAG Support System.

Provides:
- Add Document tab for ingesting new documents
- View Documents tab for listing existing documents
"""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the knowledge page."""
    st.title("📚 Knowledge Base")
    st.markdown("Manage documents in the knowledge base for RAG retrieval.")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Add Document", "View Documents"])
    
    # Tab 1: Add Document
    with tab1:
        st.subheader("📄 Ingest New Document")
        st.markdown("Add a new document to the knowledge base. The document will be chunked and indexed for retrieval.")
        
        with st.form("ingest_document"):
            title = st.text_input("Document Title *", placeholder="Enter document title")
            content = st.text_area(
                "Document Content *",
                placeholder="Enter document content...",
                height=300
            )
            category = st.text_input("Category (Optional)", placeholder="e.g., Policies, FAQ, Guides")
            tags_input = st.text_input(
                "Tags (Optional)",
                placeholder="Comma-separated tags, e.g., refund, policy, billing"
            )
            chunking_strategy = st.selectbox(
                "Chunking Strategy",
                ["fixed_size", "semantic"],
                help="fixed_size: Fixed 512-character chunks with overlap\nsemantic: Paragraph-based chunks"
            )
            
            submitted = st.form_submit_button("📥 Ingest Document", type="primary")
            
            if submitted:
                if not title or not title.strip():
                    st.error("Document title is required.")
                    return
                
                if not content or not content.strip():
                    st.error("Document content is required.")
                    return
                
                # Parse tags
                tags = None
                if tags_input and tags_input.strip():
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                
                # Prepare request
                request_data = {
                    "title": title.strip(),
                    "content": content.strip(),
                    "category": category.strip() if category else None,
                    "tags": tags,
                    "chunking_strategy": chunking_strategy
                }
                
                # Show loading spinner
                with st.spinner("Ingesting document... This may take a moment."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/knowledge/ingest",
                            json=request_data,
                            timeout=60
                        )
                        
                        if response.status_code == 201:
                            data = response.json()
                            st.success(f"✅ {data.get('message', 'Document ingested successfully!')}")
                            st.info(f"Document ID: `{data.get('document_id')}`")
                            st.metric("Chunks Created", data.get("chunks_count", 0))
                        else:
                            error_msg = response.json().get("detail", "Unknown error")
                            st.error(f"Error: {error_msg}")
                    
                    except requests.exceptions.Timeout:
                        st.error("Request timed out. The document may be too large or the server is busy.")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
    
    # Tab 2: View Documents
    with tab2:
        st.subheader("📋 All Documents")
        st.markdown("View all documents in the knowledge base.")
        
        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        # Fetch documents
        try:
            response = requests.get(f"{API_BASE_URL}/api/knowledge/documents", timeout=10)
            
            if response.status_code == 200:
                documents = response.json()
                
                if not documents:
                    st.info("📭 No documents found in the knowledge base. Add some documents to get started!")
                else:
                    # Display documents
                    for doc in documents:
                        with st.expander(f"📄 {doc['title']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Chunks", doc.get("chunk_count", 0))
                            with col2:
                                st.text_input("Category", doc.get("category", "N/A"), disabled=True)
                            with col3:
                                st.text_input("ID", doc.get("id", "N/A")[:20] + "...", disabled=True)
                            
                            if doc.get("tags"):
                                st.markdown("**Tags:** " + ", ".join(doc["tags"]))
                            
                            st.caption(f"Created: {doc.get('created_at', 'N/A')}")
                            st.caption(f"Updated: {doc.get('updated_at', 'N/A')}")
                            
                            # Delete button
                            if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}", use_container_width=True):
                                try:
                                    delete_response = requests.delete(
                                        f"{API_BASE_URL}/api/knowledge/documents/{doc['id']}",
                                        timeout=10
                                    )
                                    if delete_response.status_code == 200:
                                        st.success("Document deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete document.")
                                except Exception as e:
                                    st.error(f"Error deleting document: {str(e)}")
            else:
                st.error(f"Failed to fetch documents. Status code: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
