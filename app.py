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


wav_audio_data = st_audiorec()
wav_audio_data_duplicate = st_audiorec(key='2')


# Define a list to hold the transcript text
transcript_text = []

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

# Create a RealtimeTranscriber
transcriber = aai.RealtimeTranscriber(
    on_data=on_data,
    on_error=on_error,
    sample_rate=44_100,
    on_open=on_open,
    on_close=on_close,
)

# OVERWRITE REALTIME TRANSCRIBER FOR NOW
transcriber = aai.Transcriber()



if wav_audio_data is not None:
    # Decode the audio data passed from the frontend
    wav_audio = AudioSegment.from_wav(BytesIO(wav_audio_data))

    # Check if the audio is longer than 3 seconds
    if len(wav_audio) > 3000:
        # REAL TIME STUFF....
        # transcriber.connect()
        # # Transcribe the audio data using the AssemblyAI API
        # print('Audio data retrieved, processing...')
        # transcriber.stream(wav_audio.raw_data)
        # # After the transcription process is complete, join the list into a single string
        # transcript_string = "".join(transcript_text)
        # print(transcript_string)

        
        # st.write('Your transcript is....')
        # st.write(transcript_string)

            # Decode the audio data passed from the frontend
        wav_audio = AudioSegment.from_wav(BytesIO(wav_audio_data))
        mp3_audio = wav_audio.export("output.mp3", format="mp3")

        # Transcribe the audio data using the AssemblyAI API
        print('Audio data retrieved, processing...')
        audio_transcript = transcriber.transcribe('./output.mp3')
        print('You should see the transcript now....')
        st.write('Your transcript is....')
        st.write(audio_transcript.text)
    else:
        print('The recording is too short for transcription. Please record at least 3 seconds of audio.')


