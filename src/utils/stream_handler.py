from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st
   
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container: st.container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text)