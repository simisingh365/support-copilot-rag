"""
Streamlit main application for the RAG Support System.

Provides:
- Main app with page navigation
- Integration with chat, knowledge, and analytics pages
"""

import streamlit as st
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging to show errors in Streamlit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="RAG Support System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff00;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stApp {
        background-color: #000000;
    }
    /* Improve text contrast - white text on black background */
    .stMarkdown, .stText, .stWrite, .stCaption {
        color: #ffffff !important;
    }
    /* Headers with green color */
    h1, h2, h3, h4, h5, h6 {
        color: #00ff00 !important;
    }
    /* Sidebar styling - dark gray */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #1a1a1a;
    }
    /* Sidebar text - white */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stText {
        color: #ffffff !important;
    }
    /* Buttons - green for primary, red for secondary */
    .stButton > button {
        background-color: #00ff00 !important;
        color: #000000 !important;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #00cc00 !important;
    }
    /* Input fields - dark background with white text */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #00ff00;
    }
    /* Radio buttons - white text */
    .stRadio label {
        color: #ffffff !important;
    }
    /* Success messages - green */
    .stSuccess {
        background-color: #003300 !important;
        color: #00ff00 !important;
    }
    /* Error messages - red */
    .stError {
        background-color: #330000 !important;
        color: #ff0000 !important;
    }
    /* Info messages - white text */
    .stInfo {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    /* Warning messages - yellow text */
    .stWarning {
        background-color: #332200 !important;
        color: #ffff00 !important;
    }
    /* Links - red */
    a {
        color: #ff0000 !important;
    }
    a:hover {
        color: #ff3333 !important;
    }
    /* Code blocks - dark background */
    .stCode {
        background-color: #1a1a1a !important;
        color: #00ff00 !important;
    }
    /* Dataframes - dark background with white text */
    .stDataFrame {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    .stDataFrame th {
        background-color: #003300 !important;
        color: #00ff00 !important;
    }
    /* Metrics - green text */
    .stMetric {
        color: #00ff00 !important;
    }
    /* Progress bar - green */
    .stProgress > div > div > div > div {
        background-color: #00ff00 !important;
    }
    /* Checkbox labels - white */
    .stCheckbox label {
        color: #ffffff !important;
    }
    /* Slider - green */
    .stSlider > div > div > div {
        background-color: #00ff00 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🤖 RAG Support System</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Chat", "Knowledge Base", "Tickets", "Analytics"],
    label_visibility="collapsed"
)

# Page routing
try:
    if page == "Chat":
        from app.ui.pages import chat
        chat.render()
    elif page == "Knowledge Base":
        from app.ui.pages import knowledge
        knowledge.render()
    elif page == "Tickets":
        from app.ui.pages import tickets
        tickets.render()
    elif page == "Analytics":
        from app.ui.pages import analytics
        analytics.render()
except ImportError as e:
    logger.error(f"Import error: {e}", exc_info=True)
    st.error(f"Error importing page module: {e}")
    st.info("Please ensure all page modules are properly installed.")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    st.error(f"An error occurred: {e}")
    st.error(f"Error type: {type(e).__name__}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #ffffff; font-size: 0.9rem;'>
        RAG Support System | Powered by FastAPI, ChromaDB & OpenAI
    </div>
    """,
    unsafe_allow_html=True
)
