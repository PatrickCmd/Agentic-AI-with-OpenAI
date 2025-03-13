import streamlit as st
from utils.conversation_utils import add_message, get_messages_history
from utils.api_utils import chat_completion, use_tool_response, get_weather
from utils.prompts import SYSTEM_MESSAGE
import time
import re

def extract_location(text):
    """
    Extract a location from text, particularly for weather queries.
    
    Args:
        text: Input text containing a potential location
        
    Returns:
        str: Extracted location or empty string if none found
    """
    # Convert to lowercase for easier pattern matching
    text = text.lower().strip()
    
    # Define patterns to match common weather query formats
    patterns = [
        # Pattern for "weather in X"
        r"(?:weather|temperature|forecast)(?:\s+in|\s+for|\s+at)?\s+([\w\s,]+)(?:\?|\.)?$",
        # Pattern for "what is the weather/temperature in X"
        r"(?:what(?:'s| is)?\s+the\s+(?:weather|temperature|forecast|climate))(?:\s+(?:like|going to be|for))?\s+(?:in|at|for)\s+([\w\s,]+)(?:\?|\.)?$",
        # Pattern for "how is the weather in X"
        r"how(?:'s| is)?\s+the\s+(?:weather|temperature)(?:\s+(?:like|going to be))?\s+(?:in|at|for)\s+([\w\s,]+)(?:\?|\.)?$",
        # Pattern for "current weather in X"
        r"(?:current|today(?:'s)?)\s+(?:weather|temperature|forecast)(?:\s+(?:in|at|for))?\s+([\w\s,]+)(?:\?|\.)?$",
        # Direct location with weather terms
        r"([\w\s,]+)\s+(?:weather|temperature|forecast|climate)(?:\?|\.)?$"
    ]
    
    # Try to match location using the patterns
    for pattern in patterns:
        matches = re.search(pattern, text)
        if matches:
            location = matches.group(1).strip()
            # Clean up punctuation and extra spaces
            location = re.sub(r'[?!.,]$', '', location).strip()
            return location
    
    # If no pattern matched, use a fallback method to extract location
    # Remove common phrases
    common_phrases = [
        "what is the current", "what's the current", "what is the", "what's the",
        "how is the", "how's the", "current", "today's", "today", 
        "weather in", "weather for", "weather at", "weather",
        "temperature in", "temperature for", "temperature at", "temperature",
        "forecast in", "forecast for", "forecast at", "forecast",
        "climate in", "climate for", "climate at", "climate",
        "like in", "like at", "going to be in"
    ]
    
    # Sort by length (descending) to remove longest phrases first
    common_phrases.sort(key=len, reverse=True)
    
    location_text = text
    for phrase in common_phrases:
        location_text = location_text.replace(phrase, "").strip()
    
    # Clean up the result
    location_text = re.sub(r'[?!.,]$', '', location_text).strip()
    
    return location_text

def render_chat_interface(tools_config):
    """
    Render the chat interface with message display and user input handling.
    
    Args:
        tools_config: Dictionary of enabled tools
    """
    # Display chat messages
    messages = get_messages_history()
    
    # Display welcome message if it's a new conversation
    if not messages:
        with st.chat_message("assistant"):
            st.markdown("👋 Hello! " + SYSTEM_MESSAGE)
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show source files if available
            if message["role"] == "assistant" and "metadata" in message and "source_files" in message["metadata"]:
                source_files = message["metadata"]["source_files"]
                if source_files:
                    with st.expander("Sources"):
                        for file in sorted(source_files):
                            st.write(f"- {file}")
    
    # User input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Add user message to history
        add_message("user", user_input)
        
        # Get model response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Check if this might be a weather query
                is_weather_query = any(keyword in user_input.lower() for keyword in ["weather", "temperature", "forecast", "climate"])
                
                # Special case for weather function - try to handle in different ways
                if tools_config.get("function_calling") and is_weather_query:
                    # First try with direct location extraction
                    location = extract_location(user_input)
                    
                    if location and len(location) > 1:  # Ensure location is not empty or too short
                        # Try to get weather with the extracted location
                        try:
                            response_text = get_weather(location)
                            metadata = {"function": "weather", "location": location}
                        except Exception as e:
                            # If direct extraction fails, fallback to using the tool response system
                            print(f"Direct weather extraction failed: {e}")
                            response_text, metadata = use_tool_response(
                                user_input, 
                                tools_config,
                                model=tools_config.get("model", "gpt-4o")
                            )
                    else:
                        # If no location found, use normal tool response
                        response_text, metadata = use_tool_response(
                            user_input, 
                            tools_config,
                            model=tools_config.get("model", "gpt-4o")
                        )
                # If tools are enabled, use them
                elif any([tools_config.get("web_search"), 
                       tools_config.get("file_search") and tools_config.get("vector_store_id"),
                       tools_config.get("function_calling")]):
                    # Use tools to get response
                    response_text, metadata = use_tool_response(
                        user_input, 
                        tools_config,
                        model=tools_config.get("model", "gpt-4o")
                    )
                else:
                    # Just use plain chat completion
                    response_text = chat_completion(
                        user_input,
                        model=tools_config.get("model", "gpt-4o")
                    )
                    metadata = {}
                
                # Display the response with a typing effect
                full_response = ""
                for chunk in response_text.split():
                    full_response += chunk + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)
                
                # Final update without cursor
                message_placeholder.markdown(response_text)
                
                # Show source files if available
                if "source_files" in metadata and metadata["source_files"]:
                    with st.expander("Sources"):
                        for file in sorted(metadata["source_files"]):
                            st.write(f"- {file}")
                
                # Add assistant message to history
                add_message("assistant", response_text, metadata)
                
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.markdown(error_message)
                add_message("assistant", error_message)
