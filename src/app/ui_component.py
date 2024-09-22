import os
import streamlit as st
from config import ROLE_MAP
from _pinecone_module.pinecone_upload_client import save_conversation
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
    # There's new message(s), update the display
    for message in st.session_state['memory_cache'].chat_memory.messages:
        # Using ROLE_MAP to get a user-friendly name for the message type
        message_role = ROLE_MAP.get(message.type, "Unknown")
        with st.chat_message(message_role):
            st.markdown(message.content)

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
                        
    with col3:
        st.button('Pinecone', 
                    on_click=save_conversation, 
                    use_container_width=True,
                    args=(st.session_state.memory_cache, 'button')
        )


def display_chat_interface():
    return st.chat_input('Type a message')
