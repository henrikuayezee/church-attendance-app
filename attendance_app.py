import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Church Attendance System",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    .warning-banner {
        background: linear-gradient(90deg, #ff9800, #f57c00);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa, #e9ecef);
    }
</style>
""", unsafe_allow_html=True)

# File paths
MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

def load_data_safely(file_path):
    """Load CSV data with consistent date formatting"""
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if 'Date' in df.columns:
                # Normalize all dates to YYYY-MM-DD format
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def save_data_safely(df, file_path):
    """Save CSV data with error handling"""
    try:
        # Ensure dates are in correct format before saving
        if 'Date' in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def main_app():
    # Sidebar navigation with icons and styling
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;'>
        <h2 style='color: white; margin: 0;'>⛪ Church Attendance</h2>
        <p style='color: #f0f0f0; margin: 0; font-size: 0.9rem;'>Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation with better icons
    page = st.sidebar.radio(
        "📍 Navigate to:",
        [
            "🏠 Dashboard",
            "📝 Mark Attendance", 
            "📅 View History", 
            "📊 Analytics",
            "📈 Reports",
            "⚙️ Admin Panel"
        ],
        index=0
    )
    
    # Add some sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    
    # Quick stats in sidebar
    try:
        df = load_data_safely(MASTER_FILE)
        if not df.empty:
            total_records = len(df)
            unique_dates = len(df['Date'].unique()) if 'Date' in df.columns else 0
            st.sidebar.metric("📋 Total Records", total_records)
            st.sidebar.metric("📅 Sundays Tracked", unique_dates)
        else:
            st.sidebar.info("No data yet")
    except:
        st.sidebar.info("Loading stats...")
    
    # Route to pages
    if page == "🏠 Dashboard":
        dashboard_home()
    elif page == "📝 Mark Attendance":
        attendance_page()
    elif page == "📅 View History":
        history_page()
    elif page == "📊 Analytics":
        analytics_page()
    elif page == "📈 Reports":
        reports_page()
    elif page == "⚙️ Admin Panel":
        admin_page()

def dashboard_home():
    st.markdown('<div class="main-header">🏠 Dashboard Overview</div>', unsafe_allow_html=True)
    
    # Load data
    df = load_data_safely(MASTER_FILE)
    members_df = load_data_safely(MEMBER_FILE)
    
    if df.empty:
        st.info("👋 Welcome! No attendance data yet. Start by marking attendance or uploading member data in the Admin Panel.")
        
        # Show getting started guide
        st.markdown("### 🚀 Getting Started")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Step 1: Upload Members**
            - Go to Admin Panel
            - Upload your member CSV file
            - Ensure it has: Membership Number, Full Name, Group
            """)
        
        with col2:
            st.markdown("""
            **Step 2: Mark Attendance**
            - Select the Sunday date
            - Choose a group
            - Mark present members
            """)
        
        with col3:
            st.markdown("""
            **Step 3: View Reports**
            - Check Dashboard for overview
            - Use Analytics for insights
            - Generate detailed reports
            """)
        return
    
    # Prepare data
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Key Metrics Row
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_attendance = len(df)
        st.metric(
            label="📋 Total Attendance",
            value=f"{total_attendance:,}",
            help="Total attendance records"
        )
    
    with col2:
        sundays_tracked = df["Date"].nunique()
        st.metric(
            label="📅 Sundays Tracked",
            value=sundays_tracked,
            help="Number of different Sundays with attendance"
        )
    
    with col3:
        active_members = df["Full Name"].nunique()
        st.metric(
            label="👥 Active Members",
            value=active_members,
            help="Unique members who attended at least once"
        )
    
    with col4:
        groups_active = df["Group"].nunique()
        st.metric(
            label="📂 Active Groups",
            value=groups_active,
            help="Groups with recorded attendance"
        )
    
    with col5:
        if sundays_tracked > 0:
            avg_attendance = total_attendance / sundays_tracked
            st.metric(
                label="📈 Avg per Sunday",
                value=f"{avg_attendance:.1f}",
                help="Average attendance per Sunday"
            )
        else:
            st.metric("📈 Avg per Sunday", "0")
    
    # Recent Activity and Trends
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Attendance Trend (Last 8 Weeks)")
        
        # Get last 8 weeks of data
        recent_data = df[df["Date"] >= (datetime.now() - timedelta(weeks=8))]
        weekly_trend = recent_data.groupby("Date").size().reset_index(name="Attendance")
        
        if len(weekly_trend) > 1:
            fig = px.line(
                weekly_trend,
                x="Date",
                y="Attendance",
                markers=True,
                line_shape="spline"
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Date",
                yaxis_title="Total Attendance",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            fig.update_traces(
                line=dict(color="#1f77b4", width=3),
                marker=dict(size=8, color="#ff7f0e")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 data points for trend analysis")
    
    with col2:
        st.markdown("### 🎯 Recent Activity")
        
        # Last 5 attendance records
        recent_records = df.nlargest(5, "Date")[["Date", "Full Name", "Group"]]
        recent_records["Date"] = recent_records["Date"].dt.strftime("%Y-%m-%d")
        
        for _, row in recent_records.iterrows():
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 0.5rem; margin: 0.3rem 0; border-radius: 5px; border-left: 3px solid #28a745;'>
                <strong>{row['Full Name']}</strong><br>
                <small>{row['Group']} • {row['Date']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Group Performance
    st.markdown("### 👥 Group Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Group attendance totals
        group_stats = df.groupby("Group").size().reset_index(name="Total_Attendance")
        group_stats = group_stats.sort_values("Total_Attendance", ascending=True)
        
        fig = px.bar(
            group_stats,
            x="Total_Attendance",
            y="Group",
            orientation="h",
            color="Total_Attendance",
            color_continuous_scale="blues"
        )
        fig.update_layout(
            title="Total Attendance by Group",
            height=400,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Group consistency (how many different weeks they attended)
        group_consistency = df.groupby("Group")["Date"].nunique().reset_index(name="Weeks_Active")
        group_consistency = group_consistency.sort_values("Weeks_Active", ascending=False)
        
        fig = px.bar(
            group_consistency,
            x="Group",
            y="Weeks_Active",
            color="Weeks_Active",
            color_continuous_scale="greens"
        )
        fig.update_layout(
            title="Group Consistency (Weeks Active)",
            height=400,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

def attendance_page():
    st.markdown('<div class="main-header">📝 Mark Attendance</div>', unsafe_allow_html=True)
    
    # Check for members file
    members_df = load_data_safely(MEMBER_FILE)
    if members_df.empty:
        st.warning("⚠️ No members file found. Please upload member data in the Admin Panel first.")
        if st.button("🔗 Go to Admin Panel"):
            st.switch_page("Admin Panel")
        return
    
    # Main form in a nice container
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            sunday = st.date_input(
                "📅 Select Sunday",
                value=date.today(),
                help="Choose the Sunday for attendance marking"
            )
            sunday_str = pd.to_datetime(sunday).strftime("%Y-%m-%d")
        
        with col2:
            available_groups = sorted(members_df["Group"].dropna().unique())
            group = st.selectbox(
                "👥 Select Group",
                available_groups,
                help="Choose the group to mark attendance for"
            )
    
    # Group information
    group_df = members_df[members_df["Group"] == group].copy()
    
    st.info(f"📊 **{group}** has **{len(group_df)}** members total")
    
    # Check for existing attendance
    master_df = load_data_safely(MASTER_FILE)
    existing_attendance = []
    
    if not master_df.empty and "Date" in master_df.columns:
        existing = master_df[
            (master_df["Date"] == sunday_str) & 
            (master_df["Group"] == group)
        ]
        existing_attendance = existing["Full Name"].tolist()
    
    if existing_attendance:
        st.markdown(f"""
        <div class="warning-banner">
            ⚠️ Found {len(existing_attendance)} existing records for {sunday_str} in {group}
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("👀 View existing attendance"):
            for name in existing_attendance:
                st.write(f"✅ {name}")
    
    # Member selection
    st.markdown("### 👤 Select Present Members")
    
    # Search functionality
    search_term = st.text_input(
        "🔍 Search members",
        placeholder="Type to search by name...",
        help="Start typing to filter members"
    )
    
    # Filter members based on search
    if search_term:
        filtered_members = group_df[
            group_df["Full Name"].str.contains(search_term, case=False, na=False)
        ]
        st.info(f"Found {len(filtered_members)} members matching '{search_term}'")
    else:
        filtered_members = group_df
    
    # Member selection with better UI
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        present = st.multiselect(
            "Present Members:",
            filtered_members["Full Name"].tolist(),
            default=existing_attendance,
            help="Select all members who are present today"
        )
    
    with col2:
        if st.button("✅ Select All", help="Select all filtered members"):
            st.session_state.select_all_members = filtered_members["Full Name"].tolist()
    
    with col3:
        if st.button("❌ Clear All", help="Clear all selections"):
            st.session_state.clear_all_members = True
    
    # Handle session state for select/clear all
    if hasattr(st.session_state, 'select_all_members'):
        present = st.session_state.select_all_members
        delattr(st.session_state, 'select_all_members')
        st.rerun()
    
    if hasattr(st.session_state, 'clear_all_members'):
        present = []
        delattr(st.session_state, 'clear_all_members')
        st.rerun()
    
    # Show selection summary
    if present:
        attendance_rate = (len(present) / len(group_df)) * 100
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Selected", len(present))
        with col2:
            st.metric("📊 Attendance Rate", f"{attendance_rate:.1f}%")
        with col3:
            st.metric("❌ Absent", len(group_df) - len(present))
    
    # Submit button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🎯 Submit Attendance",
            type="primary",
            use_container_width=True,
            help="Save attendance records"
        ):
            if not present:
                st.error("⚠️ Please select at least one member as present before submitting.")
                return
            
            # Create attendance records
            new_present_df = group_df[group_df["Full Name"].isin(present)].copy()
            new_present_df["Status"] = "Present"
            new_present_df["Date"] = sunday_str
            
            output = new_present_df[["Date", "Membership Number", "Full Name", "Group", "Status"]]
            
            # Save data
            if not master_df.empty:
                # Remove existing entries for this date/group
                master_df = master_df[~(
                    (master_df["Date"] == sunday_str) & 
                    (master_df["Group"] == group)
                )]
                updated_df = pd.concat([master_df, output], ignore_index=True)
            else:
                updated_df = output.copy()
            
            if save_data_safely(updated_df, MASTER_FILE):
                st.markdown(f"""
                <div class="success-banner">
                    🎉 Successfully saved {len(output)} attendance records for {group} on {sunday_str}!
                </div>
                """, unsafe_allow_html=True)
                
                # Show summary
                st.balloons()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"✅ {len(present)} members marked present")
                with col2:
                    st.info(f"📅 Date: {sunday_str}")
            else:
                st.error("❌ Failed to save attendance. Please try again.")

def history_page():
    st.markdown('<div class="main-header">📅 Attendance History</div>', unsafe_allow_html=True)
    
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.info("📝 No attendance records found. Start by marking attendance!")
        return
    
    # Convert dates
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Filters
    st.markdown("### 🔍 Filter Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dates = sorted(df["Date"].dt.date.unique(), reverse=True)
        selected_date = st.selectbox("📅 Select Date", dates)
    
    with col2:
        groups = ["All Groups"] + sorted(df["Group"].unique())
        selected_group = st.selectbox("👥 Filter by Group", groups)
    
    with col3:
        # Quick date filters
        quick_filter = st.selectbox(
            "⚡ Quick Filter",
            ["Selected Date", "Last Week", "Last Month", "All Time"]
        )
    
    # Apply filters
    if quick_filter == "Last Week":
        week_ago = datetime.now() - timedelta(days=7)
        filtered_df = df[df["Date"] >= week_ago]
    elif quick_filter == "Last Month":
        month_ago = datetime.now() - timedelta(days=30)
        filtered_df = df[df["Date"] >= month_ago]
    elif quick_filter == "All Time":
        filtered_df = df.copy()
    else:  # Selected Date
        filtered_df = df[df["Date"].dt.date == selected_date]
    
    if selected_group != "All Groups":
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]
    
    if filtered_df.empty:
        st.warning("No records found for the selected filters.")
        return
    
    # Summary stats
    st.markdown("### 📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Records", len(filtered_df))
    with col2:
        st.metric("👥 Unique Members", filtered_df["Full Name"].nunique())
    with col3:
        st.metric("📂 Groups", filtered_df["Group"].nunique())
    with col4:
        st.metric("📅 Dates", filtered_df["Date"].nunique())
    
    # Group breakdown
    if len(filtered_df) > 0:
        st.markdown("### 👥 Group Breakdown")
        group_summary = filtered_df.groupby("Group").agg({
            "Full Name": "count",
            "Date": "nunique"
        }).rename(columns={"Full Name": "Total_Attendance", "Date": "Unique_Dates"})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(group_summary, use_container_width=True)
        
        with col2:
            fig = px.pie(
                values=group_summary["Total_Attendance"],
                names=group_summary.index,
                title="Attendance Distribution by Group"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Detailed records
    st.markdown("### 📋 Detailed Records")
    
    # Format the display
    display_df = filtered_df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values(["Date", "Group", "Full Name"], ascending=[False, True, True])
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export options
    st.markdown("### 📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📧 Generate Email List"):
            if "Email" in filtered_df.columns:
                emails = filtered_df["Email"].dropna().unique()
                st.text_area("Email Addresses", "; ".join(emails), height=100)
            else:
                st.info("No email column found in member data")
    
    with col3:
        if st.button("📊 Generate Report"):
            st.info("Report generation feature coming soon!")

def analytics_page():
    st.markdown('<div class="main-header">📊 Analytics & Insights</div>', unsafe_allow_html=True)
    
    df = load_data_safely(MASTER_FILE)
    if df.empty:
        st.info("📈 No data available for analytics. Please mark some attendance first!")
        return
    
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Time range selector
    st.markdown("### 📅 Analysis Period")
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = df["Date"].min().date()
        start_date = st.date_input("Start Date", min_date)
    
    with col2:
        max_date = df["Date"].max().date()
        end_date = st.date_input("End Date", max_date)
    
    # Filter data
    mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
    filtered_df = df.loc[mask]
    
    if filtered_df.empty:
        st.warning("No data in selected date range")
        return
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "👥 Groups", "🎯 Members", "📊 Patterns"])
    
    with tab1:
        st.markdown("#### 📈 Attendance Trends Over Time")
        
        # Weekly trend
        weekly_data = filtered_df.groupby(filtered_df["Date"].dt.to_period("W")).size()
        weekly_df = pd.DataFrame({
            "Week": weekly_data.index.astype(str),
            "Attendance": weekly_data.values
        })
        
        fig = px.line(
            weekly_df,
            x="Week",
            y="Attendance",
            markers=True,
            title="Weekly Attendance Trend"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth metrics
        if len(weekly_df) >= 2:
            recent_avg = weekly_df.tail(4)["Attendance"].mean()
            previous_avg = weekly_df.head(len(weekly_df)-4)["Attendance"].mean() if len(weekly_df) > 4 else weekly_df.head(4)["Attendance"].mean()
            
            growth = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Recent Avg", f"{recent_avg:.1f}")
            with col2:
                st.metric("Previous Avg", f"{previous_avg:.1f}")
            with col3:
                st.metric("Growth", f"{growth:+.1f}%", delta=f"{growth:.1f}%")
    
    with tab2:
        st.markdown("#### 👥 Group Analysis")
        
        # Group performance comparison
        group_stats = filtered_df.groupby("Group").agg({
            "Full Name": ["count", "nunique"],
            "Date": "nunique"
        }).round(2)
        
        group_stats.columns = ["Total_Attendance", "Unique_Members", "Sundays_Active"]
        group_stats["Avg_per_Sunday"] = (group_stats["Total_Attendance"] / group_stats["Sundays_Active"]).round(1)
        group_stats = group_stats.reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(group_stats, use_container_width=True)
        
        with col2:
            # Group comparison radar chart
            fig = px.bar(
                group_stats,
                x="Group",
                y="Avg_per_Sunday",
                color="Avg_per_Sunday",
                title="Average Attendance per Sunday by Group"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("#### 🎯 Member Engagement")
        
        # Member attendance frequency
        member_stats = filtered_df.groupby("Full Name").agg({
            "Date": ["count", "nunique"],
            "Group": "first"
        }).round(2)
        
        member_stats.columns = ["Total_Attendance", "Unique_Sundays", "Group"]
        member_stats = member_stats.reset_index().sort_values("Total_Attendance", ascending=False)
        
        # Top performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏆 Top 10 Most Active Members**")
            top_members = member_stats.head(10)
            st.dataframe(top_members, use_container_width=True, hide_index=True)
        
        with col2:
            # Attendance distribution
            fig = px.histogram(
                member_stats,
                x="Total_Attendance",
                nbins=20,
                title="Member Attendance Distribution"
            )
            fig.update_layout(
                xaxis_title="Number of Attendances",
                yaxis_title="Number of Members"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("#### 📊 Attendance Patterns")
        
        # Day patterns
        filtered_df["Day_of_Month"] = filtered_df["Date"].dt.day
        filtered_df["Month"] = filtered_df["Date"].dt.strftime("%B")
        
        col1, col2 = st.columns(2)
        
        with col1:
            day_pattern = filtered_df.groupby("Day_of_Month").size().reset_index(name="Attendance")
            fig = px.bar(
                day_pattern,
                x="Day_of_Month",
                y="Attendance",
                title="Attendance by Day of Month"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            month_pattern = filtered_df.groupby("Month").size().reset_index(name="Attendance")
            # Order months correctly
            month_order = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            month_pattern["Month"] = pd.Categorical(month_pattern["Month"], categories=month_order, ordered=True)
            month_pattern = month_pattern.sort_values("Month")
            
            fig = px.bar(
                month_pattern,
                x="Month",
                y="Attendance",
                title="Attendance by Month"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def reports_page():
    st.markdown('<div class="main-header">📈 Detailed Reports</div>', unsafe_allow_html=True)
    
    df = load_data_safely(MASTER_FILE)
    members_df = load_data_safely(MEMBER_FILE)
    
    if df.empty:
        st.info("📊 No attendance data available for reports. Please mark some attendance first!")
        return
    
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Report type selector
    report_type = st.selectbox(
        "📋 Select Report Type",
        [
            "📅 Monthly Summary Report",
            "👥 Group Performance Report", 
            "🎯 Member Consistency Report",
            "📊 Attendance Overview Report",
            "📈 Growth Analysis Report"
        ]
    )
    
    # Date range for reports
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Report Start Date", df["Date"].min().date())
    with col2:
        end_date = st.date_input("📅 Report End Date", df["Date"].max().date())
    
    # Filter data by date range
    mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
    report_df = df.loc[mask]
    
    if report_df.empty:
        st.warning("No data available for selected date range")
        return
    
    # Generate selected report
    if report_type == "📅 Monthly Summary Report":
        generate_monthly_report(report_df)
    elif report_type == "👥 Group Performance Report":
        generate_group_report(report_df, members_df)
    elif report_type == "🎯 Member Consistency Report":
        generate_member_report(report_df)
    elif report_type == "📊 Attendance Overview Report":
        generate_overview_report(report_df)
    elif report_type == "📈 Growth Analysis Report":
        generate_growth_report(report_df)

def generate_monthly_report(df):
    st.markdown("### 📅 Monthly Summary Report")
    
    # Monthly breakdown
    df["Month"] = df["Date"].dt.to_period("M")
    monthly_stats = df.groupby(["Month", "Group"]).size().unstack(fill_value=0)
    monthly_stats["Total"] = monthly_stats.sum(axis=1)
    
    st.markdown("#### 📊 Monthly Attendance by Group")
    st.dataframe(monthly_stats, use_container_width=True)
    
    # Monthly trends
    monthly_totals = df.groupby("Month").size().reset_index(name="Total_Attendance")
    monthly_totals["Month_Str"] = monthly_totals["Month"].astype(str)
    
    fig = px.bar(
        monthly_totals,
        x="Month_Str",
        y="Total_Attendance",
        title="Monthly Attendance Totals",
        color="Total_Attendance",
        color_continuous_scale="blues"
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Total Attendance",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly insights
    st.markdown("#### 💡 Monthly Insights")
    
    if len(monthly_totals) >= 2:
        best_month = monthly_totals.loc[monthly_totals["Total_Attendance"].idxmax()]
        worst_month = monthly_totals.loc[monthly_totals["Total_Attendance"].idxmin()]
        avg_monthly = monthly_totals["Total_Attendance"].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Best Month", f"{best_month['Month_Str']}", f"{best_month['Total_Attendance']} attendees")
        with col2:
            st.metric("📉 Lowest Month", f"{worst_month['Month_Str']}", f"{worst_month['Total_Attendance']} attendees")
        with col3:
            st.metric("📊 Monthly Average", f"{avg_monthly:.1f}", "attendees")
    
    # Export option
    csv_data = monthly_stats.to_csv()
    st.download_button(
        "📥 Download Monthly Report",
        csv_data,
        f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

def generate_group_report(df, members_df):
    st.markdown("### 👥 Group Performance Report")
    
    # Group statistics
    group_analysis = df.groupby("Group").agg({
        "Full Name": ["count", "nunique"],
        "Date": "nunique"
    }).round(2)
    
    group_analysis.columns = ["Total_Attendance", "Active_Members", "Sundays_Active"]
    group_analysis["Avg_per_Sunday"] = (group_analysis["Total_Attendance"] / group_analysis["Sundays_Active"]).round(1)
    
    # Add member totals if available
    if not members_df.empty and "Group" in members_df.columns:
        group_totals = members_df.groupby("Group").size().reset_index(name="Total_Members")
        group_analysis = group_analysis.reset_index().merge(group_totals, on="Group", how="left")
        group_analysis["Participation_Rate"] = (
            group_analysis["Active_Members"] / group_analysis["Total_Members"] * 100
        ).round(1)
        group_analysis["Participation_Rate"] = group_analysis["Participation_Rate"].fillna(0)
    
    st.markdown("#### 📊 Group Performance Summary")
    st.dataframe(group_analysis, use_container_width=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            group_analysis,
            x="Group",
            y="Avg_per_Sunday",
            title="Average Attendance per Sunday",
            color="Avg_per_Sunday",
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if "Participation_Rate" in group_analysis.columns:
            fig = px.bar(
                group_analysis,
                x="Group",
                y="Participation_Rate",
                title="Member Participation Rate (%)",
                color="Participation_Rate",
                color_continuous_scale="greens"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Group recommendations
    st.markdown("#### 💡 Recommendations")
    
    if not group_analysis.empty:
        top_group = group_analysis.loc[group_analysis["Avg_per_Sunday"].idxmax()]
        if "Participation_Rate" in group_analysis.columns:
            low_participation = group_analysis[group_analysis["Participation_Rate"] < 50]
            
            if not low_participation.empty:
                st.warning(f"⚠️ Groups with low participation (< 50%): {', '.join(low_participation['Group'].tolist())}")
            
        st.success(f"🏆 {top_group['Group']} has the highest average attendance per Sunday ({top_group['Avg_per_Sunday']} members)")

def generate_member_report(df):
    st.markdown("### 🎯 Member Consistency Report")
    
    # Member statistics
    member_stats = df.groupby("Full Name").agg({
        "Date": ["count", "nunique", "min", "max"],
        "Group": "first"
    }).round(2)
    
    member_stats.columns = ["Total_Attendance", "Unique_Sundays", "First_Attendance", "Last_Attendance", "Group"]
    member_stats = member_stats.reset_index()
    
    # Calculate engagement metrics
    member_stats["Days_Active"] = (
        pd.to_datetime(member_stats["Last_Attendance"]) - 
        pd.to_datetime(member_stats["First_Attendance"])
    ).dt.days + 1
    
    member_stats["Consistency_Score"] = (
        member_stats["Total_Attendance"] / member_stats["Unique_Sundays"] * 100
    ).round(1)
    
    # Filter options
    st.markdown("#### 🔍 Filter Options")
    col1, col2 = st.columns(2)
    
    with col1:
        min_attendance = st.slider(
            "Minimum Attendance Count",
            1, int(member_stats["Total_Attendance"].max()),
            1
        )
    
    with col2:
        selected_group = st.selectbox(
            "Filter by Group",
            ["All Groups"] + sorted(member_stats["Group"].unique())
        )
    
    # Apply filters
    filtered_stats = member_stats[member_stats["Total_Attendance"] >= min_attendance]
    if selected_group != "All Groups":
        filtered_stats = filtered_stats[filtered_stats["Group"] == selected_group]
    
    # Display results
    st.markdown("#### 📋 Member Consistency Data")
    
    # Sort by total attendance
    display_stats = filtered_stats.sort_values("Total_Attendance", ascending=False)
    st.dataframe(display_stats, use_container_width=True, hide_index=True)
    
    # Consistency insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        most_consistent = display_stats.loc[display_stats["Consistency_Score"].idxmax()] if not display_stats.empty else None
        if most_consistent is not None:
            st.metric(
                "🎯 Most Consistent",
                most_consistent["Full Name"],
                f"{most_consistent['Consistency_Score']:.1f}% consistency"
            )
    
    with col2:
        most_active = display_stats.loc[display_stats["Total_Attendance"].idxmax()] if not display_stats.empty else None
        if most_active is not None:
            st.metric(
                "🏆 Most Active",
                most_active["Full Name"],
                f"{most_active['Total_Attendance']} attendances"
            )
    
    with col3:
        avg_attendance = display_stats["Total_Attendance"].mean() if not display_stats.empty else 0
        st.metric(
            "📊 Average Attendance",
            f"{avg_attendance:.1f}",
            "per member"
        )

def generate_overview_report(df):
    st.markdown("### 📊 Attendance Overview Report")
    
    # Key metrics
    total_records = len(df)
    unique_members = df["Full Name"].nunique()
    unique_dates = df["Date"].nunique()
    unique_groups = df["Group"].nunique()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Records", f"{total_records:,}")
    with col2:
        st.metric("👥 Unique Members", unique_members)
    with col3:
        st.metric("📅 Sundays Tracked", unique_dates)
    with col4:
        st.metric("👥 Active Groups", unique_groups)
    
    # Weekly analysis
    st.markdown("#### 📈 Weekly Attendance Pattern")
    
    weekly_data = df.groupby(df["Date"].dt.to_period("W")).agg({
        "Full Name": "count",
        "Group": "nunique"
    }).reset_index()
    
    weekly_data.columns = ["Week", "Total_Attendance", "Groups_Active"]
    weekly_data["Week_Str"] = weekly_data["Week"].astype(str)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=weekly_data["Week_Str"], y=weekly_data["Total_Attendance"], name="Attendance"),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=weekly_data["Week_Str"], y=weekly_data["Groups_Active"], 
                  mode="lines+markers", name="Groups Active"),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text="Week")
    fig.update_yaxes(title_text="Total Attendance", secondary_y=False)
    fig.update_yaxes(title_text="Groups Active", secondary_y=True)
    fig.update_layout(title_text="Weekly Attendance and Group Activity")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.markdown("#### 📊 Summary Statistics")
    
    summary_stats = {
        "Average per Sunday": df.groupby("Date").size().mean(),
        "Peak Attendance": df.groupby("Date").size().max(),
        "Lowest Attendance": df.groupby("Date").size().min(),
        "Most Active Group": df["Group"].value_counts().index[0],
        "Date Range": f"{df['Date'].min().date()} to {df['Date'].max().date()}"
    }
    
    for metric, value in summary_stats.items():
        if isinstance(value, float):
            st.write(f"**{metric}:** {value:.1f}")
        else:
            st.write(f"**{metric}:** {value}")

def generate_growth_report(df):
    st.markdown("### 📈 Growth Analysis Report")
    
    # Calculate growth metrics
    df["Week"] = df["Date"].dt.to_period("W")
    weekly_attendance = df.groupby("Week").size().reset_index(name="Attendance")
    weekly_attendance["Week_Str"] = weekly_attendance["Week"].astype(str)
    
    if len(weekly_attendance) < 2:
        st.warning("Need at least 2 weeks of data for growth analysis")
        return
    
    # Calculate week-over-week growth
    weekly_attendance["Growth"] = weekly_attendance["Attendance"].pct_change() * 100
    weekly_attendance["Growth_Absolute"] = weekly_attendance["Attendance"].diff()
    
    # Growth visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Weekly Attendance", "Week-over-Week Growth %"),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(
            x=weekly_attendance["Week_Str"],
            y=weekly_attendance["Attendance"],
            mode="lines+markers",
            name="Attendance",
            line=dict(color="blue", width=3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=weekly_attendance["Week_Str"],
            y=weekly_attendance["Growth"],
            name="Growth %",
            marker_color=["green" if x >= 0 else "red" for x in weekly_attendance["Growth"]]
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Growth insights
    st.markdown("#### 💡 Growth Insights")
    
    # Calculate key metrics
    avg_growth = weekly_attendance["Growth"].mean()
    positive_weeks = (weekly_attendance["Growth"] > 0).sum()
    negative_weeks = (weekly_attendance["Growth"] < 0).sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📈 Average Growth",
            f"{avg_growth:.1f}%",
            "per week"
        )
    
    with col2:
        st.metric(
            "✅ Positive Weeks",
            positive_weeks,
            f"out of {len(weekly_attendance)-1} weeks"
        )
    
    with col3:
        st.metric(
            "📉 Declining Weeks", 
            negative_weeks,
            f"out of {len(weekly_attendance)-1} weeks"
        )
    
    # Trend analysis
    if len(weekly_attendance) >= 4:
        recent_trend = weekly_attendance.tail(4)["Growth"].mean()
        overall_trend = weekly_attendance["Growth"].mean()
        
        st.markdown("#### 🔍 Trend Analysis")
        
        if recent_trend > overall_trend:
            st.success(f"📈 Recent trend is positive! Last 4 weeks average: {recent_trend:.1f}% vs overall: {overall_trend:.1f}%")
        elif recent_trend < overall_trend:
            st.warning(f"📉 Recent trend is concerning. Last 4 weeks average: {recent_trend:.1f}% vs overall: {overall_trend:.1f}%")
        else:
            st.info(f"📊 Recent trend is stable. Last 4 weeks average: {recent_trend:.1f}%")

def admin_page():
    st.markdown('<div class="main-header">⚙️ Admin Panel</div>', unsafe_allow_html=True)
    
    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "🗃️ Data Management", "⚙️ System Settings"])
    
    with tab1:
        manage_members()
    
    with tab2:
        manage_data()
    
    with tab3:
        system_settings()

def manage_members():
    st.markdown("### 👥 Member List Management")
    
    members_df = load_data_safely(MEMBER_FILE)
    
    if not members_df.empty:
        # Display current members with statistics
        st.success(f"✅ **{len(members_df)}** members currently loaded")
        
        # Group breakdown
        if "Group" in members_df.columns:
            group_counts = members_df["Group"].value_counts()
            st.markdown("**📊 Member Distribution by Group:**")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for group, count in group_counts.items():
                    st.write(f"• **{group}:** {count} members")
            
            with col2:
                fig = px.pie(
                    values=group_counts.values,
                    names=group_counts.index,
                    title="Member Distribution"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # Display member data
        st.markdown("#### 📋 Current Member List")
        st.dataframe(members_df, use_container_width=True, hide_index=True)
        
        # Download current list
        csv_data = members_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Current Member List",
            data=csv_data,
            file_name=f"members_backup_{date.today()}.csv",
            mime="text/csv",
            help="Download a backup of your current member list"
        )
    else:
        st.info("📝 No member data found. Please upload a member list below.")
    
    # Upload new member list
    st.markdown("### 📤 Upload New Member List")
    
    st.info("💡 **CSV Format Required:** Your file should include columns: Membership Number, Full Name, Group")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=["csv"],
        help="Upload a CSV file with member information"
    )
    
    if uploaded_file:
        try:
            # Preview the uploaded file
            new_df = pd.read_csv(uploaded_file)
            
            st.markdown("#### 👀 Preview of Uploaded File")
            st.dataframe(new_df.head(10), use_container_width=True)
            
            # Validate required columns
            required_cols = ["Membership Number", "Full Name", "Group"]
            missing_cols = [col for col in required_cols if col not in new_df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                st.info("Please ensure your CSV has all required columns and try again.")
            else:
                st.success("✅ File format looks good!")
                
                # Show summary
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total Members", len(new_df))
                with col2:
                    st.metric("👥 Groups", new_df["Group"].nunique())
                
                # Confirm upload
                if st.button("✅ Confirm Upload", type="primary"):
                    if save_data_safely(new_df, MEMBER_FILE):
                        st.success("🎉 Member list updated successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to save member list. Please try again.")
                        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.help("Please ensure your file is a valid CSV format.")

def manage_data():
    st.markdown("### 🗃️ Data Management")
    
    # Current data statistics
    df = load_data_safely(MASTER_FILE)
    
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total Records", len(df))
        with col2:
            st.metric("📅 Date Range", f"{(df['Date'].max() - df['Date'].min()).days} days")
        with col3:
            file_size = os.path.getsize(MASTER_FILE) / 1024  # KB
            st.metric("💾 File Size", f"{file_size:.1f} KB")
        with col4:
            last_modified = datetime.fromtimestamp(os.path.getmtime(MASTER_FILE))
            st.metric("🕒 Last Updated", last_modified.strftime("%Y-%m-%d"))
    
    # Data backup and export
    st.markdown("### 💾 Backup & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📦 Create Backup")
        
        if not df.empty:
            backup_name = f"attendance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Full Backup",
                data=csv_data,
                file_name=backup_name,
                mime="text/csv",
                help="Download all attendance data as backup"
            )
        else:
            st.info("No data available for backup")
    
    with col2:
        st.markdown("#### 🧹 Data Cleanup")
        
        st.warning("⚠️ **Danger Zone** - These actions cannot be undone!")
        
        if st.button("🗑️ Clear All Attendance Data", type="secondary"):
            st.warning("This will permanently delete ALL attendance records!")
            
            confirm = st.text_input("Type 'DELETE' to confirm:", key="delete_confirm")
            
            if confirm == "DELETE":
                if st.button("❌ Confirm Deletion", type="secondary"):
                    try:
                        if os.path.exists(MASTER_FILE):
                            os.remove(MASTER_FILE)
                            st.success("✅ All attendance data has been cleared.")
                            st.rerun()
                        else:
                            st.info("No data to clear.")
                    except Exception as e:
                        st.error(f"Error clearing data: {str(e)}")
    
    # Data quality check
    if not df.empty:
        st.markdown("### 🔍 Data Quality Check")
        
        # Check for issues
        issues = []
        
        # Check for missing dates
        null_dates = df["Date"].isna().sum()
        if null_dates > 0:
            issues.append(f"❌ {null_dates} records with missing dates")
        
        # Check for missing names
        null_names = df["Full Name"].isna().sum()
        if null_names > 0:
            issues.append(f"❌ {null_names} records with missing names")
        
        # Check for missing groups
        null_groups = df["Group"].isna().sum()
        if null_groups > 0:
            issues.append(f"❌ {null_groups} records with missing groups")
        
        if issues:
            st.warning("⚠️ **Data Quality Issues Found:**")
            for issue in issues:
                st.write(issue)
        else:
            st.success("✅ Data quality looks good!")

def system_settings():
    st.markdown("### ⚙️ System Settings")
    
    # File locations
    st.markdown("#### 📁 File Locations")
    st.code(f"Members Database: {MEMBER_FILE}")
    st.code(f"Attendance Database: {MASTER_FILE}")
    st.code(f"Export Directory: {EXPORT_DIR}")
    
    # System information
    st.markdown("#### 💻 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Streamlit Version:** {st.__version__}")
        st.write(f"**Pandas Version:** {pd.__version__}")
        st.write(f"**Current Date:** {date.today()}")
    
    with col2:
        st.write(f"**Working Directory:** {os.getcwd()}")
        st.write(f"**Export Directory Exists:** {'✅' if os.path.exists(EXPORT_DIR) else '❌'}")
    
    # Application controls
    st.markdown("### 🔄 Application Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Application"):
            st.rerun()
    
    with col2:
        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared!")
    
    # Version information
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p><strong>Church Attendance Management System</strong></p>
        <p>Version 2.0 | Built with Streamlit & Python</p>
    </div>
    """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    main_app()