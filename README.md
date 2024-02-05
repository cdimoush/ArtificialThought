Artificial Thought
================== 
Convert audio to text to thought. Exploring utilization of LLM to utilize, condense, and categorize unstructured data, with the hope of generating new data.

---
# Log
## 2024-02-01
Ok goal for today. Write a streamlit app that takes audio and makes summary. 

First pass just rip off the audio app, make your chain a single function from another file, return summary

## 2024-02-03
Found a streamlit audio example that I like for a single button. Click Start Click Stop + Save. 

The next hurdle was passing audio to assemblyai without saving raw audio locally first. Dug around in the 
transcriber class and found a work around by leverging a manual api call to assemblyai to upload file first.

Lets plug in GPT now. Steps....
1. Transcriber Error and Streamlit State Tracking
    - Streamlit is annoying to develop when errors occur. Think you can by pass audio after transcribe by tracking state

2. Plugin you custom langchain chain. Output with st.write
3. Make pretty, squash big frontend bugs only