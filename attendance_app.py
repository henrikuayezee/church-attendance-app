import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config("Church Attendance", layout="centered")

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = []

# --- FILE PATHS ---
MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
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
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio("Go to", ["📝 Mark Attendance", "📅 View History", "📊 Dashboard"])

    if page == "📝 Mark Attendance":
        attendance_page()
    elif page == "📅 View History":
        history_page()
    elif page == "📊 Dashboard":
        dashboard_page()

# --- PAGE 1: MARK ATTENDANCE ---
def attendance_page():
    st.header("📝 Mark Attendance")

    if not os.path.exists(MEMBER_FILE):
        st.warning("⚠️ No members file found. Please upload one.")
        uploaded = st.file_uploader("Upload member list CSV", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)
            df.to_csv(MEMBER_FILE, index=False)
            st.success("✅ Members list saved.")
            st.rerun()
        else:
            st.stop()

    # Load saved members list
    members_df = pd.read_csv(MEMBER_FILE)

    # Update option
    with st.expander("🔄 Update Member List"):
        update = st.file_uploader("Upload new list", type=["csv"], key="update")
        if update:
            df = pd.read_csv(update)
            df.to_csv(MEMBER_FILE, index=False)
            st.success("✅ Member list updated.")
            st.rerun()

    sunday = st.date_input("Select Sunday", value=date.today())
    group = st.selectbox("Select Group", sorted(members_df["Group"].dropna().unique()))
    group_df = members_df[members_df["Group"] == group].copy()
    present = st.multiselect("Select Present Members:", group_df["Full Name"].tolist())

    group_df["Status"] = group_df["Full Name"].apply(lambda name: "Present" if name in present else "Absent")

    if st.button("✅ Submit Group Attendance"):
        output = group_df[["Membership Number", "Full Name", "Group"]].copy()
        output.insert(0, "Date", sunday)
        output["Status"] = group_df["Status"]
        st.session_state.attendance_data.append(output)

        # Save to all_attendance.csv
        if os.path.exists(MASTER_FILE):
            master_df = pd.read_csv(MASTER_FILE)
            master_df = pd.concat([master_df, output], ignore_index=True)
        else:
            master_df = output.copy()

        master_df.to_csv(MASTER_FILE, index=False)

        st.success(f"✅ Group {group} attendance saved ({output['Status'].value_counts().to_dict()})")

# --- PAGE 2: HISTORY VIEWER ---
def history_page():
    st.header("📅 View Past Attendance")

    if not os.path.exists(MASTER_FILE):
        st.warning("No attendance has been saved yet.")
        return

    df = pd.read_csv(MASTER_FILE)
    df["Date"] = pd.to_datetime(df["Date"])
    dates = sorted(df["Date"].dt.date.unique(), reverse=True)
    
    selected_date = st.selectbox("Select a Sunday", dates)
    filtered = df[df["Date"].dt.date == selected_date]

    st.write(f"Showing attendance for **{selected_date}**")
    st.dataframe(filtered)

    st.download_button(
        label="⬇️ Download CSV for this date",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"attendance_{selected_date}.csv",
        mime="text/csv"
    )

# --- PAGE 3: DASHBOARD ---
def dashboard_page():
    st.header("📊 Attendance Dashboard")

    if not os.path.exists(MASTER_FILE):
        st.warning("No attendance data to analyze.")
        return

    df = pd.read_csv(MASTER_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    latest_date = df["Date"].max().date()
    latest_data = df[df["Date"].dt.date == latest_date]

    st.subheader(f"🗓️ Latest Attendance: {latest_date}")
    group_summary = latest_data.groupby("Group")["Status"].value_counts().unstack().fillna(0)
    group_summary["% Present"] = (group_summary["Present"] / group_summary.sum(axis=1) * 100).round(1)

    st.dataframe(group_summary)

    st.subheader("📈 Member Consistency (Last 4 Weeks)")
    last_4 = df[df["Date"] >= df["Date"].max() - pd.Timedelta(weeks=4)]
    streaks = last_4.groupby("Full Name")["Status"].apply(lambda s: (s == "Present").sum())
    top_absent = streaks[streaks < 2].sort_values()
    if not top_absent.empty:
        st.write("Members present less than 2x in last 4 weeks:")
        st.dataframe(top_absent)

# --- RUN ---
if auth():
    main_app()
