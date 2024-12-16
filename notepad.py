import streamlit as st
from streamlit_feedback import streamlit_feedback
from openai import OpenAI
import random
import time
import numpy as np
from retrieval import retrieve

def main():
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

    if "notepad" not in st.session_state:
        st.session_state['notepad'] = ""

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"
    
    # Current context and current message content history

    if "cur_msg_context" not in st.session_state:
        st.session_state["cur_msg_context"] = []
    
    if "cur_msg_history" not in st.session_state:
        st.session_state["cur_msg_history"] = []

    st.session_state.setdefault("retrieve_top_k", 5)

    # [Informal, Casual, Formal, Academic]
    st.session_state.setdefault("formality_level", "Informal")

    if "mood_keywords" not in st.session_state:
        st.session_state["mood_keywords"] = ''

    if "character" not in st.session_state:
        st.session_state["character"] = {
            "Name": "",
            "Age": "",
            "Pronouns": "",
            "Personality": "",
            "Traits": "",
        }

    # OpenAI API init
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    ### UI Elements

    # 3 Tabs
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
        # Chat messages container
        global chat_container 
        chat_container = st.container();
        with chat_container:
            for i, message in enumerate(st.session_state['chat_history']):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                

        # Chat input
        user_input = st.chat_input("Send a message!")
        if user_input:
            st.session_state['cur_msg_history'] = []
            # Append user message to chat history
            st.session_state['chat_history'].append({"role": "user", "content": user_input})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_input)

            # Assistant response
            with chat_container:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()  # Dynamic response placeholder

                    # Generate response stream
                    context_results = retrieve(user_input, st.session_state["retrieve_top_k"])
                    st.session_state["cur_msg_context"] = context_results
                    context_string = "\n".join([
                        f"- Sentence: {result['sentence']} (from '{result['story_title']}')"
                        for result in context_results
                    ])
                    full_prompt = (
                        f"Context:\n{context_string}\n\n"
                        f"User Query: {user_input}\n\n"
                        f"Respond in {st.session_state['formality_level']} tone."
                    )
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{"role": "system", "content": full_prompt}],
                        stream=True,
                    )

                    # Dynamically update assistant's response
                    response_text = ""
                    for chunk in stream:
                        chunk_text = chunk.choices[0].delta.content or ""
                        response_text += chunk_text
                        response_placeholder.markdown(response_text)

                    # Append response to chat history
                    st.session_state['chat_history'].append({"role": "assistant", "content": response_text})

                    # Feedback form placed inside the container directly under assistant's response
                    with chat_container:
                        with st.form(f"feedback_form"):
                            streamlit_feedback(
                                feedback_type="thumbs", 
                                optional_text_label="[Optional]",
                                align="flex-start",
                                key="fb_k"
                            )
                            st.form_submit_button("Save feedback", on_click=fbcb)
            
            init_chat_sidebar()

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

        with st.expander("Character Building", expanded=False):
            st.text("Create a character using the template below:")

            # input fields for character
            st.session_state["character"]["Name"] = st.text_input("Name", st.session_state["character"]["Name"])
            st.session_state["character"]["Age"] = st.text_input("Age", st.session_state["character"]["Age"])
            st.session_state["character"]["Pronouns"] = st.text_input("Pronouns", st.session_state["character"]["Pronouns"])
            st.session_state["character"]["Personality"] = st.text_area("Personality", st.session_state["character"]["Personality"], height=100)
            st.session_state["character"]["Traits"] = st.text_area("Traits", st.session_state["character"]["Traits"], height=100)

            # character summary
            st.subheader("Character Summary")
            for key, value in st.session_state["character"].items():
                st.write(f"**{key}:** {value}")

            # clear all fields
            if st.button("Clear Character"):
                for key in st.session_state["character"]:
                    st.session_state["character"][key] = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# refine prompt
def refine_prompt_with_feedback(feedback, client):
    if not feedback:
        return

    # Get the last assistant message
    message_id = len(st.session_state.chat_history) - 1
    if message_id < 0 or st.session_state.chat_history[message_id]["role"] != "assistant":
        return

    last_response = st.session_state.chat_history[message_id]["content"]

    # Append old version to history
    old_version = {
        "content": last_response, 
        "feedback": {
            "score": feedback.get("score", "🤐"),
            "text": feedback.get("text", "No feedback given")
        }
        }
    st.session_state["cur_msg_history"].append(old_version)

    # Create refined prompt
    refined_prompt = f"The user provided feedback: {feedback}. Please refine the previous response accordingly.\n\n" \
                     f"Previous Response: {last_response}\n\nRefined Response:"

    # Call OpenAI API with refined prompt
    response = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "system", "content": "You are an AI that refines responses based on user feedback."},
            {"role": "user", "content": refined_prompt}
        ]
    )

    # Extract refined response
    refined_response = response.choices[0].message.content

    # Update the previous assistant message with "(Refined)" tag
    # st.session_state.chat_history[message_id]["content"] = f"**(Refined)** {refined_response}"
    st.session_state["chat_history"].append({"role": "assistant", "content": f"**(Refined)** {refined_response}"})

    with chat_container:
        with st.form(f"feedback_form"):
            streamlit_feedback(
                feedback_type="thumbs", 
                optional_text_label="[Optional]",
                align="flex-start",
                key="fb_k"
            )
            st.form_submit_button("Save feedback", on_click=fbcb)
    

# feedback callback
def fbcb():
    message_id = len(st.session_state.chat_history) - 1
    if message_id >= 0:
        st.session_state.chat_history[message_id]["feedback"] = st.session_state.fb_k
        refine_prompt_with_feedback(st.session_state.fb_k, client)
        init_chat_sidebar()

def init_chat_sidebar():    
    with st.sidebar:
        st.subheader("🕒 Feedback History")
        if not st.session_state["cur_msg_history"]:
            st.write("Nothing here yet :(")
        else:
            reversed_msg_history = st.session_state["cur_msg_history"]
            reversed_msg_history.reverse()

            for idx, message in enumerate(reversed_msg_history):
                expander_label = ""
                if idx == 0:
                    expander_label = "Initial Message"
                else:
                    expander_label = f"Revision {idx}"
                
                with st.expander(expander_label):
                    formatted_feedback = f"{message['feedback']['score']} {message['feedback']['text']}"
                    st.caption(f"🤖 {message['content']}")
                    st.caption(formatted_feedback)

        st.subheader("📚 Retrieved Context")
        if not st.session_state["cur_msg_context"]:
            st.write("Nothing here yet :(")
        else:
            for result in st.session_state["cur_msg_context"]:
                with st.expander(f"{result['sentence']}"):
                    st.caption(f'from "{result["story_title"]}"')

if __name__ == "__main__":
    main()
