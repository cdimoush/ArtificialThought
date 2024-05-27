import streamlit as st
from langchain.memory import ConversationBufferMemory
from src.agents import AgentHandler
from config import APP_MODE

def handle_session_initialization():
    """
    Initializes or resets the session state variables required for the application.
    If the initial state is not set, it initializes session variables and preloads an AI message.
    """
    if 'initial_state' not in st.session_state:
        st.session_state['rerender'] = False
        st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
        st.session_state['agent_handler'] = AgentHandler('config/agents.yaml')
        st.session_state['app_mode'] = APP_MODE.CHAT
        # st.session_state.memory_cache.chat_memory.add_ai_message("""
        #     Hello human, welcome to artificial thought experiment....
                    
        #     Don't get hung up on experiment. Think of it as an experience gifted to us by the grace and love of Conner Dimoush. 
                    
        #     We will be exploring the phenomenon of inefficiency of communication. Whether it be verbal human to human dialogue or an internal monologue,
        #     it can be observed that quantity of words scale atrociously with the complexity of the subject matter.

        #     This doesn't have to be the case. You'll see why shortly.
                    
        #     I want you to describe something novel, unique, or interesting. Maybe something you've been thinking about for quite some time, or maybe something that just popped into your head. I will transcribe your message and we will go from there.... 
        #     """
        # )
        st.session_state['initial_state'] = True