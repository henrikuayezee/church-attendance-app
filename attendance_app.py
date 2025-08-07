
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def init_firebase():
    firebase_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

def load_members():
    try:
        docs = db.collection("members").stream()
        return pd.DataFrame([doc.to_dict() for doc in docs])
    except Exception as e:
        st.error(f"Failed to load members: {e}")
        return pd.DataFrame()

def save_members(df):
    try:
        ref = db.collection("members")
        for doc in ref.stream():
            doc.reference.delete()
        for _, row in df.iterrows():
            ref.add(row.to_dict())
        return True
    except Exception as e:
        st.error(f"Failed to save members: {e}")
        return False

st.title("✅ Firebase Connected Successfully")
members_df = load_members()
st.write("Current Members:", members_df)
