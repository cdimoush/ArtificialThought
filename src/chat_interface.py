import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from config import APP_MODE
from src.menu import initialize_menu_manager
import typer

#################################
##########   UI  ################
#################################

def handle_chat_options():
    with bottom():
        (col1, col2) = st.columns(2)
        with col1:
            with st.popover('Options'):
                # Fetch the current active agent title for display or selection
                current_agent_title = st.session_state.agent_handler.active_agent.title if st.session_state.agent_handler.active_agent else None
                selected_agent = st.selectbox('Agent Role', st.session_state.agent_handler.agent_titles, index=st.session_state.agent_handler.agent_titles.index(current_agent_title) if current_agent_title in st.session_state.agent_handler.agent_titles else 0)
                # Update the active agent based on selection
                if selected_agent != current_agent_title:
                    st.session_state.agent_handler.active_agent = selected_agent
        with col2:
            st.write('[MICROPHONE PLACEHOLDER]')



#################################
##########   Query ##############
#################################

def add_references_to_query(query: str):
    if st.session_state.file_handler.has_file_content():
        query = st.session_state.file_handler.write_file_content_to_query() + query
    return query

def handle_query(query: str):
    query = add_references_to_query(query)
    with st.chat_message('user'):
        st.markdown(query)


#################################
##########   Response  ##########
#################################

def handle_response(query: str):
    with st.chat_message('assistant'):
        agent = st.session_state.agent_handler.active_agent
        response = agent.generate_response(query, st.empty())
        st.session_state.memory_cache.chat_memory.add_ai_message(response)

#################################
##########   Main  ##############
#################################

def handle_chat():
    # UI
    handle_chat_options()
    query = st.chat_input('Type a message')

    # QUERY
    if st.session_state.app_mode == APP_MODE.QUERY:
        if query:
            if query.startswith('/'): # Menu Toggle
                st.session_state.app_mode = APP_MODE.MENU
                initialize_menu_manager()
            else: 
                st.session_state.app_mode = APP_MODE.RESPONSE
                st.session_state.memory_cache.chat_memory.add_user_message(query)
                handle_query(query)

            query = None

    # RESPONSE
    if st.session_state.app_mode == APP_MODE.RESPONSE:
        st.session_state.app_mode = APP_MODE.QUERY
        handle_response(st.session_state.memory_cache.chat_memory.messages[-1])

    # MENU
    if st.session_state.app_mode == APP_MODE.MENU:
        if query:
            if query.startswith('/'): # Menu Toggle
                st.session_state.app_mode = APP_MODE.QUERY
            else:
                st.session_state.menu_manager.handle_selection(query)
