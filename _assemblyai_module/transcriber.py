import os
import assemblyai as aai
import streamlit as st
import asyncio
import time


# Get the API key from the environment variable
api_key = os.getenv('ASSEMBLYAI_API_KEY')

# Set the API key in the AssemblyAI settings
aai.settings.api_key = api_key
transcriber = aai.Transcriber()

def transcribe_url(url):
    try:
        # Transcribe the uploaded audio data
        transcript = transcriber.transcribe(url)
    except Exception as e:
        print(f"Failed to transcribe audio data: {e}")
        return None

    return transcript.text

async def transcribe_stream(url):
    # Start the transcription process
    future = transcriber.transcribe_async(url)
    print(type(future))

    # Wait for the transcription to complete
    transcription = future.result()

    # Return transcription.text
    return transcription.text

async def write_transcript_stream():
    if len(st.session_state['transcript_url_list']) > 0:
        url = st.session_state['transcript_url_list'].pop(0)
        st.session_state['old_url_list'].append(url)
        text = await transcribe_stream(url)
        return text
    else:
        return None
