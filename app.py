# Third-party libraries
import streamlit as st
import typer

# source imports
from src.app.initialization import handle_session_initialization
from src.app.ui_component import display_title, display_chat_history, display_system_messages
from src.app.chat_interface import handle_chat
from config import APP_MODE

# Define main application function
def main():
    # Setup Layout
    # ------------
    typer.secho(f'Running Loop! Mode: {st.session_state.app_mode}', fg=typer.colors.RED)
    st.set_page_config(layout="wide")
    header = st.container()

    if st.session_state.app_mode == APP_MODE.DRAFT:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['col1'] = st.container()
        with col2:
            st.session_state['col2'] = st.container()
    else:
        st.session_state['col1'] = st.container()
        st.session_state['col2'] = None

    # Handle rerender requests
    # ------------
    rerender_page_if_needed()

    # Display UI
    # ------------
    with header:
        display_title()
        display_system_messages()
    display_chat_history()

    # Handle chat
    # ------------
    handle_chat()

# Function to rerender the page if needed
def rerender_page_if_needed():
    if st.session_state['rerender']:
        st.session_state['rerender'] = False
        # HEY YOU CAN ADD RERENDER LOGIC HERE IF NEEDED
        st.rerun()

# Main application entry point
if __name__ == "__main__":
    handle_session_initialization()
    main()
