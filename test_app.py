import streamlit as st

st.title('Test App')
main_text = st.empty()

def my_button():
    st.session_state['button_state'] = not st.session_state['button_state']


if 'button_state' not in st.session_state:
    st.session_state['button_state'] = False

if st.session_state['button_state']:
    main_text.text('Button State: True')
else:
    main_text.text('Button State: False')

st.button('Toggle Button State', on_click=my_button)
