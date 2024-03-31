# Native Python libraries
from operator import itemgetter
import asyncio
# Third-party libraries
import streamlit as st
# LangChain Modules
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser

# Initialize global objects and state variables
def initialize_global_objects():
    global ROLE_MAP
    ROLE_MAP = {
        'human': 'user',
        'ai': 'assistant'
    }

# Define main application function
def main():
    # Initialization
    initialize_session_state()
    # Handle rerender requests
    rerender_page_if_needed()
    # Display UI
    display_title()
    display_system_messages()
    display_chat_history()
    # Handle chat
    handle_chat()

def initialize_session_state():
    if 'initial_state' not in st.session_state:
        st.session_state['audio_state'] = True
        st.session_state['initial_ai_state'] = False
        st.session_state['subsequent_ai_state'] = False
        st.session_state['rerender'] = False
        st.session_state['queue_state_change'] = None
        st.session_state['transcript'] = ''
        st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
        st.session_state.memory_cache.chat_memory.add_ai_message("""
            Hello human, welcome to artificial thought experiment....
                    
            Don't get hung up on experiment. Think of it as an experience gifted to us by the grace and love of Conner Dimoush. 
                    
            We will be exploring the phenomenon of inefficiency of communication. Whether it be verbal human to human dialogue or an internal monologue,
            it can be observed that quantity of words scale atrociously with the complexity of the subject matter.

            This doesn't have to be the case. You'll see why shortly.
                    
            I want you to describe something novel, unique, or interesting. Maybe something you've been thinking about for quite some time, or maybe something that just popped into your head. I will transcribe your message and we will go from there.... 
            """
        )
        st.session_state['initial_state'] = True

# Function to display the application title or any static content
def display_title():
    st.title('Artificial Thought Experiment')

# Function to display the chat history
def display_chat_history():
    # Check if there's a new message to display
    current_history_length = len(st.session_state['memory_cache'].chat_memory.messages)
    # if 'last_displayed_length' not in st.session_state or st.session_state['last_displayed_length'] != current_history_length:
        # There's new message(s), update the display
    for message in st.session_state['memory_cache'].chat_memory.messages:
        # Using ROLE_MAP to get a user-friendly name for the message type
        message_role = ROLE_MAP.get(message.type, "Unknown")
        with st.chat_message(message_role):
            st.markdown(message.content)
        
    # Update the last displayed length in session state
    st.session_state['last_displayed_length'] = current_history_length

# Function to handle the end state of the application
def display_system_messages():
    if not st.session_state['initial_state']:
        st.warning('You have reached the end of current development...')

def handle_chat():
    from streamlit_extras.bottom_container import bottom
    with bottom():
        col1, col2 = st.columns(2)
        with col1:
            with st.popover("Options"):
                role_select = st.selectbox(
                'Agent Role',
                ('dry', 'chatty'))
        with col2:
            st.write("[MICROPHONE PLACEHOLDER]")
    if query := st.chat_input("What is up?"):
        with st.chat_message("user"):
            st.markdown(query)

        agent_roles = {
            "dry": "You are a chat bot that chats. Except you are not that chatty. You really try stay to the point and finish the conversation.",
            "chatty": "You are a chat bot that chats. You are very chatty and love to keep the conversation going."
        }

        role = agent_roles[role_select]

        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template(role),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template('{query}')
        ])

        parser = StrOutputParser()
        model = ChatOpenAI(
            model="gpt-4-0125-preview", 
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter("history")
            )
            | prompt
            | model
            | parser
        )

        with st.chat_message("assistant"):
            assistant_message = st.empty()

        async def write_stream():
            assistant_response = ''
            async for chunk in chain.astream({"query": query}):
                assistant_response += chunk
                assistant_message.markdown(assistant_response)

            return assistant_response

        assistant_response = asyncio.run(write_stream())

        # Save new message history
        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(assistant_response)

# Function to rerender the page if needed
def rerender_page_if_needed():
    if st.session_state['rerender']:
        st.session_state['rerender'] = False

        # HEY YOU CAN ADD RERENDER LOGIC HERE IF NEEDED

        st.rerun()

# Main application entry point
if __name__ == "__main__":
    # Global object initialization
    initialize_global_objects()
    main()