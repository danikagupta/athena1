import pandas as pd
import streamlit as st
from datetime import datetime
import authlib

from firestore_integration import get_google_cloud_credentials
from main_app import main_app, set_up_credentials

st.title("Athena App 1")


# Function to convert timestamp to human-readable format
def format_timestamp(timestamp):
    try:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return timestamp  # Return original if conversion fails

def main_code():
    key_descriptions = {
        "is_logged_in": "Indicates if the user is currently logged in.",
        "iss": "Issuer Identifier for the issuer of the response.",
        "azp": "Authorized party - the party to which the ID Token was issued.",
        "aud": "Audience - the party for which the ID Token is intended.",
        "sub": "Subject - an identifier for the user, unique among all Google accounts.",
        "email": "The user's email address.",
        "email_verified": "Indicates if the user's email address has been verified.",
        "at_hash": "Access token hash for validating the token.",
        "nonce": "A unique value to associate a client session with an ID Token.",
        "name": "The user's full name.",
        "picture": "URL of the user's profile picture.",
        "given_name": "The user's given name.",
        "family_name": "The user's family name.",
        "iat": "Issued At Time - the time the ID Token was issued.",
        "exp": "Expiration Time - the time the ID Token expires."
    }

    # Create a list of dictionaries for the DataFrame
    data = []
    for key, value in st.experimental_user.items():
        if key in ["iat", "exp"]:
            value = format_timestamp(value)  # Convert timestamps to human-readable format
        description = key_descriptions.get(key, "No description available.")
        data.append({"Key": key, "Value": value, "Description": description})
    df = pd.DataFrame(data)
    with st.sidebar.expander("Key Descriptions", expanded=False):
        #st.html(f"Hello, <span style='color: orange; font-weight: bold;'>{st.experimental_user.name}</span>!")
        st.subheader("User Information", divider=True)
        st.dataframe(df, height=600, hide_index=True)


config_auth_needed=st.secrets.get("AUTH_NEEDED","True").lower()=="true"

auth_needed=config_auth_needed and not st.experimental_user.is_logged_in

if auth_needed:
    if st.sidebar.button("Log in", type="primary", icon=":material/login:"):
        st.login()
else:
    # Display user name
    #main_code()
    set_up_credentials()
    main_app()
    if st.sidebar.button("Log out", type="primary", icon=":material/logout:"):
        st.session_state.clear()
        st.logout()
