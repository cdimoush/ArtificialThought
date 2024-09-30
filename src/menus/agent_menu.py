import streamlit as st
from langchain.memory import ConversationBufferMemory

# Local imports
from src.agents.agent_handler import AgentHandler
from src.menus.menu import Menu
from config import APP_MODE
   
class AgentMenu(Menu):
    def __init__(self, handler: AgentHandler):
        options = {f"{title}": self.make_select_agent_function(handler, title) for idx, title in enumerate(handler.agent_titles)}
        super().__init__("Select an Agent", options)

    def __reinstate__(self):
        """ Reinitialize the menu with the current agent handler. 
        
        TRASHY CODE REVIEW LATER
        """
        self.__init__(st.session_state.agent_handler)

    def make_select_agent_function(self, handler, title):
        """Returns a function that sets the active agent based on the title."""
        def select_agent(menu_status, **kwargs):
            handler.active_agent = title
            st.session_state['menu_manager'].reset()
            menu_status.success(f"Selected agent: {title}")
        return select_agent
    
class ModelMenu(Menu):
    def __init__(self, handler: AgentHandler):
        models = [
            'gpt-4o-2024-05-13',
            'gpt-4o-mini-2024-07-18',
            'gpt-4-0125-preview'
        ]
        options = {f"{model}": self.make_change_model_function(handler, model) for model in models}
        super().__init__("Change Model", options)

    def __reinstate__(self):
        """ Reinitialize the menu with the current agent handler. 
        
        TRASHY CODE REVIEW LATER
        """
        self.__init__(st.session_state.agent_handler)

    def make_change_model_function(self, handler, model):
        """Returns a function that sets the active agent based on the title."""
        def change_model(menu_status, **kwargs):
            handler.change_model(model)
            st.session_state['menu_manager'].reset()
            menu_status.success(f"Agent model changed to: {model}")
        return change_model