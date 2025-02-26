import streamlit as st
import time

from firestore_integration import get_google_cloud_credentials, fetch_users, add_user_by_information, fetch_users_by_email
#, show_all_users, show_one_user, update_one_user
import pandas as pd

ROLES = [None, "User", "Admin"]

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

    #st.sidebar.write(f"Name: {name}")
    #st.sidebar.write(f"Email: {email}")
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
            #st.sidebar.write(f"Role: {role}")


def main_app():
    creds=set_up_credentials()
    initialize_user()
    if "role" not in st.session_state:
        st.session_state.role = None
    role = st.session_state.role
    admin_1 = st.Page("ui/admin.py", title="Admin 1", icon=":material/person_add:", default=(role == "Admin"))
    user_1 = st.Page("ui/user.py", title="User 1", icon=":material/help:", default=(role == "User"))
    acct_1 = st.Page("streamlit_app.py", title="Home", icon=":material/help:", default=False)
    admin_pages = [admin_1]
    user_pages = [user_1]
    acct_pages= [acct_1]

    page_dict = {}
    if st.session_state.role in ["User", "Admin"]:
        page_dict["User"] = user_pages
    if st.session_state.role == "Admin":
        page_dict["Admin"] = admin_pages

    if len(page_dict) > 0:
        pg = st.navigation(page_dict)
    else:
        pg = st.navigation({"Account Def": acct_pages} )
    pg.run()

