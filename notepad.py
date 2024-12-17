import streamlit as st
from streamlit_feedback import streamlit_feedback
from openai import OpenAI
import json
from retrieval import retrieve

def main():
    """
    The main function that sets up the Streamlit app, initializes session state,
    and renders the three main tabs: Notepad, Chat, and Settings.
    """
    # Configure the Streamlit page
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    
    # Apply custom CSS styles
    try:
        with open('styles.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("styles.css not found. Continuing without custom styles.")
    
    # Initialize session state variables if they don't exist
    initialize_session_state()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    # Create the three main tabs
    notepad_tab, chat_tab, settings_tab = st.tabs(["Notepad 🗒️", "Chat 💬", "Settings ⚙️"])
    
    with notepad_tab:
        render_notepad_tab(client)
    
    with chat_tab:
        render_chat_tab(client)
    
    with settings_tab:
        render_settings_tab()

def initialize_session_state():
    """
    Initializes necessary session state variables to maintain state across interactions.
    """
    if "notepad" not in st.session_state:
        st.session_state['notepad'] = ""

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"
    
    if "cur_msg_context" not in st.session_state:
        st.session_state["cur_msg_context"] = []
    
    if "cur_msg_history" not in st.session_state:
        st.session_state["cur_msg_history"] = []

    st.session_state.setdefault("retrieve_top_k", 5)
    st.session_state.setdefault("formality_level", "Informal")
    
    if "mood_keywords" not in st.session_state:
        st.session_state["mood_keywords"] = ''
    
    if "characters" not in st.session_state:
        st.session_state["characters"] = []  # To store multiple characters
    
    if "current_character" not in st.session_state:
        st.session_state["current_character"] = {
            "Name": "",
            "Age": "",
            "Pronouns": "",
            "Personality": "",
            "Traits": "",
            "Additional Information": ""
        }
    
    # Initialize upload_key to manage file uploader reset
    if "upload_key" not in st.session_state:
        st.session_state["upload_key"] = 0

########################################
#################### RENDER AND RELATED FUNCTIONS
########################################

def render_notepad_tab(client):
    """
    Renders the Notepad tab, which includes functionalities to save, load, clear,
    and edit text in a notepad-like interface.

    Args:
        client (OpenAI): The initialized OpenAI client for generating responses.
    """
    # Create four columns for Save, Load, Clear, and Autocomplete functionalities
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

    # Save Expander
    with col1:
        with st.expander("💾 Save File", expanded=False):
            st.write("Save the current content to a downloadable file.")
            filename = st.text_input("Enter filename (with .txt):", value="example.txt", key="save_filename")
            if filename.strip():
                st.download_button(
                    label="Download File",
                    data=st.session_state['notepad'],
                    file_name=filename,
                    mime="text/plain",
                    key="download_notepad"
                )
            else:
                st.error("Please enter a valid filename.")

    # Load Expander
    with col2:
        with st.expander("📂 Load File", expanded=False):
            uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"], accept_multiple_files=False, key="upload_notepad")
            if uploaded_file is not None:
                try:
                    st.session_state['notepad'] = uploaded_file.read().decode("utf-8")
                    st.success("File loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading file: {e}")

    # Clear Expander
    with col3:
        with st.expander("🗑️ Clear Notepad"):
            if st.button("Confirm", key="clear_notepad"):
                st.session_state['notepad'] = ""
                st.info("Notepad cleared.")

    # Autocomplete Expander
    with col4:
        with st.expander("✨ Autocomplete"):
            if st.button("Confirm"):
                # Call OpenAI API with the current notepad content, context and custom prompt
                context_results = retrieve(st.session_state['notepad'], st.session_state["retrieve_top_k"])
                context_string = "\n".join([
                                f"- Sentence: {result['sentence']} (from '{result['story_title']}')"
                                for result in context_results
                            ])
                full_prompt = (
                                f"You are an AI which is designed to autocomplete sentences in a story."
                                f"The current content of the story is as follows: {st.session_state['notepad']}\n\n"
                                f"Context:\n{context_string}\n\n"
                                f"Respond in {st.session_state['formality_level']} tone. "
                                f"Keywords: {st.session_state['mood_keywords']} "
                                f"Characters: {json.dumps(st.session_state['characters'])}"
                                f"It is crucial that you output only the completion of the last sentence, or"
                                f"if the last sentence is finished, it is crucial that you continue the story with only one new sentence."
                            )
                print("\n\n",full_prompt,"\n\n")
                try:
                    response = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": "system", "content": full_prompt}
                        ]
                    )
                except Exception as e:
                    st.error(f"Error communicating with OpenAI API: {e}")
                    return
                st.success(response.choices[0].message.content)
                # Add response to current notepad content

    # Notepad Text Area
    st.text_area(
        "",
        height=400,
        key="notepad",
        placeholder="📝 Start writing!"
    )

def render_chat_tab(client):
    """
    Renders the Chat tab, which includes the chat interface, message handling,
    interaction with the OpenAI API, and feedback mechanisms.
    
    Args:
        client (OpenAI): The initialized OpenAI client for generating responses.
    """
    # Chat messages container
    global chat_container 
    chat_container = st.container()
    with chat_container:
        for message in st.session_state['chat_history']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input from the user
    user_input = st.chat_input("Send a message!")
    if user_input:
        handle_user_input(user_input, client)

def handle_user_input(user_input, client):
    """
    Handles the user input by updating the chat history, generating a response
    from the OpenAI API, and adding feedback functionality.
    
    Args:
        user_input (str): The message input by the user.
        client (OpenAI): The initialized OpenAI client for generating responses.
    """
    # Reset current message history
    st.session_state['cur_msg_history'] = []
    
    # Append user message to chat history
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)

    # Assistant response
    with chat_container:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()  # Placeholder for dynamic response

            # Retrieve relevant context
            context_results = retrieve(user_input, st.session_state["retrieve_top_k"])
            st.session_state["cur_msg_context"] = context_results
            context_string = "\n".join([
                f"- Sentence: {result['sentence']} (from '{result['story_title']}')"
                for result in context_results
            ])
            
            # Construct the prompt for OpenAI
            full_prompt = (
                f"Context:\n{context_string}\n\n"
                f"User Query: {user_input}\n\n"
                f"Respond in {st.session_state['formality_level']} tone. "
                f"Keywords: {st.session_state['mood_keywords']} "
                f"Characters: {json.dumps(st.session_state['characters'])}"
            )
            
            # Generate response stream from OpenAI
            try:
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[{"role": "system", "content": full_prompt}],
                    stream=True,
                )
            except Exception as e:
                st.error(f"Error communicating with OpenAI API: {e}")
                return

            # Dynamically update assistant's response
            response_text = ""
            try:
                for chunk in stream:
                    chunk_text = chunk.choices[0].delta.content or ""
                    response_text += chunk_text
                    response_placeholder.markdown(response_text)
            except Exception as e:
                st.error(f"Error during response streaming: {e}")
                return

            # Append assistant response to chat history
            st.session_state['chat_history'].append({"role": "assistant", "content": response_text})

            # Add feedback form below the assistant's response
            with chat_container:
                with st.form(f"feedback_form_{len(st.session_state['chat_history'])}", clear_on_submit=True):
                    streamlit_feedback(
                        feedback_type="thumbs", 
                        optional_text_label="[Optional]",
                        align="flex-start",
                        key=f"fb_k_{len(st.session_state['chat_history'])}"
                    )
                    st.form_submit_button("Save feedback", on_click=fbcb, args=(len(st.session_state['chat_history'])-1, client))

    # Initialize or update the chat sidebar with feedback and context
    init_chat_sidebar()

def render_settings_tab():
    """
    Renders the Settings tab, which includes options to adjust retrieval settings,
    formality level, mood keywords, and a character builder for managing characters.
    """
    # Retrieval Top K Setting
    st.number_input(
        "🗃️ How much context should I retrieve? (1-10)",
        min_value=1,
        max_value=10,
        step=1,
        key="retrieve_top_k"
    )

    # Formality Level Selection
    st.selectbox(
        "🎩 How formal would you like the text to be?",
        options=["Informal", "Casual", "Formal", "Academic"],
        key="formality_level"
    )

    # Mood Keywords Input
    st.text_input(
        label="😊 Any keywords for mood?",
        max_chars=200,
        key="mood_keywords"
    )

    # Character Builder Section
    with st.expander("🧑‍🤝‍🧑 Character Builder", expanded=False):
        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.text("Create a character using the template below:")

            # Input fields for current character
            st.session_state["current_character"]["Name"] = st.text_input(
                "Name", st.session_state["current_character"]["Name"], key="char_name"
            )
            st.session_state["current_character"]["Age"] = st.text_input(
                "Age", st.session_state["current_character"]["Age"], key="char_age"
            )
            st.session_state["current_character"]["Pronouns"] = st.text_input(
                "Pronouns", st.session_state["current_character"]["Pronouns"], key="char_pronouns"
            )
            st.session_state["current_character"]["Personality"] = st.text_area(
                "Personality", st.session_state["current_character"]["Personality"], height=100, key="char_personality"
            )
            st.session_state["current_character"]["Traits"] = st.text_area(
                "Traits", st.session_state["current_character"]["Traits"], height=100, key="char_traits"
            )
            st.session_state["current_character"]["Additional Information"] = st.text_input(
                "Additional Information", st.session_state["current_character"]["Additional Information"], key="char_additional_info"
            )

            # Button to save the current character
            if st.button("Save Character", key="save_character"):
                if all(st.session_state["current_character"].values()):
                    # Add current character to the list of characters
                    st.session_state["characters"].append(st.session_state["current_character"].copy())
                    # Clear current character fields
                    for key in st.session_state["current_character"]:
                        st.session_state["current_character"][key] = ""
                    st.success("Character saved successfully!")
                else:
                    st.error("Please fill in all character fields before saving.")

            # Button to clear all fields of the current character
            if st.button("Clear Current Character", key="clear_character"):
                for key in st.session_state["current_character"]:
                    st.session_state["current_character"][key] = ""
                st.info("Current character fields cleared.")

        with col2: 
            # Upload JSON File to load characters
            uploaded_file = st.file_uploader("Upload JSON File", type=["json"], key=f"upload_characters_{st.session_state.upload_key}")
            if uploaded_file is not None:
                try:
                    characters = json.load(uploaded_file)
                    if isinstance(characters, list):
                        st.session_state["characters"] = characters
                        st.success("Characters loaded successfully!")
                        # Reset the upload_key to prevent immediate reload
                        st.session_state["upload_key"] +=1
                    else:
                        st.error("Invalid JSON format. Please upload a list of characters.")
                except Exception as e:
                    st.error(f"Error loading file: {e}")

            # Display saved characters
            st.subheader("Saved Characters")
            if st.session_state["characters"]:
                # Create two columns for Download and Clear buttons
                col_download, col_clear = st.columns([2, 1])
                with col_download:
                    if st.button("💾 Download Characters File", key="download_characters"):
                        if st.session_state["characters"]:
                            file_content = json.dumps(st.session_state["characters"], indent=4)
                            st.download_button(
                                label="💾 Download JSON",
                                data=file_content,
                                file_name="characters.json",
                                mime="application/json",
                                key="download_json_button"
                            )
                            st.success("Characters ready for download.")
                        else:
                            st.error("No characters to download.")
                with col_clear:
                    if st.button("🗑️ Clear Characters", key="clear_characters"):
                        st.session_state["characters"] = []
                        st.session_state["upload_key"] +=1  # Reset the uploader
                        st.info("All characters have been cleared.")
                # Display each character
                for idx, character in enumerate(st.session_state["characters"]):
                    st.write(f"### Character {idx + 1}")
                    for key, value in character.items():
                        st.write(f"- **{key}:** {value}")
            else:
                st.info("No characters saved yet. Create one to get started!")

########################################
#################### HELPER FUNCTIONS
########################################

def refine_prompt_with_feedback(feedback, message_id, client):
    """
    Refines the previous assistant response based on user feedback by generating
    a new response from the OpenAI API.
    
    Args:
        feedback (dict): The feedback provided by the user.
        message_id (int): The ID of the message being refined.
        client (OpenAI): The initialized OpenAI client for generating responses.
    """
    if not feedback:
        return

    # Get the last assistant message
    if message_id < 0 or st.session_state.chat_history[message_id]["role"] != "assistant":
        return

    last_response = st.session_state.chat_history[message_id]["content"]

    # Append old version to history with feedback
    old_version = {
        "content": last_response, 
        "feedback": {
            "score": feedback.get("score", "🤐"),
            "text": feedback.get("text", "No feedback given")
        }
    }
    st.session_state["cur_msg_history"].append(old_version)

    # Create refined prompt based on feedback
    refined_prompt = (
        f"The user provided feedback: {feedback}. Please refine the previous response accordingly.\n\n"
        f"Previous Response: {last_response}\n\nRefined Response:"
    )

    # Call OpenAI API with the refined prompt
    try:
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": "You are an AI that refines responses based on user feedback."},
                {"role": "user", "content": refined_prompt}
            ]
        )
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {e}")
        return

    # Extract refined response
    refined_response = response.choices[0].message.content

    # Append the refined response to chat history with a "(Refined)" tag
    st.session_state["chat_history"].append({"role": "assistant", "content": f"**(Refined)** {refined_response}"})

    # Re-render the feedback form for the refined response
    with chat_container:
        with st.form(f"feedback_form_{len(st.session_state['chat_history'])}", clear_on_submit=True):
            streamlit_feedback(
                feedback_type="thumbs", 
                optional_text_label="[Optional]",
                align="flex-start",
                key=f"fb_k_{len(st.session_state['chat_history'])}"
            )
            st.form_submit_button("Save feedback", on_click=fbcb, args=(len(st.session_state['chat_history'])-1, client))

def fbcb(message_id, client):
    """
    Callback function triggered when the feedback form is submitted.
    It saves the feedback and initiates the prompt refinement process.
    
    Args:
        message_id (int): The ID of the message being refined.
        client (OpenAI): The initialized OpenAI client for generating responses.
    """
    feedback_key = f"fb_k_{message_id}"
    if feedback_key in st.session_state:
        feedback = st.session_state[feedback_key]
        st.session_state.chat_history[message_id]["feedback"] = feedback
        refine_prompt_with_feedback(feedback, message_id, client)
        init_chat_sidebar()

def init_chat_sidebar():    
    """
    Initializes or updates the sidebar with feedback history and retrieved context.
    """
    with st.sidebar:
        # Feedback History Section
        st.subheader("🕒 Feedback History")
        if not st.session_state["cur_msg_history"]:
            st.write("Nothing here yet :(")
        else:
            reversed_msg_history = st.session_state["cur_msg_history"].copy()
            reversed_msg_history.reverse()

            for idx, message in enumerate(reversed_msg_history):
                expander_label = "Initial Message" if idx == 0 else f"Revision {idx}"
                
                with st.expander(expander_label):
                    formatted_feedback = f"{message['feedback']['score']} {message['feedback']['text']}"
                    st.caption(f"🤖 {message['content']}")
                    st.caption(formatted_feedback)

        # Retrieved Context Section
        st.subheader("📚 Retrieved Context")
        if not st.session_state["cur_msg_context"]:
            st.write("Nothing here yet :(")
        else:
            for result in st.session_state["cur_msg_context"]:
                with st.expander(f"{result['sentence']}"):
                    st.caption(f'from "{result["story_title"]}"')

if __name__ == "__main__":
    main()
