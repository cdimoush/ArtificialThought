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
from _openai_module.summary_chain import LabelChain, CleanUpChain, SummaryChain 

ROLE_MAP = {
    'human': 'user',
    'ai': 'assistant'
}

label_chain = LabelChain()
cleanup_chain = CleanUpChain()
summary_chain = SummaryChain()

# import audrecorder_streamlit
st.title('Artifical Thought Experiment')

# Check if we're in the initial state
if 'intial_state' not in st.session_state:
    st.session_state['intial_state'] = True
    st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)

    # FOR DEVELOPMENT
    st.session_state.memory_cache.chat_memory.add_user_message("lets talk about frogs")
    st.session_state.memory_cache.chat_memory.add_ai_message("did you know frogs are kinda weird about boiling water?")

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

# Get new user input
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
