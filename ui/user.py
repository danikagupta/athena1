import streamlit as st
from firestore_integration import get_google_cloud_credentials, add_userinput_by_information, add_actionItem_list, fetch_userinputs, fetch_actionitems
from llm_integration import llm_process

import pandas as pd



def initialize_user_page():
    st.title("User Page")
    name=st.session_state.get('name')
    email=st.session_state.get('email')
    role=st.session_state.get('role')
    st.sidebar.write(f"Name: {name}")
    st.sidebar.write(f"Email: {email}")
    st.sidebar.write(f"Role: {role}")
    
    if st.sidebar.button("Log out", type="primary", icon=":material/logout:"):
        st.session_state.clear()
        st.logout()

def show_all_userinputs(creds):
    s1=fetch_userinputs(creds)
    df=pd.DataFrame(s1)
    df = df.drop(columns=["id", "creationDate"])
    st.dataframe(df, hide_index=True)

def show_all_actionitems(creds):
    s1=fetch_actionitems(creds)
    df=pd.DataFrame(s1)
    df = df.drop(columns=["id", "creationDate"])
    st.dataframe(df, hide_index=True)

def accept_user_input():
    user_input=st.text_area("Say whatever is on your mind")
    if st.button("Confirm"):
        st.write(f"You wrote: {user_input}")
        name=st.session_state.get('name')
        email=st.session_state.get('email')
        role=st.session_state.get('role')
        userinput_record={'name':name,'email':email,'role':role,'user_input':user_input}
        credentials = get_google_cloud_credentials(st.secrets.get('GOOGLE_KEY'))
        add_userinput_by_information(credentials,userinput_record)
        rsp_list=llm_process(userinput_record)
        if len(rsp_list)>0:
            add_actionItem_list(credentials,rsp_list)


def show_history():
    tab1,tab2=st.tabs(["Show User Inputs","Show Action Items"])
    credentials=st.session_state.get('credentials')
    with tab1:
        show_all_userinputs(credentials)
    with tab2:
        show_all_actionitems(credentials)

initialize_user_page()
accept_user_input()
show_history()
