import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom

def handle_chat_options() -> str:
    with bottom():
        (col1, col2) = st.columns(2)
        with col1:
            with st.popover('Options'):
                selected_agent = st.selectbox('Agent Role', st.session_state.agent_handler.agent_titles)
        with col2:
            st.write('[MICROPHONE PLACEHOLDER]')
    return selected_agent

def handle_user_input() -> str:
    query = st.chat_input('What is up?')
    if query:
        with st.chat_message('user'):
            st.markdown(query)
    return query

def handle_chat():
    selected_agent = handle_chat_options()
    query = handle_user_input()
    if query:
        agent = st.session_state.agent_handler.create_new_agent(selected_agent)
        response = asyncio.run(generate_and_display_response(agent, query))

        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(response)

async def generate_and_display_response(agent, query: str):
    response = await agent.generate_response(query)
    with st.chat_message('assistant'):
        st.markdown(response)

    return response