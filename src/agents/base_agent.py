# base_agent.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def __init__(self, title, **kwargs):
        pass

    @abstractmethod
    def _build_llm(self):
        pass

    @abstractmethod
    def generate_response(self, query: str, container):
        pass

    @abstractmethod
    def _build_chain(self):
        pass