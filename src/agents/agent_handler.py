import yaml
import streamlit as st
import typer

from src.agents.agents import Agent

class AgentHandler:
    def __init__(self, config_path):
        self.config_path = config_path
        self._agent_params = self.load_agent_params()
        self._active_agent = None
        self.active_agent = self.agent_titles[0]

    @property
    def agent_titles(self):
        return list(self._agent_params.keys())

    @property
    def active_agent(self):
        return self._active_agent

    @active_agent.setter
    def active_agent(self, title):
        if title in self._agent_params:
            self._active_agent = self.create_new_agent(title)
        else:
            st.error(f"No agent configuration found for: {title}")

    def load_agent_params(self):
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    def create_new_agent(self, title, model=None):
        if title not in self._agent_params:
            st.error(f"No agent configuration found for: {title}")
            return None
        
        kwargs = self._agent_params[title]
        if isinstance(model, str):
            kwargs['model'] = model
        return Agent(title, **kwargs)
    
    def change_model(self, model):
        self._active_agent = self.create_new_agent(self.active_agent.title, model)