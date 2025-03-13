import streamlit as st
from datetime import datetime
import json

def init_session_state():
    """
    Initialize session state variables.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"conversation_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if "tools_config" not in st.session_state:
        st.session_state.tools_config = {
            "web_search": False,
            "file_search": False,
            "vector_store_id": "",
            "function_calling": False
        }

def add_message(role, content, metadata=None):
    """
    Add a message to the conversation history.
    
    Args:
        role: Role of the message (user or assistant)
        content: Content of the message
        metadata: Additional metadata for the message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = {
        "role": role,
        "content": content,
        "timestamp": timestamp
    }
    
    if metadata:
        message["metadata"] = metadata
    
    st.session_state.messages.append(message)

def get_messages_history():
    """
    Get the conversation history.
    
    Returns:
        list: List of messages
    """
    return st.session_state.messages

def clear_conversation():
    """
    Clear the conversation history.
    """
    st.session_state.messages = []
    st.session_state.conversation_id = f"conversation_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def save_conversation(filepath):
    """
    Save the conversation history to a file.
    
    Args:
        filepath: Path to save the file to
    """
    conversation_data = {
        "id": st.session_state.conversation_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": st.session_state.messages
    }
    
    try:
        with open(filepath, "w") as f:
            json.dump(conversation_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False

def load_conversation(filepath):
    """
    Load a conversation history from a file.
    
    Args:
        filepath: Path to load the file from
    """
    try:
        with open(filepath, "r") as f:
            conversation_data = json.load(f)
        
        st.session_state.conversation_id = conversation_data.get("id", st.session_state.conversation_id)
        st.session_state.messages = conversation_data.get("messages", [])
        return True
    except Exception as e:
        print(f"Error loading conversation: {e}")
        return False
