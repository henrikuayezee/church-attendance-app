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

# --- FILE PATHS ---
MEMBER_FILE = "members.csv"
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

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
    st.header("📅 Church Attendance (Persistent Members List)")

    # --- MEMBERS FILE HANDLING ---
    if os.path.exists(MEMBER_FILE):
        members_df = pd.read_csv(MEMBER_FILE)
        st.success("✅ Loaded saved members list.")
    else:
        st.warning("⚠️ No member list found. Please upload a CSV.")
        uploaded = st.file_uploader("Upload members CSV", type=["csv"])
        if uploaded:
            members_df = pd.read_csv(uploaded)
            required = ["Membership Number", "Full Name", "Group"]
            if not all(col in members_df.columns for col in required):
                st.error(f"CSV must contain columns: {required}")
                return
            members_df.to_csv(MEMBER_FILE, index=False)
            st.success("✅ Members list saved successfully.")
            st.rerun()
        else:
            st.stop()

    # --- OPTIONAL UPDATE ---
    with st.expander("🔄 Update Member List"):
        update_file = st.file_uploader("Upload a new CSV to replace current list", type=["csv"], key="update")
        if update_file:
            updated_df = pd.read_csv(update_file)
            required = ["Membership Number", "Full Name", "Group"]
            if not all(col in updated_df.columns for col in required):
                st.error(f"CSV must contain columns: {required}")
            else:
                updated_df.to_csv(MEMBER_FILE, index=False)
                st.success("✅ Member list updated. Refreshing...")
                st.rerun()

    # --- ATTENDANCE FLOW ---
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

    # --- FINAL EXPORT ---
    if st.session_state.attendance_data:
        st.markdown("---")
        st.subheader("📤 Export Combined Attendance")

        all_attendance = pd.concat(st.session_state.attendance_data, ignore_index=True)
        file_name = f"attendance_{sunday}.csv"

        st.download_button(
            label="⬇️ Download All Groups CSV",
            data=all_attendance.to_csv(index=False).encode("utf-8"),
            file_name=file_name,
            mime="text/csv"
        )

        with st.expander("👀 Preview Combined Attendance"):
            st.dataframe(all_attendance)

# --- RUN APP ---
if auth():
    main_app()
