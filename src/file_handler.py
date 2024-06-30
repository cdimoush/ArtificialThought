import yaml
import os
import sys
from typing import Union
import streamlit as st

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
            if not os.path.isdir(dir):
                print(f"Directory '{dir}' does not exist.")
            else:
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
    """ 
    Object for opening and reading files.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = os.path.basename(file_path)

    def load_file(self):
        with open(self.file_path, 'r') as file:
            st.session_state.file_handler.add_file_content(self.name, file.read())

class FileHandler:
    """ 
    Object to be used by session state to
    1) Store loaded contents
    2) Store parameters for file navigation
        -> Be able to produce top-level FolderNavigator objects
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.file_content = {}

    def get_nav(self) -> FolderNavigator:
        return FolderNavigator(self.load_dirs(self.config_path))

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
        output = "(START FILE REFERENCE SECTION)\n NOTE: HUMAN HAS ATTACHED THE FOLLOWING REFERENCE FILES\n"
        for header, content in self.file_content.items():
            output += f"\n--{header}--\n{content}\n\n"
        output += "(END FILE REFERENCE SECTION)\n"
        self.clear_file_content()
        return output

    def clear_file_content(self) -> None:
        self.file_content = {}