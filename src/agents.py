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
import streamlit as st

class Agent:
    def __init__(self, role, description):
        self.role = role
        self.description = description

    async def generate_response(self, query: str):
        raise NotImplementedError

    async def _generate_and_display_response(self, query: str):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template(self.description),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])

        parser = StrOutputParser()

        model = ChatOpenAI(model='gpt-4-0125-preview', streaming=True, callbacks=[StreamingStdOutCallbackHandler()])

        chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | model | parser

        assistant_response = ''
        try:
            async for chunk in chain.astream({'query': query}):
                assistant_response += chunk
        except Exception as e:
            st.error(f"Error generating response: {e}")
        
        return assistant_response

class DryAgent(Agent):
    def __init__(self):
        description = "You are a chat bot that chats. Except you are not that chatty. You really try to stay to the point and finish the conversation."
        super().__init__('dry', description)

    async def generate_response(self, query: str):
        # Use the base class method to generate and display the response
        return await self._generate_and_display_response(query)

class ChattyAgent(Agent):
    def __init__(self):
        description = "You are a chat bot that chats. You are very chatty and love to keep the conversation going."
        super().__init__('chatty', description)

    async def generate_response(self, query: str):
        # Use the base class method to generate and display the response
        return await self._generate_and_display_response(query)

class CrewAIAgent(Agent):
    def __init__(self):
        description = "Coordinates a crew of AI agents, each with a specific role in analyzing, developing, reviewing, and finalizing the solution."
        super().__init__('crewai', description)

    async def generate_response(self, query: str):
        # Example of how you might set up a CrewAI agent to generate a response
        # This is a placeholder for integrating with CrewAI's API or similar functionality
        # You would replace this with actual logic to generate a response using CrewAI
        raise NotImplementedError("CrewAI integration not implemented")

def select_agent(role_select):
    if role_select == 'dry':
        return DryAgent()
    elif role_select == 'chatty':
        return ChattyAgent()
    elif role_select == 'crewai':
        return CrewAIAgent()
    else:
        raise ValueError("Invalid agent role selected")