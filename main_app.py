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
        st.error("No email found. Please try a different log-in.")
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
    email=st.text_area("Email")
    if st.button("Insert"):
        user_record={'name':name,'email':email}
        s=add_user_by_information(creds, user_record)
        st.write(s)

def main_app():
    creds=set_up_credentials()
    initialize_user()
    col1,col2,col3=st.tabs(['User List','User Detail','Insert'])
    with col1:
        show_all_users(creds)
    with col2:
        show_one_user(creds)
    with col3:
        add_one_user(creds)