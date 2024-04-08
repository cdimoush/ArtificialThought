import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from crewai import Agent, Task, Crew


def handle_chat_options() -> str:
    with bottom():
        (col1, col2) = st.columns(2)
        with col1:
            with st.popover('Options'):
                role_select = st.selectbox('Agent Role', ('dry', 'chatty', 'crewai'))
        with col2:
            st.write('[MICROPHONE PLACEHOLDER]')
    return role_select

def handle_user_input() -> str:
    query = st.chat_input('What is up?')
    if query:
        with st.chat_message('user'):
            st.markdown(query)
    return query

async def generate_and_display_response(role_select: str, query: str) -> str:
    agent_roles = {
        'dry': 'You are a chat bot that chats. Except you are not that chatty. You really try stay to the point and finish the conversation.',
        'chatty': 'You are a chat bot that chats. You are very chatty and love to keep the conversation going.'
    }
    role = agent_roles[role_select]
    
    prompt = ChatPromptTemplate(messages=[
        SystemMessagePromptTemplate.from_template(role),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template('{query}')
    ])
    
    parser = StrOutputParser()
    
    model = ChatOpenAI(model='gpt-4-0125-preview', streaming=True, callbacks=[StreamingStdOutCallbackHandler()])
    
    chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | model | parser
    
    with st.chat_message('assistant'):
        assistant_message = st.empty()
    
    assistant_response = ''
    try:
        async for chunk in chain.astream({'query': query}):
            assistant_response += chunk
            assistant_message.markdown(assistant_response)
    except Exception as e:
        st.error(f"Error generating response: {e}")
    
    return assistant_response

async def generate_and_display_response_crewai(query: str) -> str:
    # Placeholder for CrewAI setup, replace with actual implementation
    agent = Agent(
        role='Assistant',
        goal='Answer user queries',
        verbose=True,
        memory=True,
        backstory="I'm an AI trained to assist you.",
        tools=[],
        allow_delegation=True
    )
    
    task = Task(
        description=f"Answer the query: {query}",
        expected_output='A concise and helpful response.',
        agent=agent,
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process='sequential',
        memory=True,
        cache=True,
        max_rpm=100,
        share_crew=True
    )
    
    result = crew.kickoff(inputs={'query': query})
    
    with st.chat_message('assistant'):
        st.markdown(result)
    
    return result

def handle_chat():
    role_select = handle_chat_options()
    query = handle_user_input()
    if query:
        if role_select == 'crewai':
            assistant_response = asyncio.run(generate_and_display_response_crewai(query))
        else:
            assistant_response = asyncio.run(generate_and_display_response(role_select, query))
        
        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(assistant_response)