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
# Athought Modules
from _assemblyai_module.mic_component import audio_recorder
from _llm_module.summary_chain import LabelChain, CleanUpChain, SummaryChain 
from _pinecone_module.pinecone_upload_client import PineconeUploadClient

# Initialize global objects and state variables
def initialize_global_objects():
    global label_chain, cleanup_chain, summary_chain, pinecone_client, ROLE_MAP
    ROLE_MAP = {
        'human': 'user',
        'ai': 'assistant'
    }
    label_chain = LabelChain()
    cleanup_chain = CleanUpChain()
    summary_chain = SummaryChain()
    pinecone_client = PineconeUploadClient('athought-trainer')

# Define main application function
def main():
    # Initialization
    initialize_session_state()
    # Handle rerender requests
    rerender_page_if_needed()
    # Display UI
    display_title()
    display_chat_history()
    display_system_messages()
    # Process application states
    process_application_states()

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

# Function to process the main states of the application (audio, AI)
def process_application_states():
    if st.session_state['audio_state'] and not st.session_state['rerender']:
        handle_audio_state()
    elif st.session_state['initial_ai_state'] and not st.session_state['rerender']:
        handle_initial_ai_state()
    elif st.session_state['subsequent_ai_state'] and not st.session_state['rerender']:
        handle_subsequent_ai_state()
    else:
        print('WARNING: NO STATE DETECTED')

# Function to handle the audio state logic
def handle_audio_state():
    with st.chat_message("recorder", avatar="🎤"):
        st.write("Click on the microphone to record a message. Click on the microphone again to stop recording.")
        container = st.container(border=True)
        with container:
            transcript = audio_recorder(text='', icon_size='5x', key='main_mic')  # Returns audio in bytes (audio/wav)
            if transcript:
                st.session_state['transcript'] = transcript

    if st.session_state['transcript']:
        st.button('Save Audio', on_click=queue_initial_ai_state)

def handle_initial_ai_state():
    if st.session_state['transcript']:
        # Invoke the LabelChain and display the labels
        labels = label_chain.invoke({'transcript': st.session_state['transcript']})
        with st.chat_message("assistant"):
            st.write(f"Based on my analysis, the main topics in your message are...")
        with st.chat_message("output", avatar="✅"):
            st.write(', '.join(labels))

        # Invoke the SummaryChain and display the summary
        with st.chat_message("assistant"):
            st.write(f"Let's summarize what you've said...")
        with st.chat_message("output", avatar="✅"):
            summary = st.empty()

        async def write_summary_stream():
            summary_response = ''
            async for chunk in summary_chain.chain.astream({'transcript': st.session_state['transcript'], 'labels': labels}):
                summary_response += chunk
                summary.markdown(summary_response)

            return summary_response
        
        summary_response = asyncio.run(write_summary_stream())

        st.session_state['transcript'] = None
        st.session_state['summary'] = summary_response 
        st.session_state['labels'] = labels

        if st.session_state['summary']:
            with st.chat_message("assistant"):
                st.write(f"Great! Now that we have a summary, let's move on to the next phase.")

            # Upload the summary to Pinecone
            if 'uploaded' not in st.session_state:
                pinecone_client.upload([st.session_state['summary']])
                st.session_state['uploaded'] = True

        st.button('Continue', on_click=queue_subsequent_ai_state)

def handle_subsequent_ai_state():
    if query := st.chat_input("What is up?"):
        with st.chat_message("user"):
            st.markdown(query)

        role = 'You are a chat bot designed to talk about ANYTHING. You are friendly and helpful'
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template(role),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template('{query}')
        ])

        parser = StrOutputParser()
        model = ChatOpenAI(
            model="gpt-3.5-turbo-16k", 
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

# Function to toggle states or perform actions based on user input
def set_application_state(new_state):
    # Reset all states
    st.session_state['audio_state'] = False
    st.session_state['initial_ai_state'] = False
    st.session_state['subsequent_ai_state'] = False
    
    # Set the new state
    if new_state == 'audio':
        st.session_state['audio_state'] = True
    elif new_state == 'initial_ai_state':
        st.session_state['initial_ai_state'] = True
    elif new_state == 'subsequent_ai_state':
        st.session_state['subsequent_ai_state'] = True

def queue_initial_ai_state():
    st.session_state.memory_cache.chat_memory.add_user_message(st.session_state['transcript'])
    st.session_state['rerender'] = True
    st.session_state['queue_state_change'] = 'initial_ai_state'

def queue_subsequent_ai_state():
    # Clear the chat history
    st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
    # Add new message
    st.session_state.memory_cache.chat_memory.add_user_message(st.session_state['summary'])
    label_string = ', '.join(st.session_state['labels'])
    st.session_state.memory_cache.chat_memory.add_ai_message(f'Seems that you want to talk about {label_string}. How should we continue?')
    st.session_state['rerender'] = True
    st.session_state['queue_state_change'] = 'subsequent_ai_state'

# Function to rerender the page if needed
def rerender_page_if_needed():
    if st.session_state['rerender']:
        st.session_state['rerender'] = False
        if st.session_state['queue_state_change']:
            new_state = st.session_state['queue_state_change']
            set_application_state(new_state)
            st.session_state['queue_state_change'] = None  # Reset the queue state change
        st.rerun()

# Main application entry point
if __name__ == "__main__":
    # Global object initialization
    initialize_global_objects()
    main()