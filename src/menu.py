import streamlit as st
from langchain.memory import ConversationBufferMemory

# Local imports
from src.file_handler import FolderNavigator, FileNavigator
from src.agents import AgentHandler

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
        
class AgentMenu(Menu):
    def __init__(self, handler: AgentHandler):
        options = {f"{title}": self.make_select_agent_function(handler, title) for idx, title in enumerate(handler.agent_titles)}
        super().__init__("Select an Agent", options)

    def make_select_agent_function(self, handler, title):
        """Returns a function that sets the active agent based on the title."""
        def select_agent(menu_status, **kwargs):
            handler.active_agent = title
            st.session_state['menu_manager'].reset()
            menu_status.success(f"Selected agent: {title}")
        return select_agent
    
class FolderMenu(Menu):
    def __init__(self, nav: FolderNavigator):
        """Dynamically generate options based on files in the directory. """
        file_names = nav.list_contents()
        options = {f"{name}": self.make_sub_menu(path, folder) for name, path, folder in file_names}
        super().__init__("Select Directory / File", options)

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
    
def clear_memory_cache(menu_status, **kwargs):
    st.session_state.memory_cache = ConversationBufferMemory(return_messages=True)
    menu_status.success("Memory cache cleared.")

def initialize_menus():
    main_menu_options = {
        "Select Agent": AgentMenu(st.session_state.agent_handler),
        "Load File": FolderMenu(st.session_state.file_handler.get_nav()),
        "Clear Memory Cache": clear_memory_cache,
    }
    main_menu = Menu("Main Menu", main_menu_options)
    menu_manager = MenuManager(main_menu)
    return menu_manager

def initialize_menu_manager():
    st.session_state['menu_manager'] = initialize_menus()
