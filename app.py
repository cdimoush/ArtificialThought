import os
import streamlit as st
import assemblyai as aai
from st_audiorec import st_audiorec
from pydub import AudioSegment
from io import BytesIO

st.title('Streamlit Audio -> Summary')

# Get the API key from the environment variable
api_key = os.getenv('ASSEMBLYAI_API_KEY')

# Set the API key in the AssemblyAI settings
aai.settings.api_key = api_key
