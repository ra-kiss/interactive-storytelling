import streamlit as st

def main():
    st.set_page_config(layout="wide")

    if "notepad" not in st.session_state:
        st.session_state['notepad'] = ""

    # Sidebar
    with st.sidebar:
        # Save Expander
        with st.expander("💾 Save File", expanded=False):
          st.write("Save the current content to a downloadable file.")
          filename = st.text_input("Enter filename (with .txt):", value="example.txt")
          if filename.strip(): 
              st.download_button(
                      label="Download File",
                      data=st.session_state['notepad'],
                      file_name=filename,
                      mime="text/plain")
          else: st.error("Please enter a valid filename.")


        # Load Expander
        with st.expander("📂 Load File", expanded=False):
            uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"], accept_multiple_files=False)
            if uploaded_file is not None:
                st.session_state['notepad'] = uploaded_file.read().decode("utf-8")
                st.success("File loaded successfully!")

        # Clear Button
        if st.button("🗑️ Clear Notepad"):
            st.session_state['notepad'] = ""

    # Notepad Text Area
    st.text_area(
        "",
        height=400,
        key="notepad",
    )

if __name__ == "__main__":
    main()
