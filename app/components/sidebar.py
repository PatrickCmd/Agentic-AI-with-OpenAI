import streamlit as st
import os
import tempfile
from utils.vectorstore_utils import create_vector_store, upload_files_to_vector_store, get_vector_store_details
from utils.conversation_utils import clear_conversation
from utils.prompts import DEVELOPER_PROMPT

def render_sidebar():
    """
    Render the sidebar with toggleable features.
    
    Returns:
        dict: Tools configuration
    """
    st.sidebar.title("📚 RAG AI Assistant")
    
    # API Key Configuration
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", placeholder="Enter your OpenAI API key", 
                                   value=os.environ.get("OPENAI_API_KEY", ""))
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Model Selection
    model = st.sidebar.selectbox(
        "Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], 
        index=0
    )
    
    # Clear conversation
    if st.sidebar.button("Clear Conversation"):
        clear_conversation()
        st.sidebar.success("Conversation cleared!")
    
    # Tools Configuration
    st.sidebar.header("Tool Configuration")
    
    # Web Search
    web_search_enabled = st.sidebar.checkbox("Enable Web Search", value=st.session_state.tools_config.get("web_search", False))
    
    # File Search
    file_search_enabled = st.sidebar.checkbox("Enable File Search", value=st.session_state.tools_config.get("file_search", False))
    
    vector_store_id = ""
    if file_search_enabled:
        st.sidebar.subheader("File Search Configuration")
        
        # Vector Store ID
        vector_store_id = st.sidebar.text_input(
            "Vector Store ID", 
            value=st.session_state.tools_config.get("vector_store_id", ""),
            help="Enter an existing Vector Store ID or create a new one below"
        )
        
        # Create Vector Store
        with st.sidebar.expander("Create New Vector Store"):
            new_store_name = st.text_input("Vector Store Name", placeholder="Enter a name for your vector store")
            if st.button("Create Vector Store"):
                if new_store_name:
                    with st.spinner("Creating vector store..."):
                        store_details = create_vector_store(new_store_name)
                        if store_details:
                            vector_store_id = store_details.get("id", "")
                            st.success(f"Vector Store created: {vector_store_id}")
                        else:
                            st.error("Failed to create vector store")
                else:
                    st.warning("Please enter a name for your vector store")
        
        # Upload Files to Vector Store
        if vector_store_id:
            with st.sidebar.expander("Upload Files to Vector Store"):
                uploaded_files = st.file_uploader(
                    "Upload files to vector store", 
                    type=["pdf", "txt", "md", "docx"],
                    accept_multiple_files=True
                )
                
                if uploaded_files and st.button("Upload Files"):
                    with st.spinner("Uploading files..."):
                        temp_dir = tempfile.mkdtemp()
                        file_paths = []
                        
                        for uploaded_file in uploaded_files:
                            file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_paths.append(file_path)
                        
                        if file_paths:
                            stats = upload_files_to_vector_store(file_paths, vector_store_id)
                            if stats["successful_uploads"] > 0:
                                st.success(f"Successfully uploaded {stats['successful_uploads']} files")
                            if stats["failed_uploads"] > 0:
                                st.error(f"Failed to upload {stats['failed_uploads']} files")
            
            # Vector Store Info
            with st.sidebar.expander("Vector Store Info"):
                if st.button("Get Vector Store Info"):
                    with st.spinner("Getting vector store info..."):
                        store_info = get_vector_store_details(vector_store_id)
                        if store_info:
                            st.write(f"Name: {store_info.get('name')}")
                            st.write(f"Files: {store_info.get('file_count')}")
                            st.write(f"Created: {store_info.get('created_at')}")
                        else:
                            st.error("Failed to get vector store info")
    
    # Function Calling
    function_calling_enabled = st.sidebar.checkbox(
        "Enable Function Calling (e.g., Weather)", 
        value=st.session_state.tools_config.get("function_calling", False)
    )
    
    # Developer Information
    with st.sidebar.expander("Developer Information"):
        st.subheader("AI System Prompt")
        st.code(DEVELOPER_PROMPT, language="markdown")
    
    # Update tools config in session state
    tools_config = {
        "web_search": web_search_enabled,
        "file_search": file_search_enabled,
        "vector_store_id": vector_store_id,
        "function_calling": function_calling_enabled,
        "model": model
    }
    
    st.session_state.tools_config = tools_config
    
    return tools_config
