import streamlit as st
from streamlit_extras.bottom_container import bottom
from config import APP_MODE
from src.menu import initialize_menu_manager
import typer

#################################
##########   UI  ################
#################################

def display_agent_popover():
    with bottom():
        (col1, col2) = st.columns(2)
        with col1:
            with st.popover(f'Agent: {st.session_state.agent_handler.active_agent.title.upper()}'):
                st.write(f'MODEL: ')
                st.write(st.session_state.agent_handler.active_agent.model)
                st.write(f'ROLE: ')
                st.write(st.session_state.agent_handler.active_agent.role)

#################################
##########   Query ##############
#################################

def add_references_to_query(query: str):
    if st.session_state.file_handler.has_file_content():
        query = st.session_state.file_handler.write_file_content_to_query() + query
    return query

def handle_query():
    query = add_references_to_query(st.session_state.draft_cache)
    st.session_state.memory_cache.chat_memory.add_user_message(query)
    with st.session_state['col1']:
        with st.chat_message('user'):
            st.markdown(query)
    st.session_state.draft_cache = ''

#################################
##########   Response  ##########
#################################

def handle_response(query: str):
    with st.session_state['col1']:
        with st.chat_message('assistant'):
            agent = st.session_state.agent_handler.active_agent
            response = agent.generate_response(query, st.empty())
            st.session_state.memory_cache.chat_memory.add_ai_message(response)

#################################
##########    Draft    ##########
#################################

def handle_draft_area():
    st.session_state.draft_cache = st.session_state.draft_area

#################################
##########   Main  ##############
#################################

def handle_chat():
    # UI
    display_agent_popover()
    query = st.chat_input('Type a message')

    # QUERY (REMINDER: Not currently using this mode.)
    if st.session_state.app_mode == APP_MODE.QUERY:
        if query:
            st.session_state.app_mode = APP_MODE.RESPONSE
            handle_query(query)
            query = None

    # DRAFT
    if st.session_state.app_mode == APP_MODE.DRAFT:
        with st.session_state['col2']:
            draft_container = st.empty()
        if query:
            if query == '/': # Menu Toggle
                st.session_state.menu_manager.display_menu_as_dialog()
            elif query == '.': # Response
                st.session_state.app_mode = APP_MODE.RESPONSE
                handle_query()
            else:
                st.session_state.draft_cache += '\n' + query
        draft_container.text_area("Draft:", st.session_state.draft_cache, height=450, label_visibility='collapsed', on_change=handle_draft_area, key='draft_area')
                    
    # RESPONSE
    if st.session_state.app_mode == APP_MODE.RESPONSE:
        st.session_state.app_mode = APP_MODE.DRAFT
        handle_response(st.session_state.memory_cache.chat_memory.messages[-1])