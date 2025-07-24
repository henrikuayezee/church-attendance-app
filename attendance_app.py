import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config("Church Attendance", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 🟢 Define auth() before using it
def auth():
    if st.session_state.logged_in:
        return True
    else:
        login()
        return False

def login():
    st.header("🔐 Admin Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email == "admin@church.org" and password == "secret":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("❌ Incorrect credentials.")

# 🟢 Define main_app() before calling it
def main_app():
    st.header("📅 Church Attendance (Phase 1)")
    st.markdown("Upload member list CSV and mark attendance.")

    uploaded = st.file_uploader("Upload members CSV", type=["csv"])
    if uploaded:
        members_df = pd.read_csv(uploaded)
        required = ["Membership Number", "Full Name", "Group"]
        if not all(col in members_df.columns for col in required):
            st.error(f"CSV must have columns: {required}")
            return

        sunday = st.date_input("Select Sunday", date.today())
        group = st.selectbox("Select Group", sorted(members_df["Group"].unique()))

        group_df = members_df[members_df["Group"] == group].copy()
        present = st.multiselect("Select Present Members:", group_df["Full Name"])

        group_df["Status"] = group_df["Full Name"].apply(lambda name: "Present" if name in present else "Absent")

        if st.button("Save Attendance"):
            output = group_df[["Membership Number", "Full Name", "Group"]].copy()
            output.insert(0, "Date", sunday)
            output["Status"] = group_df["Status"]

            os.makedirs("exports", exist_ok=True)
            file_path = os.path.join("exports", f"{sunday}.csv")
            output.to_csv(file_path, index=False)
            st.success(f"Saved to `{file_path}`")

            st.download_button(
                "⬇️ Download Attendance CSV",
                data=output.to_csv(index=False).encode("utf-8"),
                file_name=f"attendance_{sunday}.csv",
                mime="text/csv"
            )

# ✅ Now safe to call the logic
if auth():
    main_app()
