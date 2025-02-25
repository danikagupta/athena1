import streamlit as st

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




initialize_admin_page()