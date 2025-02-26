import streamlit as st
import time

from firestore_integration import get_google_cloud_credentials, fetch_users, add_user_by_information, fetch_users_by_email
#, show_all_users, show_one_user, update_one_user
import pandas as pd

def set_up_credentials():
    if 'credentials' not in st.session_state:
        jstr = st.secrets.get('GOOGLE_KEY')
        credentials = get_google_cloud_credentials(jstr)
        st.session_state['credentials']=credentials
    return st.session_state['credentials']

def process_new_user(user_record):
    email=user_record.get('email')
    if email.endswith('@pyxeda.ai'):
        credentials=set_up_credentials()
        add_user_by_information(credentials, user_record)
    else:
        st.error("Non-Pyxeda email found. Please try log in with your Pyxeda.ai account.")
        time.sleep(5)
        st.logout()

def initialize_user():
    name=st.experimental_user.get('name')
    email=st.experimental_user.get('email')

    st.sidebar.write(f"Name: {name}")
    st.sidebar.write(f"Email: {email}")
    st.session_state['name']=name
    st.session_state['email']=email

    if email is None:
        #placeholder = st.empty()
        st.error("No email found. Please try to log in with your Google Account.")
        time.sleep(5)
        #placeholder.empty()
        st.logout()
    else:
        credentials=set_up_credentials()
        s=fetch_users_by_email(credentials,email)
        #st.write(f"Found {len(s)} users with email {email}; s={s}")
        if len(s)==0: # No user found. We should add .pyxeda.ai users to the system; else reject
            process_new_user({'name':name,'email':email})
        else:
            user_record=s[0]
            role=user_record.get('role')
            st.session_state['role']=role
            st.sidebar.write(f"Role: {role}")


def main_app():
    creds=set_up_credentials()
    initialize_user()
    if st.session_state.role == "admin":
        st.navigation(["User", "Admin"], default="Admin")
        st.switch_page("pages/admin.py")
    elif st.session_state.role == "user":
        st.navigation(["User"], default="User")
        st.switch_page("pages/user.py")
    
    #col1,col2,col3=st.tabs(['User List','User Detail','Insert'])
    #with col1:
    #    show_all_users(creds)
    #with col2:
    #    show_one_user(creds)
    #with col3:
    #    add_one_user(creds)