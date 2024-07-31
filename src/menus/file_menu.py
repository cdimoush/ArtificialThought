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
    
