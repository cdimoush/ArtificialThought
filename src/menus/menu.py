import streamlit as st
from langchain.memory import ConversationBufferMemory

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

    @st.dialog('Menu Selection')
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