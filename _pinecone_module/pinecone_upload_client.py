from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone

class PineconeUploadClient:
    def __init__(self, index_name: str):
        embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone(index_name=index_name, embedding=embeddings)

    def upload(self, data):
        try:
            self.vectorstore.add_texts(data)
        except Exception as e:
            print(f'Could not upload data to Pinecone: {e}')


