from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone
import time
import typer

class PineconeUploadClient:
    def __init__(self, index_name: str):
        embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone(index_name=index_name, embedding=embeddings)

    def upload(self, data, metadatas=None):
        """ 
        Uploads the chat history to Pinecone. Optionally, provide metadatas for each text. Ensure that the metadatas matches the format expected by the vectorstore add_texts method.
        """
        # Enhance metadatas with the date, if metadatas provided, otherwise create new metadatas
        date_metadata = time.strftime('%Y-%m-%d')
        if metadatas is None:
            metadatas = [{'date': date_metadata} for _ in data]
        else:
            for metadata in metadatas:
                metadata['date'] = date_metadata
        try:
            # Include the metadatas parameter when adding texts
            self.vectorstore.add_texts(texts=data, metadatas=metadatas)
            typer.secho('Uploaded chat history to Pinecone', fg=typer.colors.MAGENTA)
        except Exception as e:
            typer.secho(f'Error uploading to Pinecone: {e}', fg=typer.colors.RED)

def save_conversation(memory_cache, upload_method=''):
    """
    Save the conversation to a file.
    """
    memory = memory_cache.buffer_as_str
    puc = PineconeUploadClient('athought-trainer')
    puc.upload([memory], metadatas=[{'upload_method': upload_method}])