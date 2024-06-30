import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from config import APP_MODE
from src.menu import initialize_menu_manager

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

def add_references_to_query(query: str):
    if st.session_state.file_handler.has_file_content():
        query = st.session_state.file_handler.write_file_content_to_query() + query
    return query

def handle_user_input():
    handle_chat_options()
    query = st.chat_input('Type a message')
    if query:
        if query.startswith('/'): # Toggle between chat and menu mode
            if st.session_state.app_mode == APP_MODE.CHAT:
                st.session_state.app_mode = APP_MODE.MENU
                initialize_menu_manager()
            else:
                st.session_state.app_mode = APP_MODE.CHAT
        else:
            if st.session_state.app_mode == APP_MODE.CHAT:
                """ 
                NOTE NOTE NOTE
                NOTE NOTE NOTE
                PROBLEM WITH LONG QUERIES CAUSING ERRORS

                MY QUESS IS TIME OUT OUR SOMETHING FUNKY GOING ON WITH ST.MARKDOWN TO WRITE USER MESSAGE
                THEN CALL TO HANDLE_CHAT
                NOTE NOTE NOTE
                NOTE NOTE NOTE
                """
                query = add_references_to_query(query)
                with st.chat_message('user'):
                    st.markdown(query)
                handle_chat(query)
            else:
                st.session_state.menu_manager.handle_selection(query)

#################################
##########   Chat  ##############
#################################
def handle_chat(query: str):
    if query:
        # Execute Query
        agent = st.session_state.agent_handler.active_agent
        response = asyncio.run(generate_and_display_response(agent, query))
        # Post Query
        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(response)

async def generate_and_display_response(agent, query: str):
    response = await agent.generate_response(query)
    with st.chat_message('assistant'):
        st.markdown(response)

    return response