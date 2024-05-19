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
from crewai import Agent, Task, Crew, Process


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
    """
    Generates and displays a response based on the given query by coordinating a crew of AI agents.
    Each agent has a specific role in analyzing, developing, reviewing, and finalizing the solution.
    query: str - The input query to process.
    return: str - The final, optimized response.
    """

    # Define agents with detailed roles and goals as per the YAML specifications
    problem_solution_designer = Agent(
        role='Problem Solution Designer',
        goal='Make a plan outlining the main components and how they fit together to solve the problem.',
        verbose=True,
        memory=True,
        backstory=(
            "You're an AI model tasked with both analyzing the software development problem and designing the solution strategy."
            " First, break down the problem statement into fundamental components and requirements."
            " Then, devise a high-level strategy for the solution, including necessary algorithms, data structures, and design patterns."
        ),
        allow_delegation=True
    )

    code_developer = Agent(
        role='Code Developer',
        goal='Implement the solution strategy in Python.',
        verbose=True,
        memory=True,
        backstory=(
            "Implement the solution strategy provided by the problem_solution_designer in Python."
            " Focus on writing clean, efficient, and readable code, with well-commented sections explaining major blocks and functions."
            " Follow Pythonic conventions and best practices."
        ),
        allow_delegation=True
    )

    quality_assurance = Agent(
        role='Quality Assurance',
        goal='Review the Python code for syntax and logical errors.',
        verbose=True,
        memory=True,
        backstory=(
            "Review the Python code from code_developer, checking for syntax and logical errors, adherence to the solution strategy,"
            " and best coding practices."
            " Provide specific, actionable feedback in English text, calling out lines of code when necessary."
        ),
        allow_delegation=True
    )

    final_coder = Agent(
        role='Final Coder',
        goal='Refine the code based on feedback and prepare it for use.',
        verbose=True,
        memory=True,
        backstory=(
            "With access to all intermediate steps, read the code from code_developer and the feedback from quality_assurance."
            " Make the necessary adjustments to address the feedback and refine the code."
            " Ensure the final code incorporates all suggested improvements and adheres closely to the original solution strategy and problem requirements."
        ),
        allow_delegation=True
    )

    # Define tasks with detailed descriptions and expected outputs as per the YAML specifications
    analyze_task = Task(
        description=(
            "Make a plan outlining the main components and how they fit together to solve the problem."
            " Your output should combine clear problem analysis with a strategic solution overview, suitable for a programmer to implement."
        ),
        expected_output="Provide a concise plan in 4-10 sentences or bullet points.",
        agent=problem_solution_designer,
    )

    implement_task = Task(
        description=(
            "Implement the solution strategy in Python."
            " Focus on writing clean, efficient, and readable code, with well-commented sections explaining major blocks and functions."
        ),
        expected_output="Python code implementing the solution.",
        agent=code_developer,
    )

    review_task = Task(
        description=(
            "Review the Python code for syntax and logical errors, adherence to the solution strategy, and best coding practices."
            " Provide specific, actionable feedback in English text, calling out lines of code when necessary."
        ),
        expected_output="Feedback on the Python code.",
        agent=quality_assurance,
    )

    finalize_task = Task(
        description=(
            "Refine the code based on feedback and prepare it for use."
            " Ensure the final code incorporates all suggested improvements and adheres closely to the original solution strategy and problem requirements."
        ),
        expected_output="Final, optimized Python code.",
        agent=final_coder,
    )

    # Form the crew without tool dependencies, focusing on a sequential process
    crew = Crew(
        agents=[problem_solution_designer, code_developer, quality_assurance, final_coder],
        tasks=[analyze_task, implement_task, review_task, finalize_task],
        process=Process.sequential,
        memory=True,
        cache=True,
        max_rpm=100,
        share_crew=True
    )

    # Kickoff the process with the given query
    result = await crew.kickoff(inputs={'query': query})

    # Display the result using the appropriate method (assuming st is a Streamlit-like framework)
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