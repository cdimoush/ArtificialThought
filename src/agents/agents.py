import yaml
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import streamlit as st
import typer

class Agent:
    def __init__(self, title, **kwargs):
        self.title = title
        self.role = kwargs.get('role', 'you are a chat bot that chats.')
        self.model_provider = kwargs.get('model_provider', 'openai')
        self.model = kwargs.get('model', 'gpt-4-0125-preview')

        try:
            self._build_llm()
        except Exception as e:
            st.error(f"Error building LLM: {e}")

    def _build_llm(self):
        if self.model_provider == 'openai':
            self.llm = ChatOpenAI(model=self.model, streaming=True, verbose=False)
        else:
            raise NotImplementedError(f"Model provider {self.model_provider} is not supported.")

    def generate_response(self, query: str, container):
        typer.secho(f"User QUERY:\n {query}", fg=typer.colors.GREEN)
        chain = self._build_chain()
        assistant_response = chain.invoke(
            {'query': query},
            {'callbacks': [StreamHandler(container)]},
        )
        typer.secho(f"Agent RESPONSE:\n {assistant_response}", fg=typer.colors.RED)
        return assistant_response
    
    def _build_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template(self.role),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])

        parser = StrOutputParser()

        chain = RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser

        return chain
    
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text)