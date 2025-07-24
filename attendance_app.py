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
    return st.session_state.logged_in if st.session_state.logged_in else login() or False

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

        if os.path.exists(MASTER_FILE):
            master_df = pd.read_csv(MASTER_FILE)
            master_df["Date"] = pd.to_datetime(master_df["Date"])
        else:
            master_df = pd.DataFrame(columns=["Date", "Membership Number", "Full Name", "Group", "Status"])

        sunday_str = pd.to_datetime(sunday)
        master_df = master_df[~((master_df["Date"] == sunday_str) & (master_df["Group"] == group))]
        updated_df = pd.concat([master_df, output], ignore_index=True)
        updated_df.to_csv(MASTER_FILE, index=False)

        st.success(f"✅ Saved. Replaced existing attendance for {group} on {sunday}")

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

# --- PAGE 3: ADVANCED DASHBOARD ---
def dashboard_page():
    st.header("📊 Attendance Dashboard")

    if not os.path.exists(MASTER_FILE):
        st.warning("No attendance data to analyze.")
        return

    df = pd.read_csv(MASTER_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    st.markdown("### 🔎 Filter Attendance Records")

    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("📅 Specific Date", value=df["Date"].max().date())
    with col2:
        date_range = st.date_input("📆 Date Range", value=[df["Date"].min().date(), df["Date"].max().date()])

    group_options = sorted(df["Group"].dropna().unique())
    selected_group = st.selectbox("📂 Filter by Group", options=["All"] + group_options)

    person_options = sorted(df["Full Name"].dropna().unique())
    selected_person = st.selectbox("🙍 Filter by Member", options=["All"] + person_options)

    # --- Apply Filters ---
    filtered_df = df.copy()

    if date_filter:
        filtered_df = filtered_df[filtered_df["Date"].dt.date == date_filter]

    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_df = filtered_df[(filtered_df["Date"] >= start) & (filtered_df["Date"] <= end)]

    if selected_group != "All":
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]

    if selected_person != "All":
        filtered_df = filtered_df[filtered_df["Full Name"] == selected_person]

    # --- Summary ---
    st.markdown("### 📊 Summary Table")
    if filtered_df.empty:
        st.warning("No data for selected filters.")
    else:
        summary = filtered_df.groupby(["Date", "Group"])["Status"].value_counts().unstack().fillna(0)
        summary["% Present"] = (summary.get("Present", 0) / summary.sum(axis=1) * 100).round(1)
        st.dataframe(summary)

        with st.expander("📥 View Raw Data"):
            st.dataframe(filtered_df)

        st.download_button(
            label="⬇️ Download Filtered Data",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="filtered_attendance.csv",
            mime="text/csv"
        )

# --- RUN ---
if auth():
    main_app()
