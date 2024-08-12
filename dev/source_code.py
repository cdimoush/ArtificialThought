# File: app.py
# Third-party libraries
import streamlit as st
import typer

# source imports
from src.app.initialization import handle_session_initialization
from src.app.ui_component import display_title, display_chat_history, display_system_messages
from src.app.chat_interface import handle_chat
from config import APP_MODE

# Define main application function
def main():
    # Setup Layout
    # ------------
    typer.secho(f'Running Loop! Mode: {st.session_state.app_mode}', fg=typer.colors.RED)
    st.set_page_config(layout="wide")
    header = st.container()

    if st.session_state.app_mode == APP_MODE.DRAFT:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['col1'] = st.container()
        with col2:
            st.session_state['col2'] = st.container()
    else:
        st.session_state['col1'] = st.container()
        st.session_state['col2'] = None

    # Handle rerender requests
    # ------------
    rerender_page_if_needed()

    # Display UI
    # ------------
    with header:
        display_title()
        display_system_messages()
    display_chat_history()

    # Handle chat
    # ------------
    handle_chat()

# Function to rerender the page if needed
def rerender_page_if_needed():
    if st.session_state['rerender']:
        st.session_state['rerender'] = False
        # HEY YOU CAN ADD RERENDER LOGIC HERE IF NEEDED
        st.rerun()

# Main application entry point
if __name__ == "__main__":
    handle_session_initialization()
    main()



# File: agents.py
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
from src.agents.prompt import INTROSPECTION_PROMPT, TASK_DEFINITION_PROMPT, DEVELOPER_PROMPT, REVIEWER_PROMPT
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
        prompt = INTROSPECTION_PROMPT
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

class DevAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)
        self._build_chain()

    def _build_chain(self):
        prompts = [TASK_DEFINITION_PROMPT, DEVELOPER_PROMPT, REVIEWER_PROMPT, DEVELOPER_PROMPT]

        for prompt in prompts:
            if prompt == TASK_DEFINITION_PROMPT:
                chain = RunnablePassthrough.assign(
                    history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
                ) | prompt | self.llm | StrOutputParser()

            else:
                chain = prompt | self.llm | StrOutputParser()

            self.add_chain(chain)



# File: agent_handler.py
import yaml
import streamlit as st
from typing import Optional
from src.agents.agents import ChainableAgent, SimpleAgent, IntrospectiveAgent, DevAgent

AGENT_TYPE_MAP = {
   'simple': SimpleAgent,
   'introspective': IntrospectiveAgent,
   'dev': DevAgent
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



# File: base_agent.py
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

    @abstractmethod
    def _build_chain(self):
        pass


# File: prompt.py
from langchain_core.prompts.prompt import PromptTemplate

_DEFAULT_INTROSPECTION_PROMPT_TEMPLATE = """You are a metacognition program That acts as a internal monolog for a artificial intelligent entity. This artificial intelligent entity is multifaceted and can play many different roles. You as a metacognition program understand the role that the artificial intelligence is set to and adjust your reflection accordingly.

The artificial intellegence is chatting with a user and is attempting to best fulfill the use request by (1) understandings the user's request, (2) providing a response that alligns with their set role. 

Before the artificial intelligence can response, the metacongition program must reflect on the chat history and the role that the artificial intelligence is set to. The metacogntion program prioritizes the most recent human message. The metacognition formats its output as an internal thought that the artificial intelligence is having. These thoughts can contain some or all of the following elements: (1) a reflection on the role that the artificial intelligence is set to, (2) a reflection on the chat history, (3) a reflection on the user's request, (4) a reflection on the artificial intelligence's response.

If the conversation is simple the thought can be (internal thought: respond to the user's request). If the conversation is complex the thought can be like one of the following examples:

Example 1:
Role: You are an AI that only writes python code.
Human Query: Hey, how do I write a program that counts to 10?
Metacongition: (internal thought: I am a python AI, I should write a program that counts to 10. I should not address the user with a greeting, explanation, or any other language that is not python code. I should write a program that counts to 10.)

Example 2:
Role: You are an AI that plans software projects. You do not write code. You output concise plans in bullet points.
Human Query: Hey, how do I write a program that solve forward kinematics for robot arms? Please reference details about my robot model.
Metacongition: (internal thought: I am a project planning AI, I should output a concise plan in bullet points. These points should include how to write a program that solves forward kinematics for robot arms and reference details about the user's robot model. I should not output any code or long explanations.)

End of Examples...

YOU DO NOT NEED TO WRITE THE AI RESPONSE. ONLY WRITE THE INTERNAL THOUGHT THAT THE AI IS HAVING. YOU ONLY OUTPUT THE INTERNAL THOUGHT LABELED `internal thought:`. YOU PLACE THIS IN PERENTHESIS. THOUGHTS ARE NEVER MORE THAN 3 SENTENCES. YOU NEVER WRITE CODE. YOU NEVER ADDRESS THE USER.


Role: {role}
Chat History:
{history}
Human Query: 
{query}


"""

INTROSPECTION_PROMPT = PromptTemplate(input_variables=["role", "history", "query"], template=_DEFAULT_INTROSPECTION_PROMPT_TEMPLATE)


TASK_DEFINITION_PROMPT = PromptTemplate(
    input_variables=["role", "history", "query"],
    template="""
    ## Role: 
    {role}
    
    ## History: 
    {history}
    
    ## Query: 
    {query}

    ## Task:
    You're an superintelligent AI model developed to specialize in solving python programming problems from a high level. You are not a programmer. You provide instructions to programmers that work for you.

    You do NOT write code. You do NOT output code. You only output instructions. You may be provided with instructions that you have been previously working on. If not explicitly asked to start over, continue from where you left off by listening for the user's request to revise, change, expand, or continue the instructions.

    TEXT IN, INSTRUCTIONS OUT
    
    The text input that you receive could include the following:
    - Dialogue
    - Instructions
    - Code (Reference, examples, previous solution attempts)
    - Error messages

    Interpret the text input and output instructions that would be understood by a junior software developer. These instructions should be specific enough to define the code needed to solve the problem. However, instructions should be between 50-100 words. Do not micromanage the programmer. Just get the most important information across. 

    If the text input is not specific, make assumption of needs in instructions. If some needs cannot be determined, include a `open item` section in the instructions.

    
    INPUT EXAMPLE:
    Human: I have a custom method that converts an integer into a solution. I have two variables that should be added toghether and then converted into a solution. I need a function that takes two arguments and returns a solution.

    OUTPUT EXAMPLE:
    Instructions:
    - Write a function called solution_function that takes two arguments.
    - Add the two arguments together.
    - Use the custom method from the user's project to convert the sum into a solution.

    Now respond to the query by completing the task.
    """
)

DEVELOPER_PROMPT = PromptTemplate(
    input_variables=["role", "query"],
    template="""
    ## Role: 
    {role}
        
    ## Query: 
    {query}

    ## Task:
    You are a program that outputs python code. TEXT IN, PYTHON CODE OUT. Only output python code. No additional text.

    The text input that you receive could include the following:
    The text input that you receive could include the following:
    - Dialogue
    - Instructions
    - Code (Reference, examples, previous solution attempts)
    - Error messages

    Interpret the text input and output python code that solves the problem. If the text input is specific to the desired output code, then follow specification exactly. If the text input is not specific, make assumption of needs and include comments. If some needs cannot be determined, leave sections of the output code blank and include comments about the missing information. 

    INPUT EXAMPLE:
    Instructions:
    - Write a function called solution_function that takes two arguments.
    - Add the two arguments together.
    - Use the custom method from the user's project to convert the sum into a solution.

    OUTPUT EXAMPLE:
    ''' python
    def solution_function(arg1, arg2):
      '''
      Solution function calculated the solution by using (discussed method)
      arg1: (type) description
      arg2: (type) description
      return: (type) description
      '''

      # Implementation of equation 1 
      arg3 = arg1 + arg2

      # [Insufficient information about equation 2 ...] 

      return solution    

    Now respond to the query by completing the task.
    """
)

REVIEWER_PROMPT = PromptTemplate(
   input_variables=["role", "query"],
   template="""
   ## Role: 
   {role}

   ## Query: 
   {query}

   ## Task:
   You are a program that reviews python code. TEXT IN, REVIEW OUT. Only output review and critique. No additional text. 

   The text input that you receive could include the following:
   - Dialogue
   - Instructions
   - Code (Reference, examples, previous solution attempts)
   - Error messages

   Interpret the text input and provide constructive feedback on the code. Your review should focus on the following aspects:

   1. **Correctness**: Identify any logical errors or issues in the code. Highlight where the code does not align with the original query or requirements.
   2. **Efficiency**: Suggest improvements for optimizing the code in terms of performance and resource utilization.
   3. **Readability**: Point out areas where the code can be made more readable and maintainable, including naming conventions, code structure, and comments.
   4. **Best Practices**: Recommend changes that align with Python best practices and coding standards.
   5. **Security**: Identify any potential security vulnerabilities or concerns in the code.

   Format your output clearly with the following sections:

   - **Feedback Summary**: A concise summary of the overall feedback.
   - **Detailed Review**:
     - **Correctness**:
       - [Point out specific issues with line numbers if available]
     - **Efficiency**:
       - [Suggest optimizations]
     - **Readability**:
       - [Recommend improvements for readability]
     - **Best Practices**:
       - [Highlight deviations from best practices]
     - **Security**:
       - [Identify any security concerns]

   Use bullet points for each section to organize your feedback. Do not include any code. Focus solely on providing actionable critique and guidance.

   Now respond to the query by completing the task.
   """
)


# File: chat_interface.py
import streamlit as st
import os
from streamlit_extras.bottom_container import bottom
from _pinecone_module.pinecone_upload_client import save_conversation
from config import APP_MODE
import typer

#################################
##########   UI  ################
#################################
def display_agent_popover():
    with bottom():
        col1, col2, col3, _ = st.columns([1, 1, 1, 1], gap='small')
        with col1:
            with st.popover(f'Agent: {st.session_state.agent_handler.active_agent.title.upper()}', use_container_width=True):
                st.write(f'MODEL: ')
                st.write(st.session_state.agent_handler.active_agent.model)
                st.write(f'ROLE: ')
                st.write(st.session_state.agent_handler.active_agent.role)
        with col2:
            with st.popover('Load Files', use_container_width=True):
                uploaded_files = st.file_uploader("File Uploader", type=['py', 'txt', 'yaml'], accept_multiple_files=True)

                if uploaded_files is not None:
                    for uploaded_file in uploaded_files:
                        write_path = os.path.join(st.session_state['temp_dir'], uploaded_file.name)
                        with open(write_path, 'wb') as f:
                            f.write(uploaded_file.read())
                            
        with col3:
            st.button('Pinecone', 
                      on_click=save_conversation, 
                      use_container_width=True,
                      args=(st.session_state.memory_cache, 'button')
            )

#################################
##########   Query ##############
#################################

def add_references_to_query(query: str):
    if st.session_state.file_handler.has_file_content():
        query = st.session_state.file_handler.write_file_content_to_query() + query
    return query

def handle_query():
    query = add_references_to_query(st.session_state.draft_cache)
    st.session_state.memory_cache.chat_memory.add_user_message(query)
    with st.session_state['col1']:
        with st.chat_message('user'):
            st.markdown(query)
    st.session_state.draft_cache = ''

#################################
##########   Response  ##########
#################################

def handle_response(query: str):
    with st.session_state['col1']:
        with st.chat_message('assistant'):
            agent = st.session_state.agent_handler.active_agent
            chat_container = st.empty()
            response = agent.generate_response(query, chat_container)
            chat_container.markdown(response)

#################################
##########    Draft    ##########
#################################

def handle_draft_area():
    st.session_state.draft_cache = st.session_state.draft_area

#################################
##########   Main  ##############
#################################

def handle_chat():
    # UI
    display_agent_popover()
    query = st.chat_input('Type a message')

    # QUERY
    if st.session_state.app_mode == APP_MODE.QUERY:
        if query:
            if query == '/': # Menu Toggle
                st.session_state.menu_manager.display_menu_as_dialog()
            else:
                # st.session_state.app_mode = APP_MODE.RESPONSE
                st.session_state.draft_cache = query
                handle_query()
                handle_response(st.session_state.memory_cache.chat_memory.messages[-1])
            query = None

    # DRAFT
    if st.session_state.app_mode == APP_MODE.DRAFT:
        with st.session_state['col2']:
            draft_container = st.empty()
            print(draft_container.height)
        if query:
            if query == '/': # Menu Toggle
                st.session_state.menu_manager.display_menu_as_dialog()
            elif query == '.': # Response
                # st.session_state.app_mode = APP_MODE.RESPONSE
                handle_query()
                handle_response(st.session_state.memory_cache.chat_memory.messages[-1])
            else:
                st.session_state.draft_cache += query + '\n'
            query = None
        draft_container.text_area("Draft:", st.session_state.draft_cache, height=450, label_visibility='collapsed', on_change=handle_draft_area, key='draft_area')
                    
    # RESPONSE
    if st.session_state.app_mode == APP_MODE.RESPONSE:
        st.session_state.app_mode = APP_MODE.DRAFT
        handle_response(st.session_state.memory_cache.chat_memory.messages[-1])


# File: initialization.py
import streamlit as st
from langchain.memory import ConversationBufferMemory
import tempfile
import typer

from config import APP_MODE
from src.utils.file_handler import FileHandler
from src.agents.agent_handler import AgentHandler
from src.menus.agent_menu import AgentMenu, ModelMenu
from src.menus.file_menu import FolderMenu 
from src.menus.menu import MenuManager, Menu, SimpleMenuMethods

def handle_session_initialization():
    """
    Initializes or resets the session state variables required for the application.
    If the initial state is not set, it initializes session variables and preloads an AI message.
    """
    if 'initial_state' not in st.session_state:
        typer.secho('Initializing Session State...', fg=typer.colors.GREEN)
        st.session_state['initial_state'] = True
        st.session_state['app_mode'] = APP_MODE.QUERY
        st.session_state['rerender'] = False
        st.session_state['temp_dir'] = tempfile.mkdtemp()
        st.session_state['memory_cache'] = ConversationBufferMemory(return_messages=True)
        st.session_state['draft_cache'] = ''
        st.session_state['agent_handler'] = AgentHandler('config/agents.yaml')
        st.session_state['file_handler'] = FileHandler('config/dirs.yaml')
        initialize_menu_manager()


def initialize_menus():
    main_menu_options = {
        "Select Agent": AgentMenu(st.session_state.agent_handler),
        "Change Model": ModelMenu(st.session_state.agent_handler),
        "Load File": FolderMenu(st.session_state.file_handler),
        "Clear Memory Cache": SimpleMenuMethods.clear_memory_cache,
        "Toggle Draft Mode": SimpleMenuMethods.toggle_draft_state,
    }
    main_menu = Menu("Main Menu", main_menu_options)
    menu_manager = MenuManager(main_menu)
    return menu_manager

def initialize_menu_manager():
    st.session_state['menu_manager'] = initialize_menus()


# File: ui_component.py
import streamlit as st
from config import ROLE_MAP

def display_title():
    """
    Displays the application title or any static content at the top of the page.
    """
    st.title('Artificial Thought Experiment')

def display_chat_history():
    """
    Displays the chat history in the Streamlit application.
    Uses the global ROLE_MAP to assign user-friendly names to message types.
    """
    # There's new message(s), update the display
    for message in st.session_state['memory_cache'].chat_memory.messages:
        # Using ROLE_MAP to get a user-friendly name for the message type
        message_role = ROLE_MAP.get(message.type, "Unknown")
        with st.session_state['col1']:
            with st.chat_message(message_role):
                st.markdown(message.content)
        
def display_chat_history_old():
    """
    Displays the chat history in the Streamlit application.
    Uses the global ROLE_MAP to assign user-friendly names to message types.
    """
    # Retrieve the current history length
    current_history_length = len(st.session_state['memory_cache'].chat_memory.messages)
    
    # Check if there's a new message to display
    if 'last_displayed_length' not in st.session_state or st.session_state['last_displayed_length'] != current_history_length:
        # There's new message(s), update the display
        for message in st.session_state['memory_cache'].chat_memory.messages:
            # Using ROLE_MAP to get a user-friendly name for the message type
            message_role = ROLE_MAP.get(message.type, "Unknown")
            with st.chat_message(message_role):
                st.markdown(message.content)
        
        # Update the last displayed length in session state
        st.session_state['last_displayed_length'] = current_history_length

def display_system_messages():
    """
    Displays system messages, such as warnings or notifications, to the user.
    """
    if not st.session_state['initial_state']:
        st.warning('You have reached the end of current development...')


# File: agent_menu.py
import streamlit as st
from langchain.memory import ConversationBufferMemory
from _pinecone_module.pinecone_upload_client import save_conversation

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


# File: file_menu.py
import streamlit as st
from langchain.memory import ConversationBufferMemory
from _pinecone_module.pinecone_upload_client import save_conversation

# Local imports
from src.utils.file_handler import FileHandler, FolderNavigator, FileNavigator
from src.agents.agent_handler import AgentHandler
from src.menus.menu import Menu
from config import APP_MODE   

class FolderMenu(Menu):
    def __init__(self, handler: FileHandler):
        """Dynamically generate options based on files in the directory. """
        nav = handler.get_nav()
        file_names = nav.list_contents()
        options = {f"{name}": self.make_sub_menu(path, folder) for name, path, folder in file_names}
        super().__init__("Select Directory / File", options)

    def __reinstate__(self):
        """ Reinitialize the menu with the current file handler.

        TRASHY CODE REVIEW LATER
        """
        self.__init__(st.session_state.file_handler)

    def make_sub_menu(self, path: str, folder: bool):
        """ Make sub menus for folder navigation. """
        if folder:
            return FolderMenu(FolderNavigator([path]))
        else:
            return FileMenu(FileNavigator(path))

class FileMenu(Menu):
    def __init__(self, nav: FileNavigator):
        """ Load File...
        In the future add methods for extracting code from files. 
        """
        options = {f"Load {nav.name}": self.make_load_file_function(nav)}
        super().__init__("File Menu", options)

    def make_load_file_function(self, nav):
        """Returns a function that loads the file based on the navigator."""
        def load_file(menu_status, **kwargs):
            nav.load_file()
            st.session_state['menu_manager'].reset()
            menu_status.success(f"Loaded file: {nav.name}")
        return load_file
    
    def make_load_class_function(self, nav):
        """Returns a function that loads a specific class from the file."""
        pass

    def make_load_method_function(self, nav):
        """Returns a function that loads a specific method from the file."""
        pass
    



# File: menu.py
import streamlit as st
from langchain.memory import ConversationBufferMemory
from _pinecone_module.pinecone_upload_client import save_conversation

# Local imports
from config import APP_MODE

class MenuManager:
    def __init__(self, initial_menu):
        """
        Initialize the MenuManager with an initial menu.
        :param initial_menu: The starting Menu instance.
        """
        self.current_menu = initial_menu
        self.menu_history = [initial_menu]  # Initialize the history with the initial menu

    @st.experimental_dialog('Menu Selection')
    def display_menu_as_dialog(self):
        """
        Display the current menu as a dialog.
        """
        menu_status = st.empty()
        menu_container = st.empty()
        self.current_menu.display_dialog(menu_container)
        col1, col2 = st.columns([3, 1])
        with col1:
            menu_input = st.chat_input('Make a selection...')
        with col2:
            menu_save = st.button('Save')
        if menu_input:
            if self.handle_selection(menu_input, menu_status):
                self.current_menu.display_dialog(menu_container)
        if menu_save:
            st.rerun()
                
    def handle_selection(self, selection, menu_status)->bool:
        """
        Handle the user's menu selection.
        :param selection: The user's selection.
        :param menu_status: The status message container.
        """
        if selection == '..':
            self.go_back()
        else:
            try:
                selection = int(selection)
                action = self.current_menu.get_action(selection)
                if isinstance(action, Menu):
                    # Check if Menu has a reinstate method
                    if hasattr(action, '__reinstate__'):
                        action.__reinstate__()
                    self.current_menu = action
                    self.menu_history.append(action)
                elif callable(action):
                    action(**{'menu_status': menu_status})
                else:
                    return False
            except ValueError:
                return False
        return True

    def go_back(self):
        if len(self.menu_history) > 1:  # Ensure there's a previous menu to go back to
            self.menu_history.pop()  # Remove the current menu from the history
            self.current_menu = self.menu_history[-1]  # Set the current menu to the previous menu
        else:
            st.warning("You're at the top-level menu. There's no previous menu to go back to.")
    
    def reset(self):
        self.current_menu = self.menu_history[0]
        self.menu_history = [self.current_menu]

class Menu:
    def __init__(self, title, options):
        """
        Initialize a new Menu instance.
        :param title: The title of the menu.
        :param options: A dictionary of options where keys are option texts and values are the action methods or Menu instances for sub-menus.
        """
        self.title = title
        self.options = options

    def display_dialog(self, container):
        """
        Display the menu as a dialog.
        """
        menu_str = f"**{self.title}**\n"
        for idx, option in enumerate(self.options, start=1):
            menu_str += f"{idx}. {option}\n"
        with container:
            st.markdown(menu_str)

    def get_action(self, choice):
        """
        Get the action associated with the user's choice.
        :param choice: The user's choice (1-indexed).
        :return: The action associated with the choice.
        """
        if 1 <= choice <= len(self.options):
            return list(self.options.values())[choice - 1]
        else:
            return None
  
class SimpleMenuMethods:
    @staticmethod
    def clear_memory_cache(menu_status, **kwargs):
        """ Clear the memory cache. Include auto-save feature to backup to pinecone. """
        save_conversation(st.session_state.memory_cache, 'auto-save')
        st.session_state.memory_cache = ConversationBufferMemory(return_messages=True)
        menu_status.success("Memory cache cleared.")

    @staticmethod
    def toggle_draft_state(menu_status, **kwargs):
        if st.session_state.app_mode == APP_MODE.DRAFT:
            st.session_state.app_mode = APP_MODE.QUERY
            menu_status.success("Query mode enabled.")
        else:
            st.session_state.app_mode = APP_MODE.DRAFT
            menu_status.success("Draft mode enabled.")


# File: file_handler.py
import yaml
import os
import sys
from typing import Union
import streamlit as st
import typer

from src.utils.file_operations import FileOperations

class FolderNavigator:
    """ 
    Object for handling directory / file navagation and selection. 
    """
    def __init__(self, dirs: Union[list, str]):
        self.dirs = dirs
        if isinstance(self.dirs, str):
            self.dirs = [dirs]
        
    def list_contents(self) -> list:
        """
        Create a list of elements inside the directories. Each entry is a tuple with following structure:
        (name, path, is_directory)

        For name include the two neighboring parent directories for context of location.
        """
        contents = []
        for dir in self.dirs:
            dir = os.path.abspath(dir)
            typer.secho(f"Listing contents of directory: {dir}", fg=typer.colors.GREEN)
            if not os.path.isdir(dir):
                print(f"Directory '{dir}' does not exist.")
            else:
                typer.secho(f"Contents: {os.listdir(dir)}", fg=typer.colors.GREEN)
                for content in os.listdir(dir):
                    path = os.path.abspath(os.path.join(dir, content))
                    is_directory = os.path.isdir(path)
                    contents.append((self.make_display_name(path), path, is_directory))
                
        return contents
    
    def make_display_name(self, path: str) -> str:
        """
        Create a display name for a file or directory based on its path.
        """
        parts = os.path.normpath(path).split(os.sep)
        if len(parts) > 3:
            return f"{parts[-3]}/{parts[-2]}/{parts[-1]}"
        elif len(parts) > 2:
            return f"{parts[-2]}/{parts[-1]}"
        else:
            return parts[-1]

class FileNavigator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = os.path.basename(file_path)
        _, self.extension = os.path.splitext(self.file_path)

    def load_file(self):
        st.session_state.file_handler.add_file_content(self.name, FileOperations.load_reference_code(self.file_path))

    def load_class(self):
        # Placeholder for loading a specific class from the Python file
        print("Placeholder for loading a class.")
        # Pseudo code:
        # Determine class to load based on user input or some criteria
        # Extract class definition and related methods from the file

    def load_method(self):
        # Placeholder for loading a specific method from the Python file or class
        print("Placeholder for loading a method.")
        # Pseudo code:
        # Determine method to load based on user input or some criteria
        # Extract method definition from the class or file

class FileHandler:
    """ 
    Object to be used by session state to
    1) Store loaded contents
    2) Store parameters for file navigation
        -> Be able to produce top-level FolderNavigator objects
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.dirs = [st.session_state['temp_dir']]
        self.file_content = {}

    def get_nav(self) -> FolderNavigator:
        return FolderNavigator(self.dirs)

    def load_dirs(self, config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config['directories']
    
    def add_file_content(self, header, content) -> None:
        self.file_content[header] = content

    def has_file_content(self) -> bool:
        """ Return True if self.file_content is not empty. """
        return bool(self.file_content)
    
    def write_file_content_to_query(self) -> str:
        """Format the file content into a single string to be added to the query."""
        output = "(START FILE REFERENCE SECTION)\n NOTE: HUMAN HAS ATTACHED THE FOLLOWING REFERENCE FILES\n\n"
        for header, content in self.file_content.items():
            output += f"{content}\n\n"
        output += "(END FILE REFERENCE SECTION)\n"
        self.clear_file_content()
        return output

    def clear_file_content(self) -> None:
        self.file_content = {}



# File: file_operations.py
import re
import os
import ast
import json
import textwrap
import typer
from typing import List, Tuple

class FileOperations:
    @staticmethod
    def load_reference_code(file_path):
        """
        Load reference code from a file.
        """
        _, file_extension = os.path.splitext(file_path)

        ext_map = {
            'py': 'python',
            'java': 'java',
            'js': 'javascript',
            'html': 'html',
            'css': 'css',
            'cpp': 'c++',
            'yaml': 'yaml',
            'json': 'json',
            'ipynb': 'ipynb'
        }

        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as fin:
            file_content = fin.read()
        try:
            ext = ext_map[file_extension[1:]]
            if ext == 'ipynb':
                ext = 'python'
                file_content = FileOperations.load_notebook_code(file_content)
            reference_code = f'```{ext}\n{file_content}\n```'
        except KeyError:
            reference_code = file_content
        reference_code = f'*{file_name}*\n' + reference_code
        return reference_code

    @staticmethod
    def load_python_functions(file_content):
        """
        Load specific functions or classes from a Python file.
        """
        # Parse the file content into an Abstract Syntax Tree (AST)
        module = ast.parse(file_content)
        functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
        classes = [node for node in module.body if isinstance(node, ast.ClassDef)]
        func_class_dict = {}
        # Also, map the function names to the class name in func_class_dict
        for class_ in classes:
            class_functions = [node for node in class_.body if isinstance(node, ast.FunctionDef)]
            functions.extend(class_functions)
            for func in class_functions:
                func_class_dict[func.name] = class_.name
        # Get the names of all functions and classes
        function_names = [func.name for func in functions]
        class_names = [class_.name for class_ in classes]
        # Print the names of all classes and functions for the user to select from
        typer.secho('\nLoading classes and functions from the module...\n', fg=typer.colors.WHITE, bold=True)
        typer.secho('Classes...', fg=typer.colors.GREEN, bold=True)
        for i, class_name in enumerate(class_names):
            typer.secho(f'{i + 1}. {class_name}', fg=typer.colors.WHITE)
        typer.secho('Functions...', fg=typer.colors.GREEN, bold=True)
        for i, func_name in enumerate(function_names, start=len(class_names) + 1):
            if func_name in func_class_dict:
                typer.secho(f'{i}. {func_name} ({func_class_dict[func_name]})', fg=typer.colors.WHITE)
            else:
                typer.secho(f'{i}. {func_name}', fg=typer.colors.WHITE)
        # Initialize a list to store the selected items
        selected_items = []
        # Keep asking the user for their choice until they enter a non-integer
        typer.secho('\nEnter the number of the function or class you want to load: ', fg=typer.colors.MAGENTA, bold=True)
        typer.secho('(Note: Enter key to exit) ', fg=typer.colors.MAGENTA, bold=True)
        while True:
            choice = input()
            if not choice.isdigit():
                break
            try:
                # If the choice is a valid integer, add the corresponding item to the selected_items list
                item_index = int(choice) - 1
                if item_index < len(classes):
                    selected_items.append(classes[item_index])
                else:
                    selected_items.append(functions[item_index - len(classes)])
            except (ValueError, IndexError):
                typer.secho('Invalid choice', fg=typer.colors.RED)
        # Print the number of items that will be loaded
        typer.secho(f'Loading {len(selected_items)} items...', fg=typer.colors.GREEN)
        # If no items were selected, return the entire file content
        if len(selected_items) == 0:
            reference_code = file_content
        else:
            # Otherwise, generate the reference code from the selected items
            reference_code = ''
            selected_items_grouped = {}
            # Group the selected items by their class
            for item in selected_items:
                if isinstance(item, ast.FunctionDef) and item.name in func_class_dict:
                    class_name = func_class_dict[item.name]
                    if class_name not in selected_items_grouped:
                        selected_items_grouped[class_name] = []
                    selected_items_grouped[class_name].append(item)
                else:
                    # If the item is not a function or its class was not selected, add it to the reference code directly
                    code_block = ast.unparse(item)
                    code_block = FileOperations._extract_comments(code_block, file_content)
                    reference_code += f'{code_block}\n'
            # For each class, add its definition and its functions to the reference code
            for class_name, items in selected_items_grouped.items():
                class_def = f'class {class_name}:\n'
                reference_code += class_def
                for item in items:
                    code_block = '\n'.join((f'\t{line}' for line in ast.unparse(item).split('\n')))
                    code_block = FileOperations._extract_comments(code_block, file_content)
                    reference_code += f'{code_block}\n\n'
        # Wrap the reference code in a Python code block
        reference_code = f'```python\n{reference_code}\n```'
        return reference_code
   
    @staticmethod
    def _extract_comments(extracted_code, file_content):
        """
        Take code extracted from unparsed AST and insert comments from the original file.

        Args:
            extracted_code (str): The code extracted from the unparsed AST.
            file_content (str): The content of the original file.
        """
        # Strip all lines in the file content, and store in list
        file_lines = [line.strip() for line in file_content.split('\n')]
        ast_lines = extracted_code.split('\n')
        modified_ast_lines = []
        for line in ast_lines:
            if line.strip() in file_lines:
                line_index = file_lines.index(line.strip())
                # Check the lines immediately above for comments
                if line_index > 0 and file_lines[line_index - 1].startswith('#'):

                    # Extract the comment
                    comment = file_lines[line_index - 1]
                    # Get the whitespace at the beginning of the line
                    whitespace = line[:len(line) - len(line.lstrip())]
                    # Use textwrap.indent() to add the correct indentation to the comment
                    comment = textwrap.indent(comment, whitespace)
                    modified_ast_lines.append(comment)
                # Remove previous lines from file lines
                file_lines = file_lines[line_index + 1:]

            modified_ast_lines.append(line)
        # Return the modified unparsed AST with the comments inserted
        return '\n'.join(modified_ast_lines)

    @staticmethod
    def load_notebook_code(file_content):
        """
        Load code blocks from a Jupyter Notebook.
        """
        notebook_content = json.loads(file_content)
        code_blocks = []
        for cell in notebook_content['cells']:
            if cell['cell_type'] == 'code':
                # Preprocess the code to remove or comment out any lines that start with a `%`.
                code = ''.join(cell['source'])
                code = re.sub(r'^%.*$', '#\g<0>', code, flags=re.MULTILINE)
                code_blocks.append(code)
        reference_code = '\n'.join(code_blocks)
        return reference_code



# File: stream_handler.py
from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st
   
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container: st.container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text)

