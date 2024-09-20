# base_agent.py
from abc import ABC, abstractmethod
import streamlit as st

class BaseAgent(ABC):
    @abstractmethod
    def __init__(self, title, **kwargs):
        pass

    @abstractmethod
    def generate_response(self, query: str, container: st.container):
        pass

    @abstractmethod
    def _build_llm(self):
        pass
