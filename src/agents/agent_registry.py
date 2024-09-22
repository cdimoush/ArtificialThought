# agent_registry.py
from typing import Type, Dict
from src.agents.base_agent import BaseAgent
import typer

class AgentRegistry:
    _registry: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_class: Type[BaseAgent]):
        agent_type = agent_class.__name__.lower().replace('agent', '')
        cls._registry[agent_type] = agent_class
        return agent_class

    @classmethod
    def get_agent_class(cls, agent_type: str) -> Type[BaseAgent]:
        return cls._registry.get(agent_type.lower())

    @classmethod
    def list_agent_types(cls):
        return list(cls._registry.keys())

    @classmethod
    def create_agent(cls, agent_type: str, title: str, **kwargs) -> BaseAgent:
        agent_class = cls.get_agent_class(agent_type)
        if agent_class is None:
            raise ValueError(f"Agent type '{agent_type}' is not registered.")
        return agent_class(title, **kwargs)

def register_agent(agent_class: Type[BaseAgent]):
    typer.secho(f'Registering agent: {agent_class.__name__}', fg=typer.colors.BLUE)
    return AgentRegistry.register(agent_class)