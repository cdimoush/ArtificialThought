# File: agents.py

"""
Agents Module

This module contains classes and logic for creating and managing AI agents that interact with users. The agents are designed to handle various tasks based on their roles and configurations. Each agent can utilize different chains of logic and models to process user queries and generate appropriate responses.

Classes:
   - ChainableAgent: A base agent class that supports adding, removing, listing, and running chains of logic.
   - SimpleAgent: A straightforward agent that utilizes a single chain to generate responses.
   - IntrospectiveAgent: An advanced agent that performs introspection before generating a response.
   - Agent: A specific implementation of IntrospectiveAgent with pre-configured behaviors and roles.

The agents leverage the LangChain library for building prompt templates and processing chat interactions. They also support streaming responses for real-time interaction with users.
"""

import yaml
from copy import deepcopy
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, AIMessagePromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from operator import itemgetter
import streamlit as st
import typer

from src.agents.base_agent import BaseAgent, ChainableAgent, register_chain
from src.agents.agent_registry import register_agent
from src.agents.prompt import (SIMPLE_INTROSPECTION_PROMPT,
                               ROLE_INTROSPECTION_PROMPT,
                            )

from src.utils.stream_handler import StreamHandler
from functools import wraps
from collections import OrderedDict

"""
Chainable Agent Implementations
"""
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
        return RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser

@register_agent
class IntrospectiveAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)

    @register_chain
    def _build_intro_chain(self):
        prompt = SIMPLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()
        return RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser

    @register_chain
    def _build_main_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        return RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser

@register_agent
class RoleAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)

    @register_chain
    def _build_role_chain(self):
        prompt = ROLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()

        def update_role(result):
            self.role = result
            return result

        role_llm = ChatOpenAI(model='gpt-4o-mini-2024-07-18', streaming=True, verbose=False) 

        return (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | role_llm
            | parser 
            | RunnableLambda(update_role)
        )

    @register_chain
    def _build_main_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        return (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | self.llm 
            | parser
        )