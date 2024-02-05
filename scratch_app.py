# Native Python libraries
# -----------------------
import os
from io import BytesIO
import tempfile
# Third-party libraries
# -----------------------
# Streamlit
import streamlit as st
from audio_module.audio_recorder_streamlit import audio_recorder
# Audio
import assemblyai as aai
from pydub import AudioSegment

st.title('Streamlit Audio -> Summary')

# Get the API key from the environment variable
api_key = os.getenv('ASSEMBLYAI_API_KEY')
# Set the API key in the AssemblyAI settings
aai.settings.api_key = api_key
transcriber = aai.Transcriber()

audio_bytes = audio_recorder() # Returns audio in bytes (audio/wav)

def transcribe_audio(transcriber, audio_bytes):
    # Create a BytesIO object from the audio bytes
    audio_file = BytesIO(audio_bytes)
    try:
        # Upload the audio data
        response = transcriber._client.http_client.post(
            'https://api.assemblyai.com/v2/upload',
            content=audio_file,
        )
        response.raise_for_status()  # Raises an exception if the response contains an HTTP error status code
        audio_url = response.json()["upload_url"]
    except Exception as e:
        st.error(f"Failed to upload audio data: {e}")
        return None

    try:
        # Transcribe the uploaded audio data
        transcript = transcriber.transcribe(audio_url)
    except Exception as e:
        st.error(f"Failed to transcribe audio data: {e}")
        return None

    return transcript

# Use the new function to transcribe the audio bytes
transcript_placeholder = st.empty()
if 'first_time' not in st.session_state:
    st.session_state['first_time'] = True

if st.session_state['first_time']:
    transcript_placeholder.text(f'Please speak your transcription will appear here....')

if audio_bytes:
    transcript_placeholder.text('Loading...')
    transcript = transcribe_audio(transcriber, audio_bytes)
    if transcript: 
        transcript_placeholder.text(transcript.text)
        st.session_state['first_time'] = False
    else:
        transcript_placeholder.text('Transcription failed... Try again....')
        print("Transcription failed")

