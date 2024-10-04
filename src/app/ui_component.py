import os
import streamlit as st
from config import ROLE_MAP
from streamlit_extras.bottom_container import bottom

def display_title():
    """
    Displays the application title or any static content at the top of the page.
    """
    st.title('Artificial Thought Experiment')

def display_system_messages():
    """
    Displays system messages, such as warnings or notifications, to the user.
    """
    if not st.session_state['initial_state']:
        st.warning('You have reached the end of current development...')

def display_chat_history():
    """
    Displays the chat history in the Streamlit application.
    Uses the global ROLE_MAP to assign user-friendly names to message types.
    """
    for message, info in st.session_state.memory_handler:
        role = ROLE_MAP.get(message.type, "Unknown")
        with st.chat_message(role):
            display_info(info)
            display_message(message)

def display_last_message(container = None):
    """
    Display the last message in the chat history.
    """
    if len(st.session_state.memory_handler) > 0:
        message, info = st.session_state.memory_handler[-1]
        role = ROLE_MAP.get(message.type, "Unknown")
        with container if container else st.chat_message(role):
            display_info(info, expanded=True)
            display_message(message)

def display_message(message, container=None):
    """
    Display the main body of the message.
    """
    container = container or st.container()
    with container:
        st.markdown(message.content)

def display_info(info, container=None, expanded=False):
    """
    Display additional information in expanders.
    """
    container = container or st.container()
    with container:
        if info:
            for key, value in info.items():
                with st.expander(key, expanded=expanded):
                    st.markdown(f"**{key}:**")
                    st.markdown(value)

def display_message_content(message, info, container=None, expanded=False):
    """
    Display the message content with optional expander for additional information.
    """
    container = container or st.container()
    with container:
        display_info(info, container, expanded)
        display_message(message, container)

def display_popover_menu():
    col1, col2, col3, _ = st.columns([1, 1, 1, 1], gap='small')
    with col1:
        with st.popover(f'Agent: {st.session_state.agent_handler.active_agent.title.upper()}', use_container_width=True):
            st.write(f'MODEL: ')
            st.write(st.session_state.agent_handler.active_agent.model)
            st.write(f'ROLE: ')
            st.write(st.session_state.agent_handler.active_agent.role)
    with col2:
        with st.popover('Load Files', use_container_width=True):
            uploaded_files = st.file_uploader("File Uploader", type=['py', 'txt', 'yaml'], accept_multiple_files=True)

            if uploaded_files is not None:
                for uploaded_file in uploaded_files:
                    write_path = os.path.join(st.session_state['temp_dir'], uploaded_file.name)
                    with open(write_path, 'wb') as f:
                        f.write(uploaded_file.read())
                        

def display_chat_interface():
    return st.chat_input('Type a message')
