import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

st.set_page_config("Church Attendance", layout="wide")

MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def main_app():
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio("Go to", ["📝 Mark Attendance", "📅 View History", "📊 Dashboard", "⚙️ Admin"])

    if page == "📝 Mark Attendance":
        attendance_page()
    elif page == "📅 View History":
        history_page()
    elif page == "📊 Dashboard":
        dashboard_page()
    elif page == "⚙️ Admin":
        admin_page()

# --- PAGE 1: ATTENDANCE ---
def attendance_page():
    st.header("📝 Mark Attendance")

    if not os.path.exists(MEMBER_FILE):
        st.warning("⚠️ No members file found. Please upload one in the Admin tab.")
        st.stop()

    members_df = pd.read_csv(MEMBER_FILE)

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

        sunday_dt = pd.to_datetime(sunday)

        # ✅ FIXED: Check duplicates only for the same group + date + name
        duplicate_names = []
        for name in output["Full Name"]:
            is_duplicate = (
                (master_df["Date"] == sunday_dt) &
                (master_df["Full Name"] == name) &
                (master_df["Group"] == group)
            ).any()
            if is_duplicate:
                duplicate_names.append(name)

        if duplicate_names:
            st.error(f"⚠️ These member(s) already have attendance for {sunday} in {group}: {', '.join(duplicate_names)}")
        else:
            master_df = master_df[~((master_df["Date"] == sunday_dt) & (master_df["Group"] == group))]
            updated_df = pd.concat([master_df, output], ignore_index=True)
            updated_df.to_csv(MASTER_FILE, index=False)
            st.success(f"✅ Attendance saved for {group} on {sunday}")

# --- PAGE 2: HISTORY ---
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
        st.warning("No attendance data available.")
        return

    df = pd.read_csv(MASTER_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    st.markdown("### 🔎 Filter Options")
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("📅 Specific Date", value=df["Date"].max().date())
    with col2:
        date_range = st.date_input("📆 Date Range", value=[df["Date"].min().date(), df["Date"].max().date()])

    group_options = sorted(df["Group"].dropna().unique())
    selected_group = st.selectbox("📂 Filter by Group", options=["All"] + group_options)

    person_options = sorted(df["Full Name"].dropna().unique())
    selected_person = st.selectbox("🙍 Filter by Member", options=["All"] + person_options)

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

    if filtered_df.empty:
        st.warning("No data for selected filters.")
        return

    st.subheader("📋 Summary Table")
    summary = filtered_df.groupby(["Date", "Group"])["Status"].value_counts().unstack().fillna(0)
    summary["Total"] = summary.sum(axis=1)
    summary["% Present"] = (summary.get("Present", 0) / summary["Total"] * 100).round(1)
    st.dataframe(summary)

    st.subheader("📊 Visual Charts")

    chart_df = summary.reset_index()
    if "Present" not in chart_df.columns:
        chart_df["Present"] = 0
    fig1 = px.bar(chart_df, x="Group", y="% Present", color="Group", title="% Present by Group")
    st.plotly_chart(fig1, use_container_width=True)

    time_df = filtered_df.groupby(["Date", "Group"])["Status"].value_counts().unstack().fillna(0).reset_index()
    if "Present" not in time_df.columns:
        time_df["Present"] = 0
    fig2 = px.line(time_df, x="Date", y="Present", color="Group", title="Attendance Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# --- PAGE 4: ADMIN ---
def admin_page():
    st.header("⚙️ Admin Panel")

    st.subheader("📁 Member List")
    if os.path.exists(MEMBER_FILE):
        member_df = pd.read_csv(MEMBER_FILE)
        st.dataframe(member_df)

    new_csv = st.file_uploader("Upload New Member CSV", type=["csv"], key="member_upload")
    if new_csv:
        pd.read_csv(new_csv).to_csv(MEMBER_FILE, index=False)
        st.success("✅ Member list updated.")
        st.rerun()

    st.subheader("🧹 Clear Attendance Data")
    if st.button("❌ Delete all attendance records"):
        if os.path.exists(MASTER_FILE):
            os.remove(MASTER_FILE)
            st.success("✅ all_attendance.csv cleared.")
        else:
            st.info("Nothing to delete.")

# --- RUN ---
main_app()
