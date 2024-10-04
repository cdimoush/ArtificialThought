import streamlit as st
from langchain.memory import ConversationBufferMemory
import tempfile
import typer

from config import APP_MODE
from src.utils.file_handler import FileHandler
from src.agents.agent_handler import AgentHandler
from src.menus.agent_menu import AgentMenu, ModelMenu
from src.menus.file_menu import FolderMenu 
from src.menus.menu import MenuManager, Menu, SimpleMenuMethods
from src.utils.memory_handler import MemoryHandler

def handle_session_initialization():
    """
    Initializes or resets the session state variables required for the application.
    If the initial state is not set, it initializes session variables and preloads an AI message.
    """
    if 'initial_state' not in st.session_state:
        typer.secho('Initializing Session State...', fg=typer.colors.GREEN)
        st.session_state['initial_state'] = True
        st.session_state['app_mode'] = APP_MODE.QUERY
        st.session_state['temp_dir'] = tempfile.mkdtemp()
        st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
        st.session_state['memory_handler'] = MemoryHandler(st.session_state.memory_cache)
        st.session_state['agent_handler'] = AgentHandler('config/agents.yaml')
        st.session_state['file_handler'] = FileHandler('config/dirs.yaml')
        initialize_menu_manager()

def initialize_menus():
    main_menu_options = {
        "Select Agent": AgentMenu(st.session_state.agent_handler),
        "Change Model": ModelMenu(st.session_state.agent_handler),
        "Load File": FolderMenu(st.session_state.file_handler),
        "Clear Memory Cache": SimpleMenuMethods.clear_memory_cache,
    }
    main_menu = Menu("Main Menu", main_menu_options)
    menu_manager = MenuManager(main_menu)
    return menu_manager

def initialize_menu_manager():
    st.session_state['menu_manager'] = initialize_menus()