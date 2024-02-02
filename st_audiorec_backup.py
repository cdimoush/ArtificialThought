# HACKING THIS FILE TO TRY TO GET STREAMS AND MULTIPLE RECORDINGS WORKING
# URL: https://github.com/stefanrmmr/streamlit-audio-recorder

import os
import numpy as np
import streamlit as st
from io import BytesIO
import streamlit.components.v1 as components
import assemblyai as aai

# Define the event handlers
def on_open(session_opened: aai.RealtimeSessionOpened):
    print("Session ID:", session_opened.session_id)

def on_data(transcript: aai.RealtimeTranscript):
    print('Received data....')
    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimeFinalTranscript):
        transcript_text.append(transcript.text + "\n")
    else:
        transcript_text.append(transcript.text)

def on_error(error: aai.RealtimeError):
    print("An error occured:", error)

def on_close():
    print("Closing Session")


def st_audiorec(key='1'):

    # Get the API key from the environment variable
    api_key = os.getenv('ASSEMBLYAI_API_KEY')


    # Define a list to hold the transcript text
    transcript_text = []

    # Create a RealtimeTranscriber
    transcriber = aai.RealtimeTranscriber(
        on_data=on_data,
        on_error=on_error,
        sample_rate=44_100,
        on_open=on_open,
        on_close=on_close,
    )
    # get parent directory relative to current directory
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    # Custom REACT-based component for recording client audio in browser
    build_dir = os.path.join(parent_dir, "frontend/build")
    # specify directory and initialize st_audiorec object functionality
    st_audiorec = components.declare_component(f"st_audiorec_{key}", path=build_dir)

    # Create an instance of the component: STREAMLIT AUDIO RECORDER
    raw_audio_data = st_audiorec()  # raw_audio_data: stores all the data returned from the streamlit frontend
    wav_bytes = None                # wav_bytes: contains the recorded audio in .WAV format after conversion

    # the frontend returns raw audio data in the form of arraybuffer
    # (this arraybuffer is derived from web-media API WAV-blob data)

    if isinstance(raw_audio_data, dict):  # retrieve audio data
        with st.spinner('retrieving audio-recording...'):
            transcriber.connect()

            ind, raw_audio_data = zip(*raw_audio_data['arr'].items())
            ind = np.array(ind, dtype=int)  # convert to np array
            raw_audio_data = np.array(raw_audio_data)  # convert to np array
            sorted_ints = raw_audio_data[ind]
            stream = BytesIO(b"".join([int(v).to_bytes(1, "big") for v in sorted_ints]))
            # wav_bytes contains audio data in byte format, ready to be processed further
            # wav_bytes = stream.read()

            # REAL TIME STUFF....
            # transcriber.connect()
            # Transcribe the audio data using the AssemblyAI API
            print('Streamming audio hold your butts...')
            transcriber.stream(stream)
            # After the transcription process is complete, join the list into a single string
            transcript_string = "".join(transcript_text)
            print(transcript_string)

            
            st.write('Your transcript is....')
            st.write(transcript_string)
            transcriber.close()

    
    return None

    # return wav_bytes