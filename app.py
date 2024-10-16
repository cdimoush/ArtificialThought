# Third-party libraries
import streamlit as st
from streamlit_extras.bottom_container import bottom
import typer

# source imports
from src.app.initialization import handle_session_initialization
from src.app.ui_component import (display_title, 
                                  display_chat_history, 
                                  display_system_messages, 
                                  display_menu_button,
                                  display_chat_interface
                                  )
from src.app.chat_interface import handle_chat

# Define main application function
def main():
    st.set_page_config(layout="wide")
    handle_session_initialization()

    # Header
    # ------------
    header = st.container()
    with header:
        display_title()
        display_system_messages()

    # Tabs
    # ------------
    tab_chat, tab_dashboard, tab_about = st.tabs(['Chat', 'Dashboard', 'About'])

    # Chat Tab
    # ------------
    with tab_chat:
        body = st.container()
        footer = bottom()

        # UI Components
        # ------------
        with body:
            display_chat_history()
        
        with footer:
            footer_1, footer_2 = st.columns([1, 5], gap='small')
            with footer_1:
                display_menu_button()
            with footer_2:
                query = display_chat_interface()
                
        # Execution
        # ------------
        handle_chat(query, body)

# Main application entry point
if __name__ == "__main__":
    main()
