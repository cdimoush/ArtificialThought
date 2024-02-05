# Native Python libraries
import os
from io import BytesIO
import time
# Third-party libraries
import streamlit as st
import assemblyai as aai
# athought modules
from _audio_module.audio_recorder_streamlit import audio_recorder
from _summary_module.summary_chain import LabelChain, CleanUpChain, SummaryChain 


label_chain = LabelChain()
cleanup_chain = CleanUpChain()
summary_chain = SummaryChain()

# import audio_recorder_streamlit
st.title('Artifical Thought Experiment')

# Get the API key from the environment variable
api_key = os.getenv('ASSEMBLYAI_API_KEY')
# Set the API key in the AssemblyAI settings
aai.settings.api_key = api_key
transcriber = aai.Transcriber()

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

def audio_state_button():
    st.session_state['audio_state'] = not st.session_state['audio_state']

def ai_state_button():
    st.session_state['ai_state'] = not st.session_state['ai_state']

def main():
    # Check if we're in the initial state
    if 'intial_state' not in st.session_state:
        st.session_state['intial_state'] = True
        st.session_state['audio_state'] = True
        st.session_state['ai_state'] = False
        st.session_state['transcript'] = None
        st.session_state['rerender'] = False

    # Capture audio
    # Create a chat message
    with st.chat_message("assistant"):
        st.write("""
            Hello human, welcome to artificial thought experiment....
                 
            Don't get hung up on experiment. Think of it as an experience gifted to us by the grace of Conner Dimoush. 
                 
            We will be exploring the phenomenon of inefficiency of communication. Whether it be verbal human to human dialogue or an internal monologue,
            it can be observed that quanity of words scale autrociously with the complexity of the subject matter.

            This doesn't have to be the case. You'll see why shortly.
                 
            I want you to describe something novel, unique, or interesting. Maybe something you've been thinking about for quite some time, or maybe something that just popped into your head. I will transcribe your message and we will go from there.... 
            """
        )
    
    if st.session_state['audio_state']:
        with st.chat_message("recorder", avatar="🎤"):
            st.write("Click on the microphone to record a message. Click on the microphone again to stop recording.")
            container = st.container(border=True)
            with container:
                audio_bytes = audio_recorder(text='', icon_size='5x', key='main_mic') # Returns audio in bytes (audio/wav)
                st.session_state['audio_bytes'] = audio_bytes

    if st.session_state['audio_bytes']:
        with st.chat_message("user"):
            st.audio(st.session_state['audio_bytes'], format='audio/wav')
        if st.session_state['audio_state']:
            with st.chat_message("assistant"):
                st.write("Looks like some audio was captured. If you're happy with the recording, click the button below to transcribe the audio.")
                st.button('Save Audio', on_click=audio_state_button)

    # AI State - Do Summarization
    if st.session_state['ai_state'] and not st.session_state['rerender']:
        print('entered ai state')
        # Transcribe / Label the audio
        with st.chat_message("assistant"):
            st.write("Give me a second to to listen to the audio and transcribe your message.")
        st.session_state['audio_state'] = False
        audio_bytes = None
        st.session_state['transcript'] = transcribe_audio(transcriber, st.session_state['audio_bytes']).text
        st.session_state['labels'] = LabelChain().invoke({'transcript': st.session_state['transcript']})
        with st.chat_message("user"):
            st.write(st.session_state['transcript'])

        # After the transcription is displayed
        with st.chat_message("assistant"):
            st.write("Now that we have your transcription, let's identify the main topics or themes. This will help us better understand the context of your message.")

        # Invoke the LabelChain and display the labels
        labels = label_chain.invoke({'transcript': st.session_state['transcript']})
        with st.chat_message("assistant"):
            st.write(f"Based on my analysis, the main topics in your message are...")
        with st.chat_message("output", avatar="✅"):
            st.write(', '.join(labels))

        # Introduce the cleanup process
        with st.chat_message("assistant"):
            st.write("Let's move on to the next step. I'll now correct any errors in the transcription to ensure it accurately represents your message.")

        # Invoke the CleanUpChain and display the corrected transcription
        corrected_transcript = cleanup_chain.invoke({'transcript': st.session_state['transcript'], 'labels': labels})['transcript']
        with st.chat_message("user"):
            st.write(f"Here's the corrected transcription: {corrected_transcript}")

        # Introduce the summarization process
        with st.chat_message("assistant"):
            st.write("Now, let's summarize your message. This will help us distill the main points into a concise summary.")

        # Invoke the SummaryChain and display the summary
        summary = summary_chain.invoke({'transcript': corrected_transcript, 'labels': labels})
        with st.chat_message("assistant"):
            st.write(f"Finished!")
        with st.chat_message("output", avatar="✅"):
            st.write(summary)

    if not st.session_state['audio_state'] and not st.session_state['ai_state']:
        with st.chat_message("assistant"):
            st.write("We can now use AI to process the saved audio. Are you ready?")
            st.button('Initialize AI Sequence', on_click=ai_state_button)


if __name__ == "__main__":
    main()