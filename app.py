import streamlit as st
from datetime import datetime

from WIP import JiraDailyWIPProject
from Throughput import JiraMetricsProject
from TIS_CT import JiraTimeInStatusProject

st.title("PMO Automated Jira Metrics Dashboard")

# General instructions
st.markdown("""
Fill in your Jira details and choose which report to run.

**Important:**  
- For the **Sprint Throughput Report**, first select a **Sprint Start Date** and the **Number of Sprints**, then click **Confirm Sprint Settings**.  
- After confirmation, you can run the report and download the CSV.  
""")

# Common inputs
jira_url = st.text_input("Jira URL", "https://cadent.atlassian.net")
email = st.text_input("Email")
api_token = st.text_input("API Token", type="password")
jql_query = st.text_area("JQL Query")

def validate_inputs():
    if not jira_url or not email or not api_token or not jql_query.strip():
        st.error("⚠️ Please fill in Jira URL, Email, API Token, and JQL Query before running the report.")
        return False
    return True

# --- Daily WIP ---
st.subheader("Daily WIP Report")
st.info("Click **Run Daily WIP Report** to generate a 30-day Work In Progress report.")

if st.button("Run Daily WIP Report"):
    if validate_inputs():
        try:
            project = JiraDailyWIPProject(jira_url, email, api_token)
            project.load_jql_query(jql_query)
            project.calculate_daily_wip(days=30)
            st.text("Daily WIP Report:")
            project.display_report()
            filename = project.export_to_csv()
            with open(filename, "rb") as f:
                st.download_button("⬇️ Download WIP CSV", f, file_name=filename)
            st.success(f"✅ CSV exported as {filename}")
        except Exception as e:
            if "Unauthorized" in str(e) or "401" in str(e):
                st.error("❌ Could not connect to Jira. Please check your email and API token.")
            elif "JQL" in str(e):
                st.error("❌ Invalid JQL query. Please review your syntax.")
            else:
                st.error(f"❌ An unexpected error occurred: {e}")

# --- Time in Status ---
st.subheader("Time in Status Report")
st.info("Click **Run Time in Status Report** to calculate time spent in each status from your JQL query as well as cycle time.")

if st.button("Run Time in Status Report"):
    if validate_inputs():
        try:
            project = JiraTimeInStatusProject(jira_domain=jira_url, email=email, api_token=api_token)
            project.connect_to_jira()
            project.calculate_time_in_status_from_jql(jql_query)
            st.text("Time in Status Report:")
            project.display_report()
            filename = project.export_to_csv()
            with open(filename, "rb") as f:
                st.download_button("⬇️ Download TIS CSV", f, file_name=filename)
            st.success(f"✅ CSV exported as {filename}")
        except Exception as e:
            if "Unauthorized" in str(e) or "401" in str(e):
                st.error("❌ Could not connect to Jira. Please check your email and API token.")
            elif "JQL" in str(e):
                st.error("❌ Invalid JQL query. Please review your syntax.")
            else:
                st.error(f"❌ An unexpected error occurred: {e}")

# --- Throughput ---
st.subheader("Sprint Throughput Report")
st.info("Step 1: Choose sprint start date and number of sprints, then click **Confirm Sprint Settings**.  \n Step 2: After confirmation, click **Run Throughput Report** to generate results.")

# Stage 1: choose inputs
sprint_start = st.date_input("Sprint Start Date", datetime(2026, 1, 28), key="sprint_start")
num_sprints = st.number_input("Number of Sprints", min_value=1, max_value=7, value=6, key="num_sprints")

if st.button("Confirm Sprint Settings"):
    st.session_state["confirmed_sprint_start"] = sprint_start
    st.session_state["confirmed_num_sprints"] = num_sprints
    st.success("✅ Sprint settings saved. Now click Run Throughput Report.")

# Stage 2: generate report only after confirmation
if "confirmed_sprint_start" in st.session_state and st.button("Run Throughput Report"):
    if validate_inputs():
        try:
            project = JiraMetricsProject(jira_url, email, api_token)
            project.load_jql_query(jql_query)

            sprint_start_dt = datetime.combine(
                st.session_state["confirmed_sprint_start"], datetime.min.time()
            ).astimezone()
            project.calculate_throughput(sprint_start_dt, num_sprints=st.session_state["confirmed_num_sprints"])

            st.text("Sprint Throughput Report:")
            project.display_report()
            filename = project.export_to_csv()
            with open(filename, "rb") as f:
                st.download_button("⬇️ Download Throughput CSV", f, file_name=filename)
            st.success(f"✅ CSV exported as {filename}")
        except Exception as e:
            if "Unauthorized" in str(e) or "401" in str(e):
                st.error("❌ Could not connect to Jira. Please check your email and API token.")
            elif "JQL" in str(e):
                st.error("❌ Invalid JQL query. Please review your syntax.")
            else:
                st.error(f"❌ An unexpected error occurred: {e}")