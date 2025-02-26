import streamlit as st
from firestore_integration import fetch_users, add_user_by_information

import pandas as pd


def show_all_users(creds):
    s1=fetch_users(creds)
    df=pd.DataFrame(s1)
    st.dataframe(df, hide_index=True)

def show_one_user(creds):
    s1=fetch_users(creds)
    names=[s.get('name') for s in s1]
    emails=[s.get('email') for s in s1]
    records=[s for s in s1]
    map=dict(zip(names,emails))
    map_records=dict(zip(names,records))
    option = st.selectbox("User",names,index=None)
    if option:
        prv=map_records[option]
        st.dataframe(prv, hide_index=False)


def add_one_user(creds):
    name=st.text_input("Name")
    email=st.text_input("Email")
    if st.button("Insert"):
        user_record={'name':name,'email':email}
        s=add_user_by_information(creds, user_record)
        st.write(s)

def initialize_admin_page():
    st.title("Admin Page")
    name=st.session_state.get('name')
    email=st.session_state.get('email')
    role=st.session_state.get('role')
    st.sidebar.write(f"Name: {name}")
    st.sidebar.write(f"Email: {email}")
    st.sidebar.write(f"Role: {role}")

    if st.sidebar.button("Log out", type="primary", icon=":material/logout:"):
        st.session_state.clear()
        st.logout()

def show_admin_page():
    col1,col2,col3=st.tabs(['User List','User Detail','Insert'])
    creds=st.session_state.get('credentials')
    with col1:
        show_all_users(creds)
    with col2:
        show_one_user(creds)
    with col3:
        add_one_user(creds)


initialize_admin_page()
show_admin_page()