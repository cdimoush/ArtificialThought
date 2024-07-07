import streamlit as st
from langchain.memory import ConversationBufferMemory
from src.agents import AgentHandler
from src.file_handler import FileHandler
from src.menu import initialize_menu_manager
from config import APP_MODE

def handle_session_initialization():
    """
    Initializes or resets the session state variables required for the application.
    If the initial state is not set, it initializes session variables and preloads an AI message.
    """
    if 'initial_state' not in st.session_state:
        st.session_state['rerender'] = False
        st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
        st.session_state['draft_cache'] = ''
        st.session_state['agent_handler'] = AgentHandler('config/agents.yaml')
        st.session_state['file_handler'] = FileHandler('config/dirs.yaml')
        st.session_state['initial_state'] = True
        st.session_state['app_mode'] = APP_MODE.DRAFT
        initialize_menu_manager()
