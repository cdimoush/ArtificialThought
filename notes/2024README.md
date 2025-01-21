Artificial Thought
================== 
NEW APP
Genesis adoption

OLD APP
Convert audio to text to thought. Exploring utilization of LLM to utilize, condense, and categorize unstructured data, with the hope of generating new data.

---
# Log

## 2024-09-27
Breaking apart agent files!!!
## 2024-07-28
Been using the app! This is good, merging in a nightly I've been working on to add metadata to pinecone upload. What I want now is a simple chain that does REACT for every query.

## 2024-07-07
Good work this weekend, changed layout for drafting and dialogue menu. Going to push back to render after the following....

1. [DONE] Better file loading
1.1. [DONE] Add fences
1.2. Add class or method loading options
1.3. [DONE] Some files don't load bug!
2. [DONE] Standard Menu Status display
3. [Done] Display selected agent
3.1 [DONE] Need auto reload after menu dialogue 
4. [DONE] Handle response no query bug
5. Clean up

Going forward it would nice to 
1. Toggle in and out of draft mode
2. Add a save button
3. View agents and loaded files

## 2024-06-28
Add some crazy recursive menu awhile back, starting to dig in again. Working on loading files.


## 2024-04-07
The stripped down chat bot wrapper is working. 

Added drop down for selecting parameters and a placeholder to add microphone input back in.

Focus now is finalize the cleanup pass then start building crew-ai plug in. 

## 2024-03-21
Ok made the 'artificial thought experiment' app. I want to nuke it now and make a generic chat bot wrapper that I can layer features on top of. I save the current work in a branch called 'artificial_thought_experiment'.

Work to develope microphone module and database module can be plugged back into the chat bot wrapper.


## 2024-02-03
Found a streamlit audio example that I like for a single button. Click Start Click Stop + Save. 

The next hurdle was passing audio to assemblyai without saving raw audio locally first. Dug around in the 
transcriber class and found a work around by leverging a manual api call to assemblyai to upload file first.

Lets plug in GPT now. Steps....
1. Transcriber Error and Streamlit State Tracking
    - Streamlit is annoying to develop when errors occur. Think you can by pass audio after transcribe by tracking state

2. Plugin you custom langchain chain. Output with st.write
3. Make pretty, squash big frontend bugs only
## 2024-02-01
Ok goal for today. Write a streamlit app that takes audio and makes summary. 

First pass just rip off the audio app, make your chain a single function from another file, return summary