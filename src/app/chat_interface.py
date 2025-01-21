import streamlit as st
from src.app.ui_component import display_last_message
import os
from config import APP_MODE
import typer
import time

def add_references_to_query(query: str):
    """
    Add references to the query if the file handler has file content.
    """
    if st.session_state.file_handler.has_file_content():
        query = st.session_state.file_handler.write_file_content_to_query() + query
    return query

def handle_query(query, body):
    """
    Add references then display the query.
    """
    query = add_references_to_query(query)    
    st.session_state.memory_handler.add_user_message(query, {})
    with body:
        display_last_message()

    return query

def handle_response(query, body):
    """
    Generate a response using the active agent and display it.
    """
    agent = st.session_state.agent_handler.active_agent
    st.session_state.memory_handler.add_ai_message('', {})
    with body:
        with st.chat_message('assistant'):
            response = agent.generate_response(query)

    return response

def handle_chat(query, body):
    """
    Handle the chat interface.
    """
    # if st.session_state.app_mode == APP_MODE.QUERY:
    if query:
        if query == '/': # Menu Toggle
            st.session_state.menu_manager.display_menu_as_dialog()
        else:
            query = handle_query(query, body)
            response = handle_response(query, body)
            # handle_memory(query, response)
        query = None
