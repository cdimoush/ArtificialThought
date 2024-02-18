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
from _assemblyai_module.mic_component import audio_recorder
from _assemblyai_module.transcriber import transcribe_url, write_transcript_stream
from _llm_module.summary_chain import LabelChain, CleanUpChain, SummaryChain 
from _pinecone_module.pinecone_upload_client import PineconeUploadClient


if 'initial_state' not in st.session_state:
    st.session_state['initial_state'] = False
    st.session_state['transcript_url_list'] = []
    st.session_state['old_url_list'] = []
    st.session_state['output'] = 'Output: '

st.subheader("Base audio recorder")
url_array = audio_recorder(key="base")

if url_array:
    for url in url_array:
        if url not in st.session_state['transcript_url_list'] and url not in st.session_state['old_url_list']:
            st.session_state['transcript_url_list'].append(url)

stream = asyncio.run(write_transcript_stream())
output_message = st.empty()
if stream:
    st.session_state['output'] += stream
    output_message.text(st.session_state['output'])