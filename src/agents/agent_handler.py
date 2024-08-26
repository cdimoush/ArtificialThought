import yaml
import streamlit as st
from typing import Optional
from src.agents.agents import ChainableAgent, SimpleAgent, IntrospectiveAgent, DevAgent, RoleAgent

AGENT_TYPE_MAP = {
   'simple': SimpleAgent,
   'introspective': IntrospectiveAgent,
   'dev': DevAgent,
   'role': RoleAgent
}

class AgentHandler:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._agent_params = self._load_agent_params()
        self._active_agent = None
        self.active_agent = self.agent_titles[0]

    def change_model(self, model: str):
        active_cls = self._active_agent.__class__
        self._active_agent = self._create_new_agent_from_cls(active_cls, self.active_agent.title, model=model)

    @property
    def agent_titles(self) -> list:
        return list(self._agent_params.keys())

    @property
    def active_agent(self) -> Optional[ChainableAgent]:
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

    def _create_new_agent(self, title: str, model: str = None) -> Optional[ChainableAgent]:
        if title not in self._agent_params:
            st.error(f"No agent configuration found for: {title}")
            return None

        kwargs = self._agent_params[title]
        if isinstance(model, str):
            kwargs['model'] = model

        agent_type = kwargs.get('type', 'simple')
        agent_class = AGENT_TYPE_MAP.get(agent_type)
        if agent_class is None:
            raise ValueError(f"Agent type {agent_type} is not supported.")

        return self._create_new_agent_from_cls(agent_class, title, **kwargs)
    
    def _create_new_agent_from_cls(self, cls: ChainableAgent, title: str, **kwargs) -> Optional[ChainableAgent]:
        if title not in self._agent_params:
            st.error(f"No agent configuration found for: {title}")
            return None

        return cls(title, **kwargs)
