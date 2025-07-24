import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import plotly.express as px

st.set_page_config("Church Attendance - Debug", layout="wide")

MEMBER_FILE = "members.csv"
MASTER_FILE = "all_attendance.csv"
EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

def debug_file_info():
    """Show debug information about files"""
    st.sidebar.markdown("### 🔍 Debug Info")
    
    # Check if files exist
    member_exists = os.path.exists(MEMBER_FILE)
    master_exists = os.path.exists(MASTER_FILE)
    
    st.sidebar.write(f"Members file exists: {'✅' if member_exists else '❌'}")
    st.sidebar.write(f"Attendance file exists: {'✅' if master_exists else '❌'}")
    
    if master_exists:
        try:
            df = pd.read_csv(MASTER_FILE)
            st.sidebar.write(f"Attendance records: {len(df)}")
            st.sidebar.write(f"File size: {os.path.getsize(MASTER_FILE)} bytes")
            st.sidebar.write(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(MASTER_FILE))}")
            
            # Show last few entries
            if len(df) > 0:
                st.sidebar.write("**Last 3 entries:**")
                last_entries = df.tail(3)[['Date', 'Full Name', 'Group']]
                st.sidebar.dataframe(last_entries, use_container_width=True)
        except Exception as e:
            st.sidebar.error(f"Error reading attendance file: {e}")

def main_app():
    debug_file_info()  # Always show debug info
    
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio("Go to", [
        "📝 Mark Attendance", 
        "📅 View History", 
        "📊 Dashboard", 
        "🔍 Debug Data",
        "⚙️ Admin"
    ])
    
    if page == "📝 Mark Attendance":
        attendance_page()
    elif page == "📅 View History":
        history_page()
    elif page == "📊 Dashboard":
        dashboard_page()
    elif page == "🔍 Debug Data":
        debug_page()
    elif page == "⚙️ Admin":
        admin_page()

def attendance_page():
    st.header("📝 Mark Attendance")
    
    if not os.path.exists(MEMBER_FILE):
        st.warning("⚠️ No members file found. Please upload one in the Admin tab.")
        st.stop()
    
    try:
        members_df = pd.read_csv(MEMBER_FILE)
        st.success(f"✅ Loaded {len(members_df)} members")
    except Exception as e:
        st.error(f"Error loading members: {e}")
        st.stop()
    
    sunday = st.date_input("Select Sunday", value=date.today())
    sunday_str = pd.to_datetime(sunday).strftime("%Y-%m-%d")
    
    st.info(f"📅 Selected date: {sunday_str}")
    
    group = st.selectbox("Select Group", sorted(members_df["Group"].dropna().unique()))
    group_df = members_df[members_df["Group"] == group].copy()
    
    st.info(f"👥 Members in {group}: {len(group_df)}")
    
    # Check existing attendance with detailed info
    existing_attendance = []
    if os.path.exists(MASTER_FILE):
        try:
            master_df = pd.read_csv(MASTER_FILE)
            st.write(f"📊 Total records in file: {len(master_df)}")
            
            # Show unique dates in file
            master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
            valid_dates = master_df[master_df["Date"].notnull()]
            unique_dates = valid_dates["Date"].dt.date.unique()
            st.write(f"📅 Unique dates in file: {len(unique_dates)}")
            
            sunday_dt = pd.to_datetime(sunday_str)
            existing = master_df[
                (master_df["Date"] == sunday_dt) & 
                (master_df["Group"] == group)
            ]
            existing_attendance = existing["Full Name"].tolist()
            
            if existing_attendance:
                st.warning(f"⚠️ Found {len(existing_attendance)} existing records for {sunday_str} in {group}")
        except Exception as e:
            st.error(f"Error checking existing attendance: {e}")
    
    present = st.multiselect(
        "Select Present Members:", 
        group_df["Full Name"].tolist(),
        default=existing_attendance
    )
    
    st.write(f"📋 Selected {len(present)} members")
    
    if st.button("✅ Submit Attendance"):
        if not present:
            st.warning("⚠️ Please select at least one member as present before submitting.")
            return
        
        # Create the new records
        new_present_df = group_df[group_df["Full Name"].isin(present)].copy()
        new_present_df["Status"] = "Present"
        new_present_df["Date"] = sunday_str
        
        output = new_present_df[["Date", "Membership Number", "Full Name", "Group", "Status"]]
        
        st.write("📝 **Records to be saved:**")
        st.dataframe(output)
        
        # Handle file saving with detailed logging
        try:
            if os.path.exists(MASTER_FILE):
                master_df = pd.read_csv(MASTER_FILE)
                st.write(f"📖 Existing file has {len(master_df)} records")
                
                # Remove existing entries for this date/group to prevent duplicates
                master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
                sunday_dt = pd.to_datetime(sunday_str)
                
                before_removal = len(master_df)
                master_df = master_df[~(
                    (master_df["Date"] == sunday_dt) & 
                    (master_df["Group"] == group)
                )]
                after_removal = len(master_df)
                
                if before_removal != after_removal:
                    st.info(f"🗑️ Removed {before_removal - after_removal} existing records for this date/group")
                
                updated_df = pd.concat([master_df, output], ignore_index=True)
            else:
                st.info("📄 Creating new attendance file")
                updated_df = output.copy()
            
            # Save the file
            updated_df.to_csv(MASTER_FILE, index=False)
            
            # Verify the save
            verification_df = pd.read_csv(MASTER_FILE)
            st.success(f"✅ File saved successfully! New total: {len(verification_df)} records")
            
            # Show the last few records to confirm
            st.write("**Last 5 records in file:**")
            st.dataframe(verification_df.tail())
            
        except Exception as e:
            st.error(f"❌ Error saving attendance: {e}")
            st.error("Please check file permissions and try again")

def debug_page():
    st.header("🔍 Debug Data")
    
    st.subheader("📁 File Information")
    
    # Check files
    for filename in [MEMBER_FILE, MASTER_FILE]:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            modified = datetime.fromtimestamp(os.path.getmtime(filename))
            st.success(f"✅ {filename}: {size} bytes, modified {modified}")
            
            try:
                df = pd.read_csv(filename)
                st.write(f"   - Rows: {len(df)}, Columns: {len(df.columns)}")
                st.write(f"   - Columns: {list(df.columns)}")
                
                if filename == MASTER_FILE:
                    # Analyze attendance data
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                    valid_dates = df[df["Date"].notnull()]
                    
                    st.write("**Date Analysis:**")
                    st.write(f"   - Valid dates: {len(valid_dates)}")
                    st.write(f"   - Invalid dates: {len(df) - len(valid_dates)}")
                    
                    if len(valid_dates) > 0:
                        st.write(f"   - Date range: {valid_dates['Date'].min()} to {valid_dates['Date'].max()}")
                        
                        unique_dates = valid_dates["Date"].dt.date.unique()
                        st.write(f"   - Unique dates: {len(unique_dates)}")
                        st.write(f"   - Dates: {sorted(unique_dates, reverse=True)[:5]}...")  # Show first 5
                
            except Exception as e:
                st.error(f"   ❌ Error reading {filename}: {e}")
        else:
            st.error(f"❌ {filename}: File not found")
    
    st.subheader("📊 Raw Data View")
    
    if os.path.exists(MASTER_FILE):
        try:
            df = pd.read_csv(MASTER_FILE)
            
            st.write(f"**Total records: {len(df)}**")
            
            # Show data types
            st.write("**Data Types:**")
            st.write(df.dtypes)
            
            # Show all data
            st.write("**All Records:**")
            st.dataframe(df)
            
            # Group by date
            if "Date" in df.columns:
                st.write("**Records by Date:**")
                date_counts = df["Date"].value_counts().sort_index()
                st.write(date_counts)
                
        except Exception as e:
            st.error(f"Error displaying data: {e}")
    
    st.subheader("🧪 Test Data Saving")
    
    if st.button("🧪 Test Save Function"):
        test_data = pd.DataFrame({
            "Date": [date.today().strftime("%Y-%m-%d")],
            "Membership Number": ["TEST001"],
            "Full Name": ["Test User"],
            "Group": ["Test Group"],
            "Status": ["Present"]
        })
        
        try:
            # Try to save test data
            test_file = "test_save.csv"
            test_data.to_csv(test_file, index=False)
            
            # Try to read it back
            read_back = pd.read_csv(test_file)
            
            if len(read_back) == 1:
                st.success("✅ File save/read test passed")
                os.remove(test_file)  # Clean up
            else:
                st.error("❌ File save/read test failed - data mismatch")
                
        except Exception as e:
            st.error(f"❌ File save/read test failed: {e}")

def history_page():
    st.header("📅 View Past Attendance")
    
    if not os.path.exists(MASTER_FILE):
        st.warning("No attendance has been saved yet.")
        return
    
    try:
        df = pd.read_csv(MASTER_FILE)
        st.write(f"📊 Loaded {len(df)} total records")
        
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        valid_df = df[df["Date"].notnull()]
        
        st.write(f"📅 {len(valid_df)} records with valid dates")
        
        if valid_df.empty:
            st.warning("No valid attendance records found.")
            return
        
        dates = sorted(valid_df["Date"].dt.date.unique(), reverse=True)
        st.write(f"📅 Available dates: {len(dates)}")
        
        selected_date = st.selectbox("Select a Sunday", dates)
        
        filtered = valid_df[valid_df["Date"].dt.date == selected_date]
        
        st.write(f"Showing attendance for **{selected_date}** ({len(filtered)} records)")
        st.dataframe(filtered)
        
    except Exception as e:
        st.error(f"Error loading history: {e}")

def dashboard_page():
    st.header("📊 Attendance Dashboard")
    
    if not os.path.exists(MASTER_FILE):
        st.warning("No attendance data available.")
        return
    
    try:
        df = pd.read_csv(MASTER_FILE)
        st.write(f"📊 Total records loaded: {len(df)}")
        
        # Show first few rows for debugging
        st.write("**First 5 records:**")
        st.dataframe(df.head())
        
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notnull()]
        
        st.write(f"📅 Records with valid dates: {len(df)}")
        
        if df.empty:
            st.warning("No valid attendance records found.")
            return
        
        # Show date range
        st.write(f"📅 Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        
        # Simple summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", len(df))
        
        with col2:
            unique_dates = df["Date"].nunique()
            st.metric("Sundays Tracked", unique_dates)
        
        with col3:
            unique_members = df["Full Name"].nunique()
            st.metric("Unique Members", unique_members)
        
        # Show all data for debugging
        st.subheader("📋 All Data")
        st.dataframe(df)
        
        # Basic chart
        if len(df) > 1:
            weekly_stats = df.groupby("Date").size().reset_index(name="Total_Present")
            
            fig = px.line(
                weekly_stats, 
                x="Date", 
                y="Total_Present",
                title="Weekly Attendance",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.write("**Error details:**", str(e))

def admin_page():
    st.header("⚙️ Admin Panel")
    
    st.subheader("📁 Member List")
    if os.path.exists(MEMBER_FILE):
        try:
            member_df = pd.read_csv(MEMBER_FILE)
            st.write(f"📊 {len(member_df)} members loaded")
            st.dataframe(member_df)
        except Exception as e:
            st.error(f"Error loading members: {e}")
    
    new_csv = st.file_uploader("Upload New Member CSV", type=["csv"], key="member_upload")
    if new_csv:
        try:
            new_df = pd.read_csv(new_csv)
            new_df.to_csv(MEMBER_FILE, index=False)
            st.success("✅ Member list updated.")
            st.rerun()
        except Exception as e:
            st.error(f"Error uploading members: {e}")
    
    st.subheader("🧹 Clear Attendance Data")
    if st.button("❌ Delete all attendance records"):
        try:
            if os.path.exists(MASTER_FILE):
                os.remove(MASTER_FILE)
                st.success("✅ all_attendance.csv cleared.")
            else:
                st.info("Nothing to delete.")
        except Exception as e:
            st.error(f"Error deleting file: {e}")

# --- RUN APP ---
if __name__ == "__main__":
    main_app()