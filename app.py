# Third-party libraries
import streamlit as st

# source imports
from src.initialization import handle_session_initialization
from src.ui_component import display_title, display_chat_history, display_system_messages
from src.chat_interface import handle_chat

# Define main application function
def main():
    # Initialization
    handle_session_initialization()
    # Handle rerender requests
    rerender_page_if_needed()
    # Display UI
    display_title()
    display_system_messages()
    display_chat_history()
    # Handle chat
    handle_chat()

# Function to rerender the page if needed
def rerender_page_if_needed():
    if st.session_state['rerender']:
        st.session_state['rerender'] = False
        # HEY YOU CAN ADD RERENDER LOGIC HERE IF NEEDED
        st.rerun()

# Main application entry point
if __name__ == "__main__":
    main()
