import streamlit as st
from firestore_integration import get_google_cloud_credentials, fetch_users, add_user_by_information
#, show_all_users, show_one_user, update_one_user
import pandas as pd

def set_up_credentials():
    if 'credentials' not in st.session_state:
        jstr = st.secrets.get('GOOGLE_KEY')
        credentials = get_google_cloud_credentials(jstr)
        st.session_state['credentials']=credentials
    return st.session_state['credentials']

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
    col1,col2,col3=st.tabs(['User List','User Detail','Insert'])
    with col1:
        show_all_users(creds)
    with col2:
        show_one_user(creds)
    with col3:
        add_one_user(creds)