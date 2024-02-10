# Native Python libraries
import os
from io import BytesIO
import time
from operator import itemgetter
import asyncio
# Third-party libraries
import streamlit as st
import assemblyai as aai
# langchain modules
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    PromptTemplate
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser
# athought modules
from _assemblyai_module.__init__ import audio_recorder
from _llm_module.summary_chain import LabelChain, CleanUpChain, SummaryChain 
from _pinecone_module.pinecone_upload_client import PineconeUploadClient

ROLE_MAP = {
    'human': 'user',
    'ai': 'assistant'
}


# Chains
label_chain = LabelChain()
cleanup_chain = CleanUpChain()
summary_chain = SummaryChain()

# Pinecone
pinecone_client = PineconeUploadClient('athought-trainer')

# import audrecorder_streamlit
st.title('Artifical Thought Experiment')

# Check if we're in the initial state
if 'initial_state' not in st.session_state:
    # Booleans
    st.session_state['audio_state'] = True
    st.session_state['ai_state'] = False
    st.session_state['rerender'] = False
    st.session_state['queue_state_change'] = False 
    # Variables and Objects
    st.transcript = None
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

    # Initial state will become False after first summary is generated
    st.session_state['initial_state'] = True

# Warning Banner that reached the end    
if not st.session_state['initial_state']:
    st.warning('You have reached the end of current developement... Please enjoy this chat GPT wrapper for now... Do something cool, dont waste my money...')

def state_toggle():
    st.session_state['audio_state'] = not st.session_state['audio_state']
    st.session_state['ai_state'] = not st.session_state['ai_state']

def save_audio():
    st.session_state.memory_cache.chat_memory.add_user_message(st.session_state['transcript'])
    st.session_state['rerender'] = True
    st.session_state['queue_state_change'] = True

def main():
                                                                
    model = ChatOpenAI(
        model="gpt-3.5-turbo-16k", 
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()]
    )

    role = 'You are a chat bot designed to talk about ANYTHING. You are friendly and helpful'

    # Render the existing chat history
    if len(st.session_state.memory_cache.load_memory_variables({})['history']) > 0:
        for message in st.session_state.memory_cache.load_memory_variables({})['history']:
            with st.chat_message(ROLE_MAP[message.type]):
                st.markdown(message.content)


    # Audio State
    if st.session_state['audio_state'] and not st.session_state['rerender']:
        with st.chat_message("recorder", avatar="🎤"):
            st.write("Click on the microphone to record a message. Click on the microphone again to stop recording.")
            container = st.container(border=True)
            with container:
                st.session_state['transcript'] = audio_recorder(text='', icon_size='5x', key='main_mic') # Returns audio in bytes (audio/wav)
        
        if st.session_state['transcript']:
            with st.chat_message("user"):
                st.write(st.session_state['transcript'])
            # with st.chat_message("assistant"):
            #     st.write("Looks like some audio was captured. If you're happy with the recording, click the button below to continue.")
            st.button('Save Audio', on_click=save_audio)

    # Get new user input
    if st.session_state['ai_state'] and not st.session_state['rerender']:
        # INTIAL STATE
        if st.session_state['initial_state']:
            if st.session_state['transcript']:
                # Invoke the LabelChain and display the labels
                labels = label_chain.invoke({'transcript': st.session_state['transcript']})
                with st.chat_message("assistant"):
                    st.write(f"Based on my analysis, the main topics in your message are...")
                with st.chat_message("output", avatar="✅"):
                    st.write(', '.join(labels))


                # Invoke the SummaryChain and display the summary
                with st.chat_message("assistant"):
                    st.write(f"Lets summarize what you've said...")
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

                if st.button('Continue?'):
                    # Clear the chat history
                    st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
                    # Add new message
                    st.session_state.memory_cache.chat_memory.add_user_message(st.session_state['summary'])
                    label_string = ', '.join(st.session_state['labels'] )
                    st.session_state.memory_cache.chat_memory.add_ai_message(f'Seems that you want to talke about {label_string}. How should we continue?')
                    st.session_state['initial_state'] = False
                    st.session_state['rerender'] = True

        else:

            if query := st.chat_input("What is up?"):
                with st.chat_message("user"):
                    st.markdown(query)

                prompt = ChatPromptTemplate(messages=[
                    SystemMessagePromptTemplate.from_template(role),
                    MessagesPlaceholder(variable_name="history"),
                    HumanMessagePromptTemplate.from_template('{query}')
                ])

                parser = StrOutputParser()
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

    # Rerender the page
    if st.session_state['rerender']:
        st.session_state['rerender'] = False
        if st.session_state['queue_state_change']:
            st.session_state['queue_state_change'] = False
            state_toggle()
        st.rerun()
        
if __name__ == "__main__":
    main()
