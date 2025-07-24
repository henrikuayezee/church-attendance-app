import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config("Church Attendance", layout="centered")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 🔒 Login function
def login():
    st.header("🔐 Admin Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email == "admin@church.org" and password == "secret":
            st.session_state.logged_in = True
            st.rerun()  # ✅ Streamlit 1.25+ compatible
        else:
            st.error("❌ Incorrect credentials.")

# 🔐 Auth gate
def auth():
    if st.session_state.logged_in:
        return True
    else:
        login()
        return False

# 📋 Main attendance app
def main_app():
    st.header("📅 Church Attendance (Phase 1)")
    st.markdown("Upload member list CSV and mark attendance.")

    uploaded = st.file_uploader("Upload members CSV", type=["csv"])

    if uploaded:
        try:
            members_df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return

        # Validate required columns
        required_cols = ["Membership Number", "Full Name", "Group"]
        if not all(col in members_df.columns for col in required_cols):
            st.error(f"CSV must contain columns: {required_cols}")
            return

        # Select Sunday date
        sunday = st.date_input("Select Sunday", value=date.today())

        # Select group
        group_list = sorted(members_df["Group"].dropna().unique())
        group = st.selectbox("Select Group", group_list)

        # Filter group members
        group_df = members_df[members_df["Group"] == group].copy()
        present_names = st.multiselect("Select Present Members:", group_df["Full Name"].tolist())

        # Set attendance status
        group_df["Status"] = group_df["Full Name"].apply(lambda name: "Present" if name in present_names else "Absent")

        if st.button("✅ Save Attendance"):
            output = group_df[["Membership Number", "Full Name", "Group"]].copy()
            output.insert(0, "Date", sunday)
            output["Status"] = group_df["Status"]

            # Save to local /exports folder
            os.makedirs("exports", exist_ok=True)
            filename = f"{sunday}.csv"
            filepath = os.path.join("exports", filename)
            output.to_csv(filepath, index=False)

            st.success(f"Attendance saved to `{filename}`")

            st.download_button(
                label="⬇️ Download Attendance CSV",
                data=output.to_csv(index=False).encode("utf-8"),
                file_name=f"attendance_{sunday}.csv",
                mime="text/csv"
            )

# 🚪 Run app
if auth():
    main_app()
