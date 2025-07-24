import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config("Church Attendance", layout="centered")

# --- SESSION STATE SETUP ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = []

# --- AUTH ---
def login():
    st.header("🔐 Admin Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email == "admin@church.org" and password == "secret":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Incorrect credentials.")

def auth():
    if st.session_state.logged_in:
        return True
    else:
        login()
        return False

# --- MAIN APP ---
def main_app():
    st.header("📅 Church Attendance (Multi-Group)")
    st.markdown("Upload member list CSV, mark attendance group-by-group, and export once.")

    uploaded = st.file_uploader("Upload members CSV", type=["csv"])

    if uploaded:
        try:
            members_df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return

        required_cols = ["Membership Number", "Full Name", "Group"]
        if not all(col in members_df.columns for col in required_cols):
            st.error(f"CSV must contain columns: {required_cols}")
            return

        sunday = st.date_input("Select Sunday", value=date.today())
        group_list = sorted(members_df["Group"].dropna().unique())
        group = st.selectbox("Select Group", group_list)

        group_df = members_df[members_df["Group"] == group].copy()
        present_names = st.multiselect("Select Present Members:", group_df["Full Name"].tolist())

        group_df["Status"] = group_df["Full Name"].apply(lambda name: "Present" if name in present_names else "Absent")

        if st.button("✅ Submit Group Attendance"):
            output = group_df[["Membership Number", "Full Name", "Group"]].copy()
            output.insert(0, "Date", sunday)
            output["Status"] = group_df["Status"]

            st.session_state.attendance_data.append(output)

            st.success(f"✅ Group '{group}' attendance saved ({output['Status'].value_counts().to_dict()})")

    # Show final download button if at least one group is submitted
    if st.session_state.attendance_data:
        st.markdown("---")
        st.subheader("📤 Export Combined Attendance")

        all_attendance = pd.concat(st.session_state.attendance_data, ignore_index=True)
        file_name = f"attendance_{date.today()}.csv"

        st.download_button(
            label="⬇️ Download All Groups CSV",
            data=all_attendance.to_csv(index=False).encode("utf-8"),
            file_name=file_name,
            mime="text/csv"
        )

        # Optional: Preview table
        with st.expander("👀 Preview Combined Attendance"):
            st.dataframe(all_attendance)

# --- RUN APP ---
if auth():
    main_app()
