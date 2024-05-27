import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from config import APP_MODE
from src.menu import initialize_menu_manager

#################################
##########   UI  ################
#################################

def handle_chat_options() -> str:
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
    return selected_agent

def handle_user_input() -> str:
    selected_agent = handle_chat_options()
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
                with st.chat_message('user'):
                    st.markdown(query)
                handle_chat(selected_agent, query)
            else:
                st.session_state.menu_manager.handle_selection(query)

#################################
##########   Chat  ##############
#################################

def handle_chat(selected_agent: str, query: str):
    if query:
        agent = st.session_state.agent_handler.active_agent
        response = asyncio.run(generate_and_display_response(agent, query))

        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(response)

async def generate_and_display_response(agent, query: str):
    response = await agent.generate_response(query)
    with st.chat_message('assistant'):
        st.markdown(response)

    return response