# base_agent.py
from abc import ABC, abstractmethod
from functools import wraps
from functools import wraps
from operator import itemgetter
from collections import OrderedDict
from copy import deepcopy

import streamlit as st
from streamlit.elements.layouts import LayoutsMixin as st_container
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from src.utils.stream_handler import StreamHandler, get_streamhandler_cb
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler


import typer

# Base Agent
# -----------------
class BaseAgent(ABC):
    @abstractmethod
    def __init__(self, title, **kwargs):
        pass

    @abstractmethod
    def generate_response(self, query: str):
        pass

    @abstractmethod
    def _build_llm(self):
        pass

# Chainable Agent
# -----------------
class ChainableAgent(BaseAgent):
    """ 
    Chainable Agent:
    - This is a general base class for "agents" that use multiple llm inferences in a linear sequence. The external method
    is `generate_response` which calls the `_run_chains` method. To implement this class children must add chain instances to 
    the `chains` attribute. 
    """
    ###########################################################################################
    #################              BASE AGENT METHODS        ##################################
    ###########################################################################################
    def __init__(self, title: str, **kwargs):
        self.title = title
        self.chains = OrderedDict()
        self.role = kwargs.get('role', 'default role')
        self.model_provider = kwargs.get('model_provider', 'openai')
        self.model = kwargs.get('model', 'default-model')
        self.internal_memory = deepcopy(st.session_state.memory_cache)
        self._build_llm()
        self._initialize_chains()

    def generate_response(self, query: str):
        return self._run_chains(query)

    def _build_llm(self):
        if self.model_provider == 'openai':
            self.llm = ChatOpenAI(model=self.model, streaming=True, verbose=False)
        else:
            raise NotImplementedError(f"Model provider {self.model_provider} is not supported.")
        
    ###########################################################################################
    #################          CHAINABLE AGENT METHODS       ##################################
    ###########################################################################################
    def _initialize_chains(self):
        cls = self.__class__
        for method_name in cls.__dict__:
            method = getattr(self, method_name)
            if callable(method) and hasattr(method, '_is_chain'):
                method()  # Call the chain-building method to build the chain and add it to `self.chains`
        
    def _run_chains(self, query: str):
        result = None
        cb = get_streamhandler_cb()
        for chain_name, chain in self.chains.items():
            result = chain.invoke({'role': self.role, 'query': query}, {'callbacks': [cb]})
        return result 
    
    def _add_chain(self, name, chain):
        self.chains[name] = chain

    ###########################################################################################
    #################              DEVELOPER METHODS          #################################
    ###########################################################################################

    def fetch_memory(self, *args, **kwargs):
        return RunnablePassthrough.assign(history=RunnableLambda(self.internal_memory.load_memory_variables) | itemgetter('history'))
    
    def add_memory(self, message, *args, **kwargs):
        self.internal_memory.add_ai_message(message)

    def debug_prompt(self, prompt):
        for text in prompt.to_string().split("\n"):
            typer.secho(f"\n{text}", fg=typer.colors.MAGENTA)
        return prompt
    

def register_chain(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        chain = func(self, *args, **kwargs)
        self._add_chain(func.__name__, chain)
        return chain
    wrapper._is_chain = True
    return wrapper