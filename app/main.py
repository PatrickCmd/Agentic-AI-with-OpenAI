import streamlit as st
import os
from components.sidebar import render_sidebar
from components.chat_interface import render_chat_interface
from utils.conversation_utils import init_session_state

def main():
    # Set page config
    st.set_page_config(
        page_title="RAG Agentic AI with OpenAI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Apply custom CSS
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Render sidebar
    tools_config = render_sidebar()
    
    # Main content area
    st.header("🤖 RAG Agentic AI Assistant")
    
    # Render chat interface
    render_chat_interface(tools_config)

if __name__ == "__main__":
    main()
