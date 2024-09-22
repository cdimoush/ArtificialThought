# Third-party libraries
import streamlit as st
from streamlit_extras.bottom_container import bottom
import typer

# source imports
from src.app.initialization import handle_session_initialization
from src.app.ui_component import (display_title, 
                                  display_chat_history, 
                                  display_system_messages, 
                                  display_popover_menu,
                                  display_chat_interface
                                  )
from src.app.chat_interface import handle_chat

# Define main application function
def main():
    handle_session_initialization()
    # Setup Layout
    # ------------
    st.set_page_config(layout="wide")
    header = st.container()
    body = st.container()
    footer = bottom()

    # UI Components
    # ------------
    with header:
        display_title()
        display_system_messages()

    with body:
        display_chat_history()
    
    with footer:
        display_popover_menu()
        query = display_chat_interface()
        
    # Execution
    # ------------
    handle_chat(query, body)

# Main application entry point
if __name__ == "__main__":
    main()
