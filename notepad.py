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

    st.session_state.setdefault("retrieve_top_k", 5)

    # [Informal, Casual, Formal, Academic]
    st.session_state.setdefault("formality_level", "Informal")

    if "mood_keywords" not in st.session_state:
        st.session_state["mood_keywords"] = ''

    # OpenAI API init
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    ### UI Elements

    # 2 Tabs
    notepad_tab, chat_tab, settings_tab = st.tabs(["Notepad", "Chat", "Settings"])

    with notepad_tab:

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

        # Notepad Text Area
        st.text_area(
            "",
            height=400,
            key="notepad",
            placeholder="📝 Start writing!"
        )

    with chat_tab:
        
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
        if prompt := st.chat_input("🗨️ Send a message!"):
            st.session_state['chat_history'].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Call the retrieve function to get relevant context
                context_results = retrieve(prompt, st.session_state["retrieve_top_k"])

                # Format the context into a single string
                context_string = "\n".join([
                    f"- Sentence: {result['sentence']} (from '{result['story_title']}')"
                    for result in context_results
                ])

                full_prompt = (
                    f"Here is some related context that might help:\n{context_string}\n\n"
                    f"User Query: {prompt}\n\n"
                    f"Mood Keywords: {st.session_state['mood_keywords']}\n\n"
                    f"Please write in an {st.session_state['formality_level']} tone\n\n"
                    f"Assistant:"
                )

                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": full_prompt}
                        for m in st.session_state['chat_history']
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)

                with st.sidebar.expander("Retrieved Context", expanded=True):
                    for result in context_results:
                        st.write(f"- {result['sentence']} (from '{result['story_title']}')")

            st.session_state['chat_history'].append({"role": "assistant", "content": response})

    with settings_tab:
        # st.write("Test")
        
        retrieve_top_k = st.number_input(
            "🗃️ How much context should I retrieve? (1-10)",
            min_value=1,
            max_value=10,
            step=1,
            key="retrieve_top_k"
        )

        formality_level = st.selectbox(
            "🎩 How formal would you like the text to be?",
            options=["Informal", "Casual", "Formal", "Academic"],
            key="formality_level"
        )

        mood_keywords = st.text_input(
            label="😊 Any keywords for mood?",
            max_chars=200,
            key="mood_keywords")

if __name__ == "__main__":
    main()
