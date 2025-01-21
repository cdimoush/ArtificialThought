from src.agents.base_agent import ChainableAgent, register_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from operator import itemgetter
from src.agents.agent_registry import register_agent

import typer

# src/utils/tool_handler.py
import functools
import streamlit as st
from src.app.ui_component import display_info

def tool_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Execute the original function
        result = func(*args, **kwargs)
        method_name = func.__name__
        info_content = str(result)
        info = {method_name: info_content}
        
        # Update the last message's info with the result
        if hasattr(st.session_state, 'memory_handler') and len(st.session_state.memory_handler) > 0:
            # Update the info cache
            st.session_state.memory_handler.update_last_info(info)
        
        # Display the last message with the new info
        display_info(info)
        return result
    return wrapper

_RAG_PROMPT_TEMPLATE = """
# Role
You are a futuristic librarian softwareprogram, specializing in Isaac Sim and Isaac Lab, assisting a user with their query. 

# Task
You've consulted your vast collection of technical books and found some excerpts that might be relevant. 
Now, carefully examine these excerpts to determine their relevances and respond based on following instructions: 

1) If excerpts are relevant to the query:
- Craft a coherent and direct answer, citing your sources. 
- Quote the source material if it makes sense to do so.
- Quotes should be done in markdown blockquote format using ">".
- Quotes should reference the file name and page number of the source material.
- Build example of the source material if it makes sense to do so.

2) If excerpts are NOT relevant to the query:
- Apologize to the user, saying, "Sorry, that is not in the database." 
- Respond short, brief, and dry while being sure to mention that the information is not in the database.

3) If query pertains to chat history:
- Utilize context from chat history and the previous AI responses to answer the query.
- Try to utilize (1) to enrich response with additional relevant information if possible.

# Response Guidelines
Always ensure your responses are backed by the books. Respond in an engaging, conversational manner, 
anticipating further queries from the user.

# Specialization
As a specialist in Isaac Sim and Isaac Lab:
- Isaac Sim is a powerful simulation tool within the NVIDIA Omniverse ecosystem, designed specifically for robotics. It allows users to create, test, and visualize robotic applications in a highly realistic virtual environment.
- Isaac Lab is a framework within Isaac Sim that provides APIs and modular setups for conducting reinforcement learning and imitation learning experiments. It simplifies the process of designing and running robotics experiments, supporting various workflows and connecting to peripheral devices for demonstration purposes.

# Excerpts
{context}

# Query
{query}

# Chat History
{history}

# Helpful Answer
"""

RAG_PROMPT = PromptTemplate(input_variables=["context", "query"], template=_RAG_PROMPT_TEMPLATE)

@register_agent
class IsaacSimAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = PineconeVectorStore(index_name='omniverse-index', embedding=self.embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        super().__init__(title, **kwargs)

    def get_full_doc_context(self, source):
        metadata_filter = {"source": {"$eq": source}}
        results = self.vector_store.similarity_search(
            query="",
            k=500,
            filter=metadata_filter
        )
        sorted_results = sorted(results, key=lambda doc: float(doc.metadata.get('chunk_id', 0)))
        doc_context = ''.join(doc.page_content for doc in sorted_results)

        return doc_context

    @register_chain
    def rag_chain(self):  
        @tool
        def get_context_tool(query: str):
            """
            Get the context of a query from the vector store
            """
            chunks = self.retriever.invoke(query)
            context = ""
            doc_list = []

            for chunk in chunks:
                source = chunk.metadata['source']
                file_name = chunk.metadata['file_name']

                if source not in doc_list:
                    doc_list.append(source)
                    doc_context = self.get_full_doc_context(source)
                    
                    context += f"## Document {len(doc_list)}\n"
                    context += f"### File Name: {file_name}\n"
                    context += f"### Content:\n{doc_context}\n\n"

            return context

        rag_chain = (
            RunnablePassthrough.assign(context=get_context_tool)
            | RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history'))
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

