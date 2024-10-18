import streamlit as st
import pandas as pd
from cli import get_model_response, get_all_data

st.title("Chatbot Interface")

tab1, tab2 = st.tabs(["Vector Database", "Chatbot"])

with tab1:
    st.header("Database")
    data = get_all_data("semantic-split")
    st.dataframe(data)


with tab2:

    df = pd.DataFrame([['']*20], columns=['WBC', 'LYMp', 'MIDp', 'NEUTp', 'LYMn', 'MIDn', 'NEUTn', 'RBC',
       'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'RDWSD', 'RDWCV', 'PLT', 'MPV',
       'PDW', 'PCT', 'PLCR'])
    edited_df = st.data_editor(df, hide_index=True)

    # Get blood test biomarkers definitions
    biomarker_dictionary = pd.read_csv("biomarker_dictionary.csv", sep="\t").set_index("biomarker").to_dict()
    blood_test_input_prompt = ""
    
    for i in edited_df.columns[edited_df.loc[0] != ""]:
        blood_test_input_prompt += f"{i} is {biomarker_dictionary["definition"][i]}, the normal range for it is {biomarker_dictionary["normal_range"][i]}, and the patient has a value of {edited_df.loc[0, i]}. "


    instruction = """Based on the blood test results, provide a description of the patient's health condition, 
    give detailed explaning on what each value means, and give recommendations for further actions."""


    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if st.button("Save and begin Chat"):
        st.session_state.messages = []
        if(blood_test_input_prompt != ""):
            prompt = f"{blood_test_input_prompt} {instruction}"
            # st.session_state.messages.append({"role": "assistant", "content": prompt})
            response = get_model_response(prompt)
            
            # Display assistant response in chat message container
            # with st.chat_message("assistant"):
            #     st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask me questions related to blood test"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        conversation_history = ' '.join(msg['content'] for msg in st.session_state.messages if 'content' in msg)
        response = get_model_response(f"{blood_test_input_prompt} {conversation_history} {prompt}")
        # response = f"echo: {prompt}"
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})