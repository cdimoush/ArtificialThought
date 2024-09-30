from src.agents.base_agent import ChainableAgent, register_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from src.agents.agent_registry import register_agent

_RAG_PROMPT_TEMPLATE = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.
{context}
Query: {query}
Helpful Answer:"""

RAG_PROMPT = PromptTemplate(input_variables=["context", "query"], template=_RAG_PROMPT_TEMPLATE)


@register_agent
class PineconeAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = PineconeVectorStore(index_name='langchain-test-index', embedding=self.embeddings)
        self.retriever = self.vector_store.as_retriever()
        super().__init__(title, **kwargs)

    @register_chain
    def rag_chain(self):
        def get_context(inputs):
            query = inputs["query"]
            docs = self.retriever.invoke(query)
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            RunnablePassthrough.assign(context=RunnableLambda(get_context))
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

