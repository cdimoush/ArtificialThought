import streamlit as st
from langchain.memory import ConversationBufferMemory

def clear_memory_cache():
    st.session_state.memory_cache = ConversationBufferMemory(return_messages=True)
    st.success("Memory cache cleared.")

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
                elif callable(action):
                    # If the action is a callable, execute it.
                    action()
                else:
                    st.error("Invalid selection. Please try again.")
            except ValueError:
                st.error("Invalid selection. Please try again.")
        self.display_current_menu()

    def go_back(self):
        if len(self.menu_history) > 1:  # Ensure there's a previous menu to go back to
            self.menu_history.pop()  # Remove the current menu from the history
            self.current_menu = self.menu_history[-1]  # Set the current menu to the previous menu
        else:
            st.warning("You're at the top-level menu. There's no previous menu to go back to.")

class AgentSubMenu(Menu):
    def __init__(self, handler):
        options = {f"{title}": self.make_select_agent_function(handler, title) for idx, title in enumerate(handler.agent_titles)}
        super().__init__("Select an Agent", options)

    def make_select_agent_function(self, handler, title):
        """Returns a function that sets the active agent based on the title."""
        def select_agent():
            handler.active_agent = title
            st.success(f"Selected agent: {title}")
        return select_agent
    
class FileSubMenu(Menu):
    def __init__(self, handler):
        # Dynamically generate options based on files in the directory
        file_names = handler.list_files_in_directory()
        options = {f"{file_name}": self.make_load_file_function(handler, file_name) for file_name in file_names}
        super().__init__("Load Reference Code", options)

    def make_load_file_function(self, handler, file_name):
        """Returns a function that loads the file content into the Streamlit app."""
        def load_file():
            file_content = handler.load_file(file_name)
            if file_content is not None:
                st.text(file_content)  # Display the file content in Streamlit
            else:
                st.error("Failed to load file.")
        return load_file

def initialize_menus():
    main_menu_options = {
        "Select Agent": AgentSubMenu(st.session_state.agent_handler),
        "Load File": FileSubMenu(st.session_state.file_handler),
        "Clear Memory Cache": clear_memory_cache,
    }
    main_menu = Menu("Main Menu", main_menu_options)
    menu_manager = MenuManager(main_menu)
    return menu_manager

def initialize_menu_manager():
    st.session_state['menu_manager'] = initialize_menus()
    st.session_state['menu_manager'].display_current_menu()
