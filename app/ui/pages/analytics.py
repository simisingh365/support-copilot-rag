"""
Streamlit analytics page for the RAG Support System.

Provides:
- Overview metrics display
- Retrieval distribution chart
- System statistics
"""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the analytics page."""
    st.title("📊 Analytics Dashboard")
    st.markdown("View system performance metrics and usage statistics.")
    
    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        st.write("")
    
    # Fetch analytics overview
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/overview", timeout=10)
        
        if response.status_code == 200:
            analytics = response.json()
            
            # Main metrics
            st.subheader("📈 Query Performance")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Queries",
                    analytics.get("total_queries", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Avg Retrieval Time",
                    f"{analytics.get('avg_retrieval_time_ms', 0):.0f} ms",
                    delta=None
                )
            
            with col3:
                st.metric(
                    "Avg Response Time",
                    f"{analytics.get('avg_response_time_ms', 0):.0f} ms",
                    delta=None
                )
            
            # Total time metric
            st.metric(
                "Avg Total Time",
                f"{analytics.get('avg_total_time_ms', 0):.0f} ms",
                delta=None
            )
            
            st.divider()
            
            # Retrieval distribution
            retrieval_dist = analytics.get("retrieval_distribution", {})
            if retrieval_dist:
                st.subheader("🔍 Retrieval Method Distribution")
                
                # Create bar chart data
                methods = list(retrieval_dist.keys())
                counts = list(retrieval_dist.values())
                
                chart_data = {method: count for method, count in zip(methods, counts)}
                st.bar_chart(chart_data)
                
                # Display as table
                st.write("**Breakdown by Retrieval Method:**")
                for method, count in retrieval_dist.items():
                    percentage = (count / analytics.get("total_queries", 1)) * 100
                    st.write(f"- **{method}**: {count} queries ({percentage:.1f}%)")
            else:
                st.info("No retrieval method data available yet.")
            
            st.divider()
            
            # Queries per day
            queries_per_day = analytics.get("queries_per_day", {})
            if queries_per_day:
                st.subheader("📅 Queries Per Day")
                chart_data = {date: count for date, count in queries_per_day.items()}
                st.bar_chart(chart_data)
            else:
                st.info("No daily query data available yet.")
        
        else:
            st.error(f"Failed to fetch analytics. Status code: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    st.divider()
    
    # System statistics
    st.subheader("🗄️ System Statistics")
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Tickets", stats.get("tickets", 0))
            with col2:
                st.metric("Messages", stats.get("messages", 0))
            with col3:
                st.metric("Documents", stats.get("documents", 0))
            with col4:
                st.metric("Chunks", stats.get("chunks", 0))
            with col5:
                st.metric("Queries", stats.get("queries", 0))
        
        else:
            st.error(f"Failed to fetch system stats. Status code: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    st.divider()
    
    # Recent queries
    st.subheader("📝 Recent Queries")
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/queries?limit=10", timeout=10)
        
        if response.status_code == 200:
            queries = response.json()
            
            if not queries:
                st.info("No queries found yet.")
            else:
                for i, query in enumerate(queries, 1):
                    with st.expander(f"Query {i}: {query.get('query_text', 'N/A')[:50]}..."):
                        st.write(f"**Answer:** {query.get('answer', 'N/A')}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Retrieval Time", f"{query.get('retrieval_time_ms', 0):.0f} ms")
                        with col2:
                            st.metric("Response Time", f"{query.get('response_time_ms', 0):.0f} ms")
                        with col3:
                            st.metric("Chunks", query.get('num_chunks', 0))
                        st.caption(f"Created: {query.get('created_at', 'N/A')}")
        
        else:
            st.error(f"Failed to fetch recent queries. Status code: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
