from google.cloud import firestore
from google.oauth2 import service_account

import json

def get_defaults(table_name:str):
    if table_name=="Users":
        return {'role': 'User'}
    return {}

def get_google_cloud_credentials(jstring:str):
    credentials_dict=json.loads(jstring)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)   
    return credentials

    
def fetch_users(credentials):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'Users')
    #query = collection_ref.where('status', '==', 'transcripted')
    docs = collection_ref.stream()
    
    # Collect document IDs that match the query
    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return results

def fetch_users_by_name(credentials,name):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'Users')
    query = collection_ref.where('name', '==', name)
    docs = query.stream()
    
    # Collect document IDs that match the query
    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return results

def fetch_users_by_email(credentials,email):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'Users')
    query = collection_ref.where('email', '==', email)
    docs = query.stream()
    
    # Collect document IDs that match the query
    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return results

def add_user(credentials, incoming_record):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'Users').document() 

    default_record = get_defaults('Users')
    for key in default_record.keys():
        if key not in incoming_record:
            incoming_record[key]=default_record[key]

    incoming_record.setdefault("creationDate", firestore.SERVER_TIMESTAMP)
    collection_ref.set(incoming_record)

def add_user_by_information(credentials, incoming_record):
    email=incoming_record.get('email')
    res=fetch_users_by_email(credentials,email)
    if(len(res)==0):
        add_user(credentials, incoming_record)
        return "Found no match. Adding user."
    elif len(res)==1:
        document_id=res[0].get('id')
        db = firestore.Client(credentials=credentials)
        collection_ref = db.collection(u'test_prompts')
        document_ref = collection_ref.document(document_id)
        name=incoming_record.get('name')
        document_ref.update({'name': name})
        return f"Found one match {res}. Document {document_id} updated: name to {name}"
    else:
        return f"Found multiple matches {res}. Not updating"