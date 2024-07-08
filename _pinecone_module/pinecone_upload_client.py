from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone
import typer

class PineconeUploadClient:
    def __init__(self, index_name: str):
        embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone(index_name=index_name, embedding=embeddings)

    def upload(self, data):
        try:
            self.vectorstore.add_texts(data)
            typer.secho(f'Uploaded chat history to Pinecone', fg=typer.colors.MAGENTA)
        except Exception as e:
            typer.secho(f'Error uploading to Pinecone: {e}', fg=typer.colors.RED)


