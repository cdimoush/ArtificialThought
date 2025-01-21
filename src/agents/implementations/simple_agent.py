# File: simple_agent.py
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import streamlit as st

from src.agents.base_agent import ChainableAgent, register_chain
from src.agents.agent_registry import register_agent

@register_agent
class SimpleAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)

    @register_chain
    def _build_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        return RunnablePassthrough.assign(
            history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
        ) | prompt | self.llm | parser
