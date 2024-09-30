# %% [markdown]
# # Meta Rag with Pinecone
# (20240926) Making the meta rag example work with Pinecone
# 

# %%
import os
import getpass
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import time


# %%
## Initialize Pinecone

pc = Pinecone()

index_name = "langchain-test-index"
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embeddings dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)

index = pc.Index(index_name)


# %%
## Document Loading and Splitting

pdf_loader = PyPDFLoader("documents/building_llm_applications_book.pdf")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
embeddings_model = OpenAIEmbeddings()

# Load and split the PDF
pdf_documents = pdf_loader.load()
pdf_chunks = text_splitter.split_documents(pdf_documents)

print(f"Number of chunks: {len(pdf_chunks)}")

if pdf_chunks:
    first_chunk = pdf_chunks[0]
    print(f"Content of the first chunk: {first_chunk.page_content[:100]}...")
    print(f"Metadata of the first chunk: {first_chunk.metadata}")

# %%
## Initialize Pinecone Vector Store
vector_store = PineconeVectorStore(index=index, embedding=embeddings_model)

# Add documents to the vector store
vector_store.add_documents(pdf_chunks)


# %%
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.schema import StrOutputParser

string_output_parser = StrOutputParser()


import json

def create_debug_wrapper(name=""):
    def debug_wrapper(x):
        print(f"\n--- Debug: {name} Input ---")
        print(json.dumps(x, indent=2, default=str))
        return x  # Just pass through the input
    return RunnableLambda(debug_wrapper)

rag_prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.
{context}
Question: {question}
Helpful Answer:"""

rag_prompt = PromptTemplate.from_template(rag_prompt_template)
retriever = vector_store.as_retriever()

chatbot = ChatOpenAI(model_name="gpt-4o-mini")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    }
    | create_debug_wrapper("Context and Question")
    | rag_prompt 
    | create_debug_wrapper("Formatted Prompt")
    | chatbot 
    | create_debug_wrapper("ChatBot Response")
    | string_output_parser
)

def execute_chain(chain, question):
    print("\n=== Starting RAG Chain Execution ===\n")
    answer = chain.invoke(question)
    print("\n=== RAG Chain Execution Complete ===\n")
    return answer

# %%
answer = rag_chain.invoke("tell me about tokens")


