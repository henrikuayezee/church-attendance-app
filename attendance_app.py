import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
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
</style>
""", unsafe_allow_html=True)

class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.members_sheet = None
        self.attendance_sheet = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize Google Sheets connection"""
        try:
            # Get credentials from Streamlit secrets
            credentials_dict = st.secrets["google_sheets"]
            
            # Create credentials object
            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            
            self.client = gspread.authorize(credentials)
            
            # Open or create spreadsheet
            spreadsheet_name = st.secrets.get("spreadsheet_name", "Church Attendance System")
            
            try:
                self.spreadsheet = self.client.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet if it doesn't exist
                self.spreadsheet = self.client.create(spreadsheet_name)
                st.info(f"✅ Created new spreadsheet: {spreadsheet_name}")
            
            # Get or create worksheets
            self.setup_worksheets()
            
        except Exception as e:
            st.error(f"""
            ❌ **Google Sheets Connection Failed**
            
            Error: {str(e)}
            
            Please check:
            1. Google Sheets credentials are properly configured in Streamlit secrets
            2. Service account has access to Google Sheets API
            3. Spreadsheet permissions are correct
            """)
            self.client = None
    
    def setup_worksheets(self):
        """Setup required worksheets"""
        try:
            # Members worksheet
            try:
                self.members_sheet = self.spreadsheet.worksheet("Members")
            except gspread.WorksheetNotFound:
                self.members_sheet = self.spreadsheet.add_worksheet(
                    title="Members", rows=1000, cols=10
                )
                # Add headers
                self.members_sheet.update('A1:E1', [[
                    'Membership Number', 'Full Name', 'Group', 'Email', 'Phone'
                ]])
            
            # Attendance worksheet
            try:
                self.attendance_sheet = self.spreadsheet.worksheet("Attendance")
            except gspread.WorksheetNotFound:
                self.attendance_sheet = self.spreadsheet.add_worksheet(
                    title="Attendance", rows=10000, cols=10
                )
                # Add headers
                self.attendance_sheet.update('A1:F1', [[
                    'Date', 'Membership Number', 'Full Name', 'Group', 'Status', 'Timestamp'
                ]])
                
        except Exception as e:
            st.error(f"Error setting up worksheets: {str(e)}")
    
    def is_connected(self):
        """Check if Google Sheets is connected"""
        return self.client is not None and self.spreadsheet is not None
    
    def load_members(self):
        """Load members from Google Sheets"""
        if not self.is_connected():
            return pd.DataFrame()
        
        try:
            with st.spinner("Loading members from Google Sheets..."):
                data = self.members_sheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Clean empty rows
                if not df.empty:
                    df = df[df['Membership Number'].astype(str).str.strip() != '']
                
                return df
        except Exception as e:
            st.error(f"Error loading members: {str(e)}")
            return pd.DataFrame()
    
    def save_members(self, df):
        """Save members to Google Sheets"""
        if not self.is_connected():
            return False
        
        try:
            with st.spinner("Saving members to Google Sheets..."):
                # Clear existing data (except headers)
                self.members_sheet.clear()
                
                # Add headers
                headers = ['Membership Number', 'Full Name', 'Group', 'Email', 'Phone']
                self.members_sheet.update('A1:E1', [headers])
                
                # Prepare data
                data = []
                for _, row in df.iterrows():
                    data.append([
                        str(row.get('Membership Number', '')),
                        str(row.get('Full Name', '')),
                        str(row.get('Group', '')),
                        str(row.get('Email', '')),
                        str(row.get('Phone', ''))
                    ])
                
                # Update sheet
                if data:
                    range_name = f'A2:E{len(data) + 1}'
                    self.members_sheet.update(range_name, data)
                
                return True
                
        except Exception as e:
            st.error(f"Error saving members: {str(e)}")
            return False
    
    def load_attendance(self):
        """Load attendance from Google Sheets"""
        if not self.is_connected():
            return pd.DataFrame()
        
        try:
            with st.spinner("Loading attendance from Google Sheets..."):
                data = self.attendance_sheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Clean empty rows
                if not df.empty:
                    df = df[df['Date'].astype(str).str.strip() != '']
                
                return df
        except Exception as e:
            st.error(f"Error loading attendance: {str(e)}")
            return pd.DataFrame()
    
    def save_attendance(self, df, attendance_date, group_name):
        """Save attendance records to Google Sheets"""
        if not self.is_connected():
            return False
        
        try:
            with st.spinner("Saving attendance to Google Sheets..."):
                # Load existing data
                existing_df = self.load_attendance()
                
                # Remove existing records for this date/group
                if not existing_df.empty:
                    existing_df = existing_df[
                        ~((existing_df['Date'] == attendance_date) & 
                          (existing_df['Group'] == group_name))
                    ]
                
                # Prepare new records
                new_records = []
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for _, row in df.iterrows():
                    new_records.append({
                        'Date': attendance_date,
                        'Membership Number': str(row['Membership Number']),
                        'Full Name': str(row['Full Name']),
                        'Group': str(row['Group']),
                        'Status': 'Present',
                        'Timestamp': timestamp
                    })
                
                # Combine with existing data
                if not existing_df.empty:
                    updated_df = pd.concat([existing_df, pd.DataFrame(new_records)], ignore_index=True)
                else:
                    updated_df = pd.DataFrame(new_records)
                
                # Clear and update sheet
                self.attendance_sheet.clear()
                
                # Add headers
                headers = ['Date', 'Membership Number', 'Full Name', 'Group', 'Status', 'Timestamp']
                self.attendance_sheet.update('A1:F1', [headers])
                
                # Add data
                if not updated_df.empty:
                    data = updated_df.values.tolist()
                    range_name = f'A2:F{len(data) + 1}'
                    self.attendance_sheet.update(range_name, data)
                
                return True
                
        except Exception as e:
            st.error(f"Error saving attendance: {str(e)}")
            return False
    
    def get_existing_attendance(self, attendance_date, group_name):
        """Get existing attendance for specific date and group"""
        df = self.load_attendance()
        
        if df.empty:
            return []
        
        existing = df[
            (df['Date'] == attendance_date) & 
            (df['Group'] == group_name)
        ]
        
        return existing['Full Name'].tolist()
    
    def get_stats(self):
        """Get database statistics"""
        try:
            members_df = self.load_members()
            attendance_df = self.load_attendance()
            
            stats = {
                'total_members': len(members_df),
                'total_attendance': len(attendance_df),
                'unique_dates': len(attendance_df['Date'].unique()) if not attendance_df.empty else 0,
                'spreadsheet_url': self.spreadsheet.url if self.spreadsheet else ''
            }
            
            return stats
        except:
            return {}

# Initialize Google Sheets manager
@st.cache_resource
def get_sheets_manager():
    return GoogleSheetsManager()

def show_setup_instructions():
    """Show Google Sheets setup instructions"""
    st.markdown("## 🔧 Google Sheets Setup Instructions")
    
    with st.expander("📋 Complete Setup Guide", expanded=True):
        st.markdown("""
        ### 1. Create Google Cloud Project
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project: "Church Attendance System"
        3. Enable Google Sheets API and Google Drive API
        
        ### 2. Create Service Account
        1. Go to **IAM & Admin** → **Service Accounts**
        2. Click **Create Service Account**
        3. Name: `church-attendance-service`
        4. Download the JSON credentials file
        
        ### 3. Create Google Spreadsheet
        1. Go to [Google Sheets](https://sheets.google.com)
        2. Create new spreadsheet: "Church Attendance System"
        3. Share with your service account email (Editor permissions)
        
        ### 4. Configure Streamlit Secrets
        Create `.streamlit/secrets.toml` file and paste your JSON credentials.
        """)

sheets = get_sheets_manager()

def main_app():
    # Check connection status
    if not sheets.is_connected():
        st.error("❌ **Google Sheets Not Connected**")
        show_setup_instructions()
        return
    
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;'>
        <h2 style='color: white; margin: 0;'>⛪ Church Attendance</h2>
        <p style='color: #f0f0f0; margin: 0; font-size: 0.9rem;'>Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    page = st.sidebar.radio(
        "🔗 Navigate to:",
        [
            "🏠 Dashboard",
            "✓ Mark Attendance", 
            "📅 View History", 
            "📊 Analytics",
            "📈 Reports",
            "⚙️ Admin Panel"
        ],
        index=0
    )
    
    # Sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ☁️ Cloud Stats")
    
    try:
        stats = sheets.get_stats()
        st.sidebar.metric("📋 Total Records", stats.get('total_attendance', 0))
        st.sidebar.metric("📅 Sundays Tracked", stats.get('unique_dates', 0))
        st.sidebar.metric("👥 Total Members", stats.get('total_members', 0))
        st.sidebar.success("✅ Google Sheets Connected")
        
        if stats.get('spreadsheet_url'):
            st.sidebar.markdown(f"[📊 View Spreadsheet]({stats['spreadsheet_url']})")
    except:
        st.sidebar.error("❌ Loading stats...")
    
    # Route to pages
    if page == "🏠 Dashboard":
        dashboard_home()
    elif page == "✓ Mark Attendance":
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
    
    # Load data from Google Sheets
    df = sheets.load_attendance()
    members_df = sheets.load_members()
    
    if df.empty:
        st.info("👋 Welcome! No attendance data yet. Start by uploading member data and marking attendance!")
        return
    
    # Prepare data
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Key Metrics
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Total Attendance", f"{len(df):,}")
    with col2:
        st.metric("📅 Sundays Tracked", df["Date"].nunique())
    with col3:
        st.metric("👥 Active Members", df["Full Name"].nunique())
    with col4:
        st.metric("📂 Active Groups", df["Group"].nunique())
    with col5:
        sundays = df["Date"].nunique()
        avg_attendance = len(df) / sundays if sundays > 0 else 0
        st.metric("📈 Avg per Sunday", f"{avg_attendance:.1f}")
    
    # Attendance Trend
    st.markdown("### 📈 Attendance Trend")
    
    recent_data = df[df["Date"] >= (datetime.now() - timedelta(weeks=8))]
    weekly_trend = recent_data.groupby("Date").size().reset_index(name="Attendance")
    
    if len(weekly_trend) > 1:
        fig = px.line(
            weekly_trend,
            x="Date",
            y="Attendance",
            markers=True,
            title="Weekly Attendance Trend (Last 8 Weeks)"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Group Performance
    st.markdown("### 👥 Group Performance")
    
    group_stats = df.groupby("Group").size().reset_index(name="Total_Attendance")
    
    fig = px.bar(
        group_stats,
        x="Group",
        y="Total_Attendance",
        title="Total Attendance by Group",
        color="Total_Attendance",
        color_continuous_scale="blues"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def attendance_page():
    st.markdown('<div class="main-header">✓ Mark Attendance</div>', unsafe_allow_html=True)
    
    # Check for members
    members_df = sheets.load_members()
    if members_df.empty:
        st.warning("⚠️ No members found. Please upload member data in the Admin Panel first.")
        return
    
    # Main form
    col1, col2 = st.columns(2)
    
    with col1:
        sunday = st.date_input("📅 Select Sunday", value=date.today())
        sunday_str = sunday.strftime("%Y-%m-%d")
    
    with col2:
        available_groups = sorted(members_df["Group"].dropna().unique())
        group = st.selectbox("👥 Select Group", available_groups)
    
    # Group information
    group_df = members_df[members_df["Group"] == group].copy()
    st.info(f"📊 **{group}** has **{len(group_df)}** members total")
    
    # Check for existing attendance
    existing_attendance = sheets.get_existing_attendance(sunday_str, group)
    
    if existing_attendance:
        st.markdown(f"""
        <div class="warning-banner">
            ⚠️ Found {len(existing_attendance)} existing records for {sunday_str} in {group}
        </div>
        """, unsafe_allow_html=True)
    
    # Member selection
    st.markdown("### 👤 Select Present Members")
    
    present = st.multiselect(
        "Present Members:",
        group_df["Full Name"].tolist(),
        default=existing_attendance,
        help="Select all members who are present today"
    )
    
    # Submit button
    if st.button("☁️ Save to Google Sheets", type="primary", use_container_width=True):
        if not present:
            st.error("⚠️ Please select at least one member as present.")
            return
        
        present_df = group_df[group_df["Full Name"].isin(present)].copy()
        
        if sheets.save_attendance(present_df, sunday_str, group):
            st.markdown(f"""
            <div class="success-banner">
                🎉 Successfully saved {len(present_df)} attendance records to Google Sheets!
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("❌ Failed to save attendance.")

def history_page():
    st.markdown('<div class="main-header">📅 Attendance History</div>', unsafe_allow_html=True)
    
    df = sheets.load_attendance()
    if df.empty:
        st.info("📝 No attendance records found.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Basic filters
    col1, col2 = st.columns(2)
    
    with col1:
        groups = ["All Groups"] + sorted(df["Group"].unique())
        selected_group = st.selectbox("👥 Filter by Group", groups)
    
    with col2:
        quick_filter = st.selectbox(
            "⚡ Quick Filter",
            ["All Time", "Last Week", "Last Month"]
        )
    
    # Apply filters
    if quick_filter == "Last Week":
        week_ago = datetime.now() - timedelta(days=7)
        filtered_df = df[df["Date"] >= week_ago]
    elif quick_filter == "Last Month":
        month_ago = datetime.now() - timedelta(days=30)
        filtered_df = df[df["Date"] >= month_ago]
    else:
        filtered_df = df.copy()
    
    if selected_group != "All Groups":
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]
    
    # Display results
    st.markdown("### 📋 Records")
    
    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "📄 Download as CSV",
            csv_data,
            f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    else:
        st.warning("No records found for the selected filters.")

def analytics_page():
    st.markdown('<div class="main-header">📊 Analytics & Insights</div>', unsafe_allow_html=True)
    
    df = sheets.load_attendance()
    if df.empty:
        st.info("📈 No data available for analytics.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Analytics tabs
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "👥 Groups", "🎯 Members"])
    
    with tab1:
        st.markdown("#### 📈 Attendance Trends")
        
        weekly_data = df.groupby(df["Date"].dt.to_period("W")).size()
        weekly_df = pd.DataFrame({
            "Week": weekly_data.index.astype(str),
            "Attendance": weekly_data.values
        })
        
        if len(weekly_df) > 0:
            fig = px.line(
                weekly_df,
                x="Week",
                y="Attendance",
                markers=True,
                title="Weekly Attendance Trend"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### 👥 Group Analysis")
        
        group_stats = df.groupby("Group").agg({
            "Full Name": ["count", "nunique"],
            "Date": "nunique"
        })
        
        group_stats.columns = ["Total_Attendance", "Unique_Members", "Sundays_Active"]
        group_stats["Avg_per_Sunday"] = (group_stats["Total_Attendance"] / group_stats["Sundays_Active"]).round(1)
        
        st.dataframe(group_stats, use_container_width=True)
    
    with tab3:
        st.markdown("#### 🎯 Member Engagement")
        
        member_stats = df.groupby("Full Name").agg({
            "Date": ["count", "nunique"],
            "Group": "first"
        })
        
        member_stats.columns = ["Total_Attendance", "Unique_Sundays", "Group"]
        member_stats = member_stats.reset_index().sort_values("Total_Attendance", ascending=False)
        
        st.markdown("**🏆 Top 10 Most Active Members**")
        st.dataframe(member_stats.head(10), use_container_width=True, hide_index=True)

def reports_page():
    st.markdown('<div class="main-header">📈 Detailed Reports</div>', unsafe_allow_html=True)
    
    df = sheets.load_attendance()
    if df.empty:
        st.info("📊 No attendance data available for reports.")
        return
    
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Report selector
    report_type = st.selectbox(
        "📋 Select Report Type",
        [
            "📅 Monthly Summary",
            "👥 Group Performance", 
            "🎯 Member Consistency",
            "📊 Overview Report"
        ]
    )
    
    if report_type == "📅 Monthly Summary":
        st.markdown("### 📅 Monthly Summary Report")
        
        df["Month"] = df["Date"].dt.to_period("M")
        monthly_stats = df.groupby(["Month", "Group"]).size().unstack(fill_value=0)
        monthly_stats["Total"] = monthly_stats.sum(axis=1)
        
        st.dataframe(monthly_stats, use_container_width=True)
        
        # Export
        csv_data = monthly_stats.to_csv()
        st.download_button(
            "📥 Download Report",
            csv_data,
            f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    elif report_type == "👥 Group Performance":
        st.markdown("### 👥 Group Performance Report")
        
        group_analysis = df.groupby("Group").agg({
            "Full Name": ["count", "nunique"],
            "Date": "nunique"
        })
        
        group_analysis.columns = ["Total_Attendance", "Active_Members", "Sundays_Active"]
        group_analysis["Avg_per_Sunday"] = (group_analysis["Total_Attendance"] / group_analysis["Sundays_Active"]).round(1)
        
        st.dataframe(group_analysis, use_container_width=True)
        
        # Visualization
        fig = px.bar(
            group_analysis.reset_index(),
            x="Group",
            y="Avg_per_Sunday",
            title="Average Attendance per Sunday",
            color="Avg_per_Sunday"
        )
        st.plotly_chart(fig, use_container_width=True)

def admin_page():
    st.markdown('<div class="main-header">⚙️ Admin Panel</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👥 Member Management", "☁️ Google Sheets"])
    
    with tab1:
        st.markdown("### 👥 Member Management")
        
        members_df = sheets.load_members()
        
        if not members_df.empty:
            st.success(f"✅ **{len(members_df)}** members in Google Sheets")
            st.dataframe(members_df, use_container_width=True, hide_index=True)
            
            # Download
            csv_data = members_df.to_csv(index=False)
            st.download_button(
                "📥 Download Member List",
                csv_data,
                f"members_{date.today()}.csv",
                "text/csv"
            )
        else:
            st.info("📝 No members found. Upload a member list below.")
        
        # Upload
        st.markdown("### 📤 Upload Member List")
        st.info("💡 **Required columns:** Membership Number, Full Name, Group")
        
        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
        
        if uploaded_file:
            try:
                new_df = pd.read_csv(uploaded_file)
                st.dataframe(new_df.head(10), use_container_width=True)
                
                required_cols = ["Membership Number", "Full Name", "Group"]
                missing_cols = [col for col in required_cols if col not in new_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                else:
                    st.success("✅ File format looks good!")
                    
                    if st.button("☁️ Save to Google Sheets", type="primary"):
                        if sheets.save_members(new_df):
                            st.success("🎉 Members saved successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to save members.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("### ☁️ Google Sheets Status")
        
        stats = sheets.get_stats()
        
        if sheets.is_connected():
            st.success("✅ Connected to Google Sheets")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Members", stats.get('total_members', 0))
            with col2:
                st.metric("📋 Records", stats.get('total_attendance', 0))
            with col3:
                st.metric("📅 Dates", stats.get('unique_dates', 0))
            
            if stats.get('spreadsheet_url'):
                st.markdown(f"**📊 Spreadsheet:** [Open in Google Sheets]({stats['spreadsheet_url']})")
        else:
            st.error("❌ Not connected to Google Sheets")
            show_setup_instructions()

if __name__ == "__main__":
    main_app()