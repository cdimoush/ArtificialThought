import yaml
import streamlit as st
from typing import Optional
from src.agents.agent_registry import AgentRegistry
from src.agents.base_agent import BaseAgent
import importlib
import typer

class AgentHandler:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._ensure_agents_loaded()
        self._agent_params = self._load_agent_params()
        self._active_agent = None
        self.active_agent = self.agent_titles[0]

    def _ensure_agents_loaded(self):
        # This will import the agents module, triggering the decorators
        importlib.import_module('src.agents.agents')

    def change_model(self, model: str):
        if self._active_agent:
            agent_type = self._active_agent.__class__.__name__.lower().replace('agent', '')
            self._active_agent = self._create_new_agent(self._active_agent.title, model=model)

    @property
    def agent_titles(self) -> list:
        return list(self._agent_params.keys())

    @property
    def active_agent(self) -> Optional[BaseAgent]:
        return self._active_agent

    @active_agent.setter
    def active_agent(self, title: str):
        if title in self._agent_params:
            self._active_agent = self._create_new_agent(title)
        else:
            st.error(f"No agent configuration found for: {title}")

    def _load_agent_params(self) -> dict:
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    def _create_new_agent(self, title: str, model: str = None) -> Optional[BaseAgent]:
        if title not in self._agent_params:
            st.error(f"No agent configuration found for: {title}")
            return None

        kwargs = self._agent_params[title].copy()
        if isinstance(model, str):
            kwargs['model'] = model

        agent_type = kwargs.pop('type', 'simple')
        
        try:
            return AgentRegistry.create_agent(agent_type, title, **kwargs)
        except ValueError as e:
            st.error(str(e))
            return None

    def list_available_agents(self):
        return AgentRegistry.list_agent_types()
