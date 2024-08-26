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
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, AIMessagePromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import streamlit as st
import typer

from src.agents.base_agent import BaseAgent
from src.agents.prompt import (SIMPLE_INTROSPECTION_PROMPT,
                               ROLE_INTROSPECTION_PROMPT,
                               TASK_DEFINITION_PROMPT, 
                               DEVELOPER_PROMPT, 
                               REVIEWER_PROMPT
                            )
from src.utils.stream_handler import StreamHandler

class ChainableAgent(BaseAgent):
    def __init__(self, title, **kwargs):
        self.title = title
        self.chains = []
        self.role = kwargs.get('role', 'default role')
        self.model_provider = kwargs.get('model_provider', 'openai')
        self.model = kwargs.get('model', 'default-model')
        self._build_llm()

    def generate_response(self, query: str, container):
        response = self.run_chains(query, container)
        print(f"Agent RESPONSE:\n {response}")

        return response

    def add_chain(self, chain):
        self.chains.append(chain)

    def remove_chain(self, chain):
        if chain in self.chains:
            self.chains.remove(chain)

    def list_chains(self):
        return self.chains

    def run_chains(self, query, container):
        output = [" " for _ in range(len(self.chains))]
        for i, chain in enumerate(self.chains):
            result = chain.invoke({'role': self.role, 'query': query}, {'callbacks': [StreamHandler(container)]})
            st.session_state.memory_cache.chat_memory.add_ai_message(result)
            output[i] = result
            query += "\n" + result
                    
        return " \n ".join(output)   

    def _build_llm(self):
        if self.model_provider == 'openai':
            self.llm = ChatOpenAI(model=self.model, streaming=True, verbose=False)
        else:
            raise NotImplementedError(f"Model provider {self.model_provider} is not supported.")

    def _build_chain(self):
        pass

class SimpleAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)
        self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser
        self.add_chain(chain)

class IntrospectiveAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)
        self._build_intro_chain()
        self._build_chain()

    def _build_intro_chain(self):
        prompt = SIMPLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()
        chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser
        self.add_chain(chain)

    def _build_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser
        self.add_chain(chain)


class RoleAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)
        self._build_role_chain()
        self._build_chain()

    def _build_role_chain(self):
        prompt = ROLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()
        
        def update_role(result):
            self.role = result
            return result
        
        role_llm = ChatOpenAI(model='gpt-4o-mini-2024-07-18', streaming=True, verbose=False) 

        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | role_llm
            | parser 
            | RunnableLambda(update_role)
        )
        self.add_chain(chain)

    def _build_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | self.llm 
            | parser
        )
        self.add_chain(chain)

class DevAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)
        self._build_chain()

    def _build_chain(self):
        prompts = [TASK_DEFINITION_PROMPT, DEVELOPER_PROMPT, REVIEWER_PROMPT, DEVELOPER_PROMPT]

        for prompt in prompts:
            if prompt == TASK_DEFINITION_PROMPT:
                llm = ChatOpenAI(model='gpt-4o-mini-2024-07-18', streaming=True, verbose=False)
                chain = RunnablePassthrough.assign(
                    history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
                ) | prompt | llm | StrOutputParser()

            else:
                chain = prompt | self.llm | StrOutputParser()

            self.add_chain(chain)
