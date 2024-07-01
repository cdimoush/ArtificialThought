import streamlit as st
from config import ROLE_MAP

def display_title():
    """
    Displays the application title or any static content at the top of the page.
    """
    st.title('Artificial Thought Experiment')

def display_chat_history():
    """
    Displays the chat history in the Streamlit application.
    Uses the global ROLE_MAP to assign user-friendly names to message types.
    """
    # There's new message(s), update the display
    for message in st.session_state['memory_cache'].chat_memory.messages:
        # Using ROLE_MAP to get a user-friendly name for the message type
        message_role = ROLE_MAP.get(message.type, "Unknown")
        with st.chat_message(message_role):
            st.markdown(message.content)
        
def display_chat_history_old():
    """
    Displays the chat history in the Streamlit application.
    Uses the global ROLE_MAP to assign user-friendly names to message types.
    """
    # Retrieve the current history length
    current_history_length = len(st.session_state['memory_cache'].chat_memory.messages)
    
    # Check if there's a new message to display
    if 'last_displayed_length' not in st.session_state or st.session_state['last_displayed_length'] != current_history_length:
        # There's new message(s), update the display
        for message in st.session_state['memory_cache'].chat_memory.messages:
            # Using ROLE_MAP to get a user-friendly name for the message type
            message_role = ROLE_MAP.get(message.type, "Unknown")
            with st.chat_message(message_role):
                st.markdown(message.content)
        
        # Update the last displayed length in session state
        st.session_state['last_displayed_length'] = current_history_length

def display_system_messages():
    """
    Displays system messages, such as warnings or notifications, to the user.
    """
    if not st.session_state['initial_state']:
        st.warning('You have reached the end of current development...')