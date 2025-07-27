# Full updated script with analytics, absent tracking, multi-group attendance, backups, Sunday prefill, and progress indicators

import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta

# File paths
MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Utilities
def get_last_sunday():
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)

def load_data_safely(file_path):
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def save_data_with_backup(df, file_path):
    try:
        if os.path.exists(file_path):
            backup_name = file_path.replace(
                ".csv", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            pd.read_csv(file_path).to_csv(backup_name, index=False)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")
        return False

# Streamlit config
st.set_page_config("Church Attendance", "⛪", layout="wide")
st.title("⛪ Church Attendance Management System")

page = st.sidebar.selectbox("Navigate", ["Mark Attendance", "View Records"])

if page == "Mark Attendance":
    members_df = load_data_safely(MEMBER_FILE)
    if members_df.empty:
        st.warning("No member data found. Please upload 'members.csv' with columns: Membership Number, Full Name, Group")
    else:
        selected_date = st.date_input("Select Sunday", value=get_last_sunday())
        selected_date_str = selected_date.strftime("%Y-%m-%d")

        groups = sorted(members_df['Group'].dropna().unique())
        selected_groups = st.multiselect("Select Groups to Mark", groups)

        master_df = load_data_safely(MASTER_FILE)

        for group in selected_groups:
            st.subheader(f"Group: {group}")
            group_df = members_df[members_df['Group'] == group]
            member_names = group_df['Full Name'].tolist()

            preselected = []
            if not master_df.empty:
                preselected = master_df[
                    (master_df['Date'] == selected_date_str) &
                    (master_df['Group'] == group) &
                    (master_df['Status'] == 'Present')
                ]['Full Name'].tolist()

            present = st.multiselect(
                f"Mark Present - {group}",
                member_names,
                default=preselected,
                key=f"present_{group}"
            )

            if st.button(f"Submit Attendance for {group}", key=f"submit_{group}"):
                with st.spinner("Saving attendance..."):
                    master_df = master_df[
                        ~((master_df['Date'] == selected_date_str) & (master_df['Group'] == group))
                    ]

                    present_df = group_df[group_df['Full Name'].isin(present)].copy()
                    absent_df = group_df[~group_df['Full Name'].isin(present)].copy()
                    present_df['Status'] = 'Present'
                    absent_df['Status'] = 'Absent'

                    all_records = pd.concat([present_df, absent_df])
                    all_records['Date'] = selected_date_str
                    all_records = all_records[
                        ['Date', 'Membership Number', 'Full Name', 'Group', 'Status']
                    ]

                    updated_df = pd.concat([master_df, all_records], ignore_index=True)

                    if save_data_with_backup(updated_df, MASTER_FILE):
                        st.success(f"Attendance saved for {group}. Present: {len(present)}, Absent: {len(absent_df)}")
                        st.balloons()
                    else:
                        st.error("Failed to save attendance")

elif page == "View Records":
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.info("No attendance records yet.")
    else:
        df['Date'] = pd.to_datetime(df['Date'])

        st.subheader("📊 Attendance Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Unique Members", df['Full Name'].nunique())
        with col3:
            st.metric("Tracked Sundays", df['Date'].dt.date.nunique())

        st.subheader("📅 Attendance Records")
        st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)

        csv = df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button("Download CSV", data=csv, file_name=f"all_attendance_{timestamp}.csv", mime="text/csv")
