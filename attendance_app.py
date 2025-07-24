import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config("Church Attendance", layout="wide", page_icon="⛪")

MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

def load_data_safely(file_path):
    """Safely load CSV data with error handling"""
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return pd.DataFrame()

def save_data_safely(df, file_path):
    """Safely save CSV data with error handling"""
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {str(e)}")
        return False

def validate_member_file(df):
    """Validate member file has required columns"""
    required_cols = ["Membership Number", "Full Name", "Group"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Member file missing required columns: {', '.join(missing_cols)}")
        return False
    return True

def main_app():
    st.sidebar.title("📂 Navigation")
    
    # Add app info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Church Attendance Tracker**")
    st.sidebar.markdown("Version 2.0")
    
    page = st.sidebar.radio("Go to", [
        "📝 Mark Attendance", 
        "📅 View History", 
        "📊 Dashboard", 
        "📈 Reports",
        "⚙️ Admin"
    ])
    
    if page == "📝 Mark Attendance":
        attendance_page()
    elif page == "📅 View History":
        history_page()
    elif page == "📊 Dashboard":
        dashboard_page()
    elif page == "📈 Reports":
        reports_page()
    elif page == "⚙️ Admin":
        admin_page()

# --- PAGE 1: ATTENDANCE ---
def attendance_page():
    st.header("📝 Mark Attendance")
    
    members_df = load_data_safely(MEMBER_FILE)
    if members_df.empty or not validate_member_file(members_df):
        st.warning("⚠️ No valid members file found. Please upload one in the Admin tab.")
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        sunday = st.date_input("Select Sunday", value=date.today())
        sunday_str = pd.to_datetime(sunday).strftime("%Y-%m-%d")
    
    with col2:
        group = st.selectbox("Select Group", sorted(members_df["Group"].dropna().unique()))
    
    group_df = members_df[members_df["Group"] == group].copy()
    
    # Show group statistics
    st.info(f"📊 Total members in {group}: {len(group_df)}")
    
    # Check for existing attendance
    master_df = load_data_safely(MASTER_FILE)
    existing_attendance = []
    if not master_df.empty:
        master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
        sunday_dt = pd.to_datetime(sunday_str)
        existing = master_df[
            (master_df["Date"] == sunday_dt) & 
            (master_df["Group"] == group)
        ]
        existing_attendance = existing["Full Name"].tolist()
    
    if existing_attendance:
        st.warning(f"⚠️ {len(existing_attendance)} member(s) already marked for {sunday_str}")
        with st.expander("View existing attendance"):
            st.write(existing_attendance)
    
    # Member selection with search
    search_term = st.text_input("🔍 Search members", placeholder="Type to search...")
    
    if search_term:
        filtered_members = group_df[group_df["Full Name"].str.contains(search_term, case=False, na=False)]
    else:
        filtered_members = group_df
    
    present = st.multiselect(
        "Select Present Members:", 
        filtered_members["Full Name"].tolist(),
        default=existing_attendance  # Pre-select existing attendance
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Submit Attendance", type="primary"):
            submit_attendance(group_df, present, sunday_str, group)
    
    with col2:
        if st.button("📋 Select All"):
            st.session_state.select_all = True
    
    with col3:
        if st.button("🚫 Clear Selection"):
            st.session_state.clear_all = True

def submit_attendance(group_df, present, sunday_str, group):
    if not present:
        st.warning("⚠️ Please select at least one member as present before submitting.")
        return
    
    new_present_df = group_df[group_df["Full Name"].isin(present)].copy()
    new_present_df["Status"] = "Present"
    new_present_df["Date"] = sunday_str
    
    output = new_present_df[["Date", "Membership Number", "Full Name", "Group", "Status"]]
    
    # Handle existing data
    master_df = load_data_safely(MASTER_FILE)
    if not master_df.empty and "Date" in master_df.columns:
        master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
        master_df = master_df[master_df["Date"].notnull()]
        
        # Remove existing entries for this date/group to avoid true duplicates
        sunday_dt = pd.to_datetime(sunday_str)
        master_df = master_df[~(
            (master_df["Date"] == sunday_dt) & 
            (master_df["Group"] == group)
        )]
        
        updated_df = pd.concat([master_df, output], ignore_index=True)
    else:
        updated_df = output.copy()
    
    if save_data_safely(updated_df, MASTER_FILE):
        st.success(f"✅ {len(output)} member(s) marked Present for {group} on {sunday_str}")
        
        # Show summary stats
        total_members = len(group_df)
        attendance_rate = (len(present) / total_members) * 100
        st.metric("Attendance Rate", f"{attendance_rate:.1f}%", f"{len(present)}/{total_members}")

# --- PAGE 2: HISTORY ---
def history_page():
    st.header("📅 View Past Attendance")
    
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.warning("No attendance has been saved yet.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notnull()]
    
    if df.empty:
        st.warning("No valid attendance records found.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        dates = sorted(df["Date"].dt.date.unique(), reverse=True)
        selected_date = st.selectbox("Select a Sunday", dates)
    
    with col2:
        groups = sorted(df["Group"].dropna().unique())
        selected_group = st.selectbox("Filter by Group", ["All"] + groups)
    
    filtered = df[df["Date"].dt.date == selected_date]
    if selected_group != "All":
        filtered = filtered[filtered["Group"] == selected_group]
    
    st.write(f"Showing attendance for **{selected_date}**")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Present", len(filtered))
    with col2:
        groups_count = filtered["Group"].nunique()
        st.metric("Groups", groups_count)
    with col3:
        if not filtered.empty:
            avg_per_group = len(filtered) / groups_count if groups_count > 0 else 0
            st.metric("Avg per Group", f"{avg_per_group:.1f}")
    
    # Group breakdown
    if not filtered.empty:
        group_summary = filtered.groupby("Group").size().reset_index(name="Count")
        st.subheader("📊 Group Breakdown")
        st.dataframe(group_summary, use_container_width=True)
    
    st.subheader("📋 Detailed Records")
    st.dataframe(filtered, use_container_width=True)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇️ Download CSV for this date",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name=f"attendance_{selected_date}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📧 Generate Email List"):
            if not filtered.empty and "Email" in filtered.columns:
                emails = filtered["Email"].dropna().unique()
                st.text_area("Email Addresses", "\n".join(emails), height=100)

# --- PAGE 3: DASHBOARD ---
def dashboard_page():
    st.header("📊 Attendance Dashboard")
    
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.warning("No attendance data available.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notnull()]
    
    if df.empty:
        st.warning("No valid attendance records found.")
        return
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=df["Date"].min().date())
    with col2:
        end_date = st.date_input("End Date", value=df["Date"].max().date())
    
    # Filter data
    filtered_df = df[
        (df["Date"].dt.date >= start_date) & 
        (df["Date"].dt.date <= end_date)
    ]
    
    if filtered_df.empty:
        st.warning("No data for selected date range.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(filtered_df)
        st.metric("Total Attendance Records", total_records)
    
    with col2:
        unique_dates = filtered_df["Date"].nunique()
        st.metric("Sundays Tracked", unique_dates)
    
    with col3:
        unique_members = filtered_df["Full Name"].nunique()
        st.metric("Unique Members", unique_members)
    
    with col4:
        avg_per_sunday = total_records / unique_dates if unique_dates > 0 else 0
        st.metric("Avg per Sunday", f"{avg_per_sunday:.1f}")
    
    # Charts
    st.subheader("📈 Attendance Trends")
    
    # Weekly attendance chart
    weekly_stats = filtered_df.groupby("Date").size().reset_index(name="Total_Present")
    
    fig = px.line(
        weekly_stats, 
        x="Date", 
        y="Total_Present",
        title="Weekly Attendance Trend",
        markers=True
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Total Present")
    st.plotly_chart(fig, use_container_width=True)
    
    # Group comparison
    col1, col2 = st.columns(2)
    
    with col1:
        group_stats = filtered_df.groupby("Group").size().reset_index(name="Total_Attendance")
        fig = px.bar(
            group_stats, 
            x="Group", 
            y="Total_Attendance",
            title="Total Attendance by Group"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Most active members
        member_stats = filtered_df.groupby("Full Name").size().reset_index(name="Attendance_Count")
        top_members = member_stats.nlargest(10, "Attendance_Count")
        
        fig = px.bar(
            top_members, 
            x="Attendance_Count", 
            y="Full Name",
            orientation="h",
            title="Top 10 Most Active Members"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 4: REPORTS ---
def reports_page():
    st.header("📈 Attendance Reports")
    
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.warning("No attendance data available.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notnull()]
    
    report_type = st.selectbox("Select Report Type", [
        "Monthly Summary",
        "Group Performance",
        "Member Consistency",
        "Attendance Patterns"
    ])
    
    if report_type == "Monthly Summary":
        generate_monthly_report(df)
    elif report_type == "Group Performance":
        generate_group_report(df)
    elif report_type == "Member Consistency":
        generate_member_report(df)
    elif report_type == "Attendance Patterns":
        generate_pattern_report(df)

def generate_monthly_report(df):
    st.subheader("📅 Monthly Attendance Summary")
    
    df["Month"] = df["Date"].dt.to_period("M")
    monthly_stats = df.groupby(["Month", "Group"])["Full Name"].count().unstack(fill_value=0)
    monthly_stats["Total"] = monthly_stats.sum(axis=1)
    
    st.dataframe(monthly_stats)
    
    # Monthly trend chart
    total_monthly = df.groupby("Month").size().reset_index(name="Total_Attendance")
    total_monthly["Month"] = total_monthly["Month"].astype(str)
    
    fig = px.bar(
        total_monthly, 
        x="Month", 
        y="Total_Attendance",
        title="Monthly Attendance Totals"
    )
    st.plotly_chart(fig, use_container_width=True)

def generate_group_report(df):
    st.subheader("👥 Group Performance Analysis")
    
    members_df = load_data_safely(MEMBER_FILE)
    if not members_df.empty:
        # Calculate attendance rates
        group_totals = members_df.groupby("Group").size().reset_index(name="Total_Members")
        group_attendance = df.groupby("Group")["Full Name"].nunique().reset_index(name="Active_Members")
        
        group_analysis = pd.merge(group_totals, group_attendance, on="Group", how="left")
        group_analysis["Active_Members"] = group_analysis["Active_Members"].fillna(0)
        group_analysis["Participation_Rate"] = (group_analysis["Active_Members"] / group_analysis["Total_Members"] * 100).round(1)
        
        st.dataframe(group_analysis)
        
        # Participation rate chart
        fig = px.bar(
            group_analysis,
            x="Group",
            y="Participation_Rate",
            title="Group Participation Rates (%)",
            color="Participation_Rate",
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig, use_container_width=True)

def generate_member_report(df):
    st.subheader("👤 Member Consistency Report")
    
    # Calculate member attendance frequency
    member_stats = df.groupby("Full Name").agg({
        "Date": ["count", "min", "max"],
        "Group": "first"
    }).round(2)
    
    member_stats.columns = ["Attendance_Count", "First_Attendance", "Last_Attendance", "Group"]
    member_stats = member_stats.reset_index()
    member_stats["Days_Active"] = (pd.to_datetime(member_stats["Last_Attendance"]) - 
                                  pd.to_datetime(member_stats["First_Attendance"])).dt.days + 1
    
    # Filter options
    min_attendance = st.slider("Minimum attendance count", 1, int(member_stats["Attendance_Count"].max()), 1)
    filtered_stats = member_stats[member_stats["Attendance_Count"] >= min_attendance]
    
    st.dataframe(filtered_stats.sort_values("Attendance_Count", ascending=False))

def generate_pattern_report(df):
    st.subheader("📊 Attendance Pattern Analysis")
    
    # Day of month patterns
    df["Day_of_Month"] = df["Date"].dt.day
    df["Month_Name"] = df["Date"].dt.strftime("%B")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Which Sundays are most popular?
        day_patterns = df.groupby("Day_of_Month").size().reset_index(name="Count")
        fig = px.bar(day_patterns, x="Day_of_Month", y="Count", 
                    title="Attendance by Day of Month")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Monthly patterns
        month_patterns = df.groupby("Month_Name").size().reset_index(name="Count")
        fig = px.bar(month_patterns, x="Month_Name", y="Count", 
                    title="Attendance by Month")
        fig.update_xaxes(categoryorder="array", 
                        categoryarray=["January", "February", "March", "April", "May", "June",
                                     "July", "August", "September", "October", "November", "December"])
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 5: ADMIN ---
def admin_page():
    st.header("⚙️ Admin Panel")
    
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "🗃️ Data Management", "⚙️ Settings"])
    
    with tab1:
        manage_members()
    
    with tab2:
        manage_data()
    
    with tab3:
        app_settings()

def manage_members():
    st.subheader("👥 Member List Management")
    
    members_df = load_data_safely(MEMBER_FILE)
    if not members_df.empty:
        st.write(f"**Current members:** {len(members_df)}")
        
        # Group breakdown
        if "Group" in members_df.columns:
            group_counts = members_df["Group"].value_counts()
            st.write("**Group breakdown:**")
            for group, count in group_counts.items():
                st.write(f"• {group}: {count} members")
        
        st.dataframe(members_df, use_container_width=True)
        
        # Download current member list
        st.download_button(
            label="⬇️ Download Current Member List",
            data=members_df.to_csv(index=False).encode("utf-8"),
            file_name=f"members_backup_{date.today()}.csv",
            mime="text/csv"
        )
    
    st.subheader("📤 Upload New Member List")
    st.info("CSV should include columns: Membership Number, Full Name, Group")
    
    new_csv = st.file_uploader("Upload New Member CSV", type=["csv"], key="member_upload")
    if new_csv:
        try:
            new_df = pd.read_csv(new_csv)
            st.write("**Preview of uploaded file:**")
            st.dataframe(new_df.head())
            
            if validate_member_file(new_df):
                if st.button("✅ Confirm Upload"):
                    if save_data_safely(new_df, MEMBER_FILE):
                        st.success("✅ Member list updated successfully!")
                        st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

def manage_data():
    st.subheader("🗃️ Data Management")
    
    # Attendance data info
    df = load_data_safely(MASTER_FILE)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notnull()]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Date Range", f"{df['Date'].min().date()} to {df['Date'].max().date()}")
        with col3:
            st.metric("File Size", f"{os.path.getsize(MASTER_FILE) / 1024:.2f} KB")
    
    # Backup and export
    st.subheader("💾 Backup & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 Create Full Backup"):
            if not df.empty:
                backup_name = f"attendance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                st.download_button(
                    label="⬇️ Download Backup",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name=backup_name,
                    mime="text/csv"
                )
    
    with col2:
        if st.button("🧹 Clear All Data", type="secondary"):
            st.warning("⚠️ This will permanently delete all attendance records!")
            if st.button("❌ Confirm Delete", type="secondary"):
                try:
                    if os.path.exists(MASTER_FILE):
                        os.remove(MASTER_FILE)
                        st.success("✅ All attendance data cleared.")
                    else:
                        st.info("No data to clear.")
                except Exception as e:
                    st.error(f"Error clearing data: {str(e)}")

def app_settings():
    st.subheader("⚙️ Application Settings")
    
    st.write("**File Locations:**")
    st.code(f"Members: {MEMBER_FILE}")
    st.code(f"Attendance: {MASTER_FILE}")
    st.code(f"Exports: {EXPORT_DIR}")
    
    st.write("**System Information:**")
    st.write(f"• Streamlit version: {st.__version__}")
    st.write(f"• Python version: {pd.__version__}")
    
    if st.button("🔄 Refresh App"):
        st.rerun()

# --- RUN APP ---
if __name__ == "__main__":
    main_app()