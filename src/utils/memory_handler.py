import streamlit as st
from langchain.memory import ConversationBufferMemory

class MemoryHandler:
    """
    Class that wraps the memory cache to store additional information in info_cache.

    info_cache is a list of dictionaries that store additional information, it must be 
    the same length as the number of messages in the chat history.

    # Include inherient iterability from MemoryCache to zip together messages and info
    """
    def __init__(self, memory_cache: ConversationBufferMemory):
        self.memory_cache = memory_cache
        self.info_cache = []
        if len(self.memory_cache.chat_memory.messages) > 0:
            for _ in range(len(self.memory_cache.chat_memory.messages)):
                self.info_cache.append({})

    def __iter__(self):
        return zip(self.memory_cache.chat_memory.messages, self.info_cache)
    
    def __len__(self):
        return len(self.memory_cache.chat_memory.messages)
    
    def __getitem__(self, index):
        return self.memory_cache.chat_memory.messages[index], self.info_cache[index]

    def add_user_message(self, message: str, info: dict = {}):
        self.memory_cache.chat_memory.add_user_message(message)
        self.info_cache.append(info)

    def add_ai_message(self, message: str, info: dict = {}):
        self.memory_cache.chat_memory.add_ai_message(message)
        self.info_cache.append(info)

    def update_last_message(self, message: str, info: dict = {}):
        self.memory_cache.chat_memory.messages[-1].content = message
        self.info_cache[-1] = info

    def append_last_message(self, message: str):
        """
        Append text to the content of the last message in the chat history.
        """
        self.memory_cache.chat_memory.messages[-1].content += message

    def update_last_info(self, info: dict):
        """
        Update or add new key-value pairs to the info dictionary of the last message.
        """
        self.info_cache[-1].update(info)