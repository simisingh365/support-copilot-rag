"""
Streamlit tickets page for the RAG Support System.

Provides:
- Create new support tickets
- List and view existing tickets
- Add messages to tickets
- Update ticket status
"""

import streamlit as st
import requests
import uuid

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the tickets page."""
    st.title("🎫 Support Tickets")
    st.markdown("Manage customer support tickets and track conversations.")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Create Ticket", "View Tickets"])
    
    # Tab 1: Create Ticket
    with tab1:
        st.subheader("📝 Create New Ticket")
        st.markdown("Submit a new support ticket for assistance.")
        
        with st.form("create_ticket"):
            subject = st.text_input(
                "Subject *",
                placeholder="Brief description of the issue"
            )
            content = st.text_area(
                "Description *",
                placeholder="Provide detailed information about your issue...",
                height=150
            )
            priority = st.selectbox(
                "Priority",
                ["LOW", "MEDIUM", "HIGH", "URGENT"],
                index=1
            )
            customer_id = st.text_input(
                "Customer ID (Optional)",
                placeholder="Your customer ID"
            )
            
            submitted = st.form_submit_button("🎫 Create Ticket", type="primary")
            
            if submitted:
                if not subject or not subject.strip():
                    st.error("Subject is required.")
                    return
                
                if not content or not content.strip():
                    st.error("Description is required.")
                    return
                
                # Prepare request
                request_data = {
                    "subject": subject.strip(),
                    "content": content.strip(),
                    "priority": priority,
                    "customer_id": customer_id.strip() if customer_id.strip() else None
                }
                
                # Show loading spinner
                with st.spinner("Creating ticket..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/tickets/",
                            json=request_data,
                            timeout=10
                        )
                        
                        if response.status_code == 201:
                            data = response.json()
                            st.success(f"✅ Ticket created successfully!")
                            st.info(f"Ticket ID: `{data.get('id')}`")
                            st.metric("Priority", data.get("priority"))
                            st.text_area(
                                "Subject",
                                value=data.get("subject"),
                                disabled=True
                            )
                            st.text_area(
                                "Description",
                                value=data.get("content"),
                                disabled=True
                            )
                        else:
                            error_msg = response.json().get("detail", "Unknown error")
                            st.error(f"Error: {error_msg}")
                    
                    except requests.exceptions.Timeout:
                        st.error("Request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
    
    # Tab 2: View Tickets
    with tab2:
        st.subheader("📋 All Tickets")
        st.markdown("View and manage existing support tickets.")
        
        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        # Fetch tickets
        try:
            response = requests.get(f"{API_BASE_URL}/api/tickets/", timeout=10)
            
            if response.status_code == 200:
                tickets = response.json()
                
                if not tickets:
                    st.info("📭 No tickets found. Create a ticket to get started!")
                else:
                    # Priority badge helper
                    def get_priority_color(priority):
                        if priority == "URGENT":
                            return "🔴"
                        elif priority == "HIGH":
                            return "🟠"
                        elif priority == "MEDIUM":
                            return "🟡"
                        else:
                            return "🟢"
                    
                    def get_status_color(status):
                        if status == "OPEN":
                            return "🟢"
                        elif status == "IN_PROGRESS":
                            return "🟡"
                        elif status == "RESOLVED":
                            return "🔵"
                        else:
                            return "⚫"
                    
                    # Display tickets
                    for ticket in tickets:
                        priority_badge = get_priority_color(ticket.get("priority", ""))
                        status_badge = get_status_color(ticket.get("status", ""))
                        
                        with st.expander(f"{priority_badge} {status_badge} {ticket.get('subject', 'N/A')}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.text_input(
                                    "Status",
                                    value=ticket.get("status", "N/A"),
                                    disabled=True
                                )
                            with col2:
                                st.text_input(
                                    "Priority",
                                    value=ticket.get("priority", "N/A"),
                                    disabled=True
                                )
                            with col3:
                                st.text_input(
                                    "Customer ID",
                                    value=ticket.get("customer_id", "N/A") or "N/A",
                                    disabled=True
                                )
                            
                            st.text_area(
                                "Description",
                                value=ticket.get("content", "N/A"),
                                disabled=True,
                                height=100
                            )
                            
                            st.caption(f"Created: {ticket.get('created_at', 'N/A')}")
                            st.caption(f"Updated: {ticket.get('updated_at', 'N/A')}")
                            
                            # Ticket actions
                            st.markdown("---")
                            st.subheader("💬 Messages")
                            
                            # Fetch messages for this ticket
                            try:
                                msg_response = requests.get(
                                    f"{API_BASE_URL}/api/tickets/{ticket.get('id')}/messages",
                                    timeout=5
                                )
                                
                                if msg_response.status_code == 200:
                                    messages = msg_response.json()
                                    
                                    if not messages:
                                        st.info("No messages yet.")
                                    else:
                                        for msg in messages:
                                            role_emoji = "👤" if msg.get("role") == "USER" else "🤖" if msg.get("role") == "ASSISTANT" else "⚙️"
                                            st.markdown(f"**{role_emoji} {msg.get('role', 'N/A')}**: {msg.get('content', 'N/A')}")
                                            st.caption(f"  {msg.get('created_at', 'N/A')}")
                                else:
                                    st.warning("Could not fetch messages.")
                            except Exception as e:
                                st.warning(f"Could not fetch messages: {str(e)}")
                            
                            # Add message form
                            st.markdown("#### Add Message")
                            with st.form(f"add_message_{ticket.get('id')}"):
                                message_content = st.text_area(
                                    "Message",
                                    placeholder="Enter your response...",
                                    height=80
                                )
                                message_role = st.selectbox(
                                    "Role",
                                    ["USER", "ASSISTANT", "SYSTEM"],
                                    index=0
                                )
                                msg_submitted = st.form_submit_button("📤 Send Message")
                                
                                if msg_submitted and message_content:
                                    try:
                                        msg_response = requests.post(
                                            f"{API_BASE_URL}/api/tickets/{ticket.get('id')}/messages",
                                            json={
                                                "content": message_content,
                                                "role": message_role
                                            },
                                            timeout=10
                                        )
                                        
                                        if msg_response.status_code == 201:
                                            st.success("Message added!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to add message.")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            # Update status
                            st.markdown("#### Update Status")
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                new_status = st.selectbox(
                                    "New Status",
                                    ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"],
                                    index=["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"].index(ticket.get("status", "OPEN")) if ticket.get("status") in ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"] else 0
                                )
                            with col2:
                                if st.button("🔄 Update", key=f"update_{ticket.get('id')}", use_container_width=True):
                                    try:
                                        status_response = requests.patch(
                                            f"{API_BASE_URL}/api/tickets/{ticket.get('id')}/status",
                                            params={"status": new_status},
                                            timeout=10
                                        )
                                        
                                        if status_response.status_code == 200:
                                            st.success("Status updated!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to update status.")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            
            else:
                st.error(f"Failed to fetch tickets. Status code: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Please make sure the FastAPI server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
