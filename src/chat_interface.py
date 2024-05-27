import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from config import APP_MODE

#################################
##########   UI  ################
#################################

def handle_chat_options() -> str:
    with bottom():
        (col1, col2) = st.columns(2)
        with col1:
            with st.popover('Options'):
                selected_agent = st.selectbox('Agent Role', st.session_state.agent_handler.agent_titles)
        with col2:
            st.write('[MICROPHONE PLACEHOLDER]')
    return selected_agent

def handle_user_input() -> str:
    selected_agent = handle_chat_options()
    query = st.chat_input('Type a message')
    if query:
        if query.startswith('/'): # Toggle between chat and menu mode
            if st.session_state.app_mode == APP_MODE.CHAT:
                st.session_state.app_mode = APP_MODE.MENU
                initialize_menu_manager()
            else:
                st.session_state.app_mode = APP_MODE.CHAT
        else:
            if st.session_state.app_mode == APP_MODE.CHAT:
                with st.chat_message('user'):
                    st.markdown(query)
                handle_chat(selected_agent, query)
            else:
                st.session_state.menu_manager.handle_selection(query)

#################################
##########   Menu  ##############
#################################
class Menu:
    def __init__(self, title, options):
        """
        Initialize a new Menu instance.
        :param title: The title of the menu.
        :param options: A dictionary of options where keys are option texts and values are the action methods or Menu instances for sub-menus.
        """
        self.title = title
        self.options = options

    def display(self):
        """
        Display the menu options.
        """
        st.markdown(f"**{self.title}**")
        for idx, option in enumerate(self.options, start=1):
            st.markdown(f"{idx}. {option}")

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
        
class MenuManager:
    def __init__(self, initial_menu):
        """
        Initialize the MenuManager with an initial menu.
        :param initial_menu: The starting Menu instance.
        """
        self.current_menu = initial_menu
        self.menu_history = [initial_menu]  # Initialize the history with the initial menu

    def display_current_menu(self):
        """
        Display the current menu.
        """
        self.current_menu.display()

    def handle_selection(self, selection):
        """
        Handle the user's menu selection.
        :param selection: The user's selection.
        """
        if selection == '..':
            self.go_back()
        else:
            try:
                selection = int(selection)
                action = self.current_menu.get_action(selection)
                if isinstance(action, Menu):
                    # If the action is a Menu instance, navigate to that menu.
                    self.current_menu = action
                    self.menu_history.append(action)
                    self.display_current_menu()
                elif callable(action):
                    # If the action is a callable, execute it.
                    action()
                else:
                    st.error("Invalid selection. Please try again.")
            except ValueError:
                st.error("Invalid selection. Please try again.")

    def go_back(self):
        if len(self.menu_history) > 1:  # Ensure there's a previous menu to go back to
            self.menu_history.pop()  # Remove the current menu from the history
            self.current_menu = self.menu_history[-1]  # Set the current menu to the previous menu
            self.display_current_menu()
        else:
            st.warning("You're at the top-level menu. There's no previous menu to go back to.")

def initialize_menus():
    # Define actions
    def option_1_action():
        st.success("Option 1 action executed.")

    def option_2_action():
        st.success("Option 2 action executed.")

    # Define sub-menu
    sub_menu_options = {
        "Sub Option 1": option_1_action,
        "Sub Option 2": option_2_action,
    }
    sub_menu = Menu("Sub Menu", sub_menu_options)

    # Define main menu with a reference to the sub-menu
    main_menu_options = {
        "Option 1": option_1_action,
        "Option 2": option_2_action,
        "Go to Sub Menu": sub_menu,
    }
    main_menu = Menu("Main Menu", main_menu_options)

    # Initialize MenuManager with the main menu
    menu_manager = MenuManager(main_menu)
    return menu_manager

def initialize_menu_manager():
    st.session_state['menu_manager'] = initialize_menus() # Always build fresh menu manager
    st.session_state['menu_manager'].display_current_menu()

#################################
##########   Chat  ##############
#################################

def handle_chat(selected_agent: str, query: str):
    if query:
        agent = st.session_state.agent_handler.create_new_agent(selected_agent)
        response = asyncio.run(generate_and_display_response(agent, query))

        st.session_state.memory_cache.chat_memory.add_user_message(query)
        st.session_state.memory_cache.chat_memory.add_ai_message(response)

async def generate_and_display_response(agent, query: str):
    response = await agent.generate_response(query)
    with st.chat_message('assistant'):
        st.markdown(response)

    return response