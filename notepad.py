import streamlit as st
from openai import OpenAI
import random
import time
from retrieval import retrieve

def main():
    st.set_page_config(layout="wide")
    st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

    if "notepad" not in st.session_state:
        st.session_state['notepad'] = ""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    # OpenAI API init
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    ### UI Elements

    # Notepad Text Area
    st.text_area(
        "",
        height=400,
        key="notepad",
    )

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 2, 1])

    # Save Expander
    with col1:
        with st.expander("💾 Save File", expanded=False):
            st.write("Save the current content to a downloadable file.")
            filename = st.text_input("Enter filename (with .txt):", value="example.txt")
            if filename.strip(): 
                st.download_button(
                        label="Download File",
                        data=st.session_state['notepad'],
                        file_name=filename,
                        mime="text/plain")
            else:
                st.error("Please enter a valid filename.")

    # Load Expander
    with col2:
        with st.expander("📂 Load File", expanded=False):
            uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"], accept_multiple_files=False)
            if uploaded_file is not None:
                st.session_state['notepad'] = uploaded_file.read().decode("utf-8")
                st.success("File loaded successfully!")

    # Clear Button
    with col3:
        if st.button("🗑️ Clear Notepad"):
            st.session_state['notepad'] = ""

    with st.sidebar:
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []

        # Display chat messages before rendering chat input
        chat_container = st.container()
        with chat_container:
            for message in st.session_state['chat_history']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # React to user input via OpenAI API
        if prompt := st.chat_input("Send a message!"):
            st.session_state['chat_history'].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state['chat_history']
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state['chat_history'].append({"role": "assistant", "content": response})

# Streamed response generator
def response_generator():
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

if __name__ == "__main__":
    main()
