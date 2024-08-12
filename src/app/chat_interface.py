import streamlit as st
import os
from streamlit_extras.bottom_container import bottom
from _pinecone_module.pinecone_upload_client import save_conversation
from config import APP_MODE
import typer

#################################
##########   UI  ################
#################################
def display_agent_popover():
    with bottom():
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
            chat_container = st.empty()
            response = agent.generate_response(query, chat_container)
            chat_container.markdown(response)

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

    # QUERY
    if st.session_state.app_mode == APP_MODE.QUERY:
        if query:
            if query == '/': # Menu Toggle
                st.session_state.menu_manager.display_menu_as_dialog()
            else:
                # st.session_state.app_mode = APP_MODE.RESPONSE
                st.session_state.draft_cache = query
                handle_query()
                handle_response(st.session_state.memory_cache.chat_memory.messages[-1])
            query = None

    # DRAFT
    if st.session_state.app_mode == APP_MODE.DRAFT:
        with st.session_state['col2']:
            draft_container = st.empty()
            print(draft_container.height)
        if query:
            if query == '/': # Menu Toggle
                st.session_state.menu_manager.display_menu_as_dialog()
            elif query == '.': # Response
                # st.session_state.app_mode = APP_MODE.RESPONSE
                handle_query()
                handle_response(st.session_state.memory_cache.chat_memory.messages[-1])
            else:
                st.session_state.draft_cache += query + '\n'
            query = None
        draft_container.text_area("Draft:", st.session_state.draft_cache, height=450, label_visibility='collapsed', on_change=handle_draft_area, key='draft_area')
                    
    # RESPONSE
    if st.session_state.app_mode == APP_MODE.RESPONSE:
        st.session_state.app_mode = APP_MODE.DRAFT
        handle_response(st.session_state.memory_cache.chat_memory.messages[-1])