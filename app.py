import streamlit as st
from datetime import datetime

from WIP import JiraDailyWIPProject
from Throughput import JiraMetricsProject
from TIS_CT import JiraTimeInStatusProject

st.title("PMO Automated Jira Metrics Dashboard")
st.markdown("Fill in your Jira details and choose which report to run.")

# Common inputs
jira_url = st.text_input("Jira URL", "https://cadent.atlassian.net")
email = st.text_input("Email")
api_token = st.text_input("API Token", type="password")
jql_query = st.text_area("JQL Query")

# --- Daily WIP ---
if st.button("Run Daily WIP Report"):
    project = JiraDailyWIPProject(jira_url, email, api_token)
    project.load_jql_query(jql_query)
    project.calculate_daily_wip(days=30)
    st.text("Daily WIP Report:")
    project.display_report()
    filename = project.export_to_csv()   # your script returns the filename
    with open(filename, "rb") as f:
        st.download_button("⬇️ Download WIP CSV", f, file_name=filename)
    st.success(f"✅ CSV exported as {filename}")

# --- Throughput ---
if st.button("Run Sprint Throughput Report"):
    sprint_start = st.date_input("Sprint Start Date", datetime(2026, 1, 28))
    num_sprints = st.number_input("Number of Sprints", min_value=1, max_value=20, value=6)

    project = JiraMetricsProject(jira_url, email, api_token)
    project.load_jql_query(jql_query)
    sprint_start_dt = datetime.combine(sprint_start, datetime.min.time())
    project.calculate_throughput(sprint_start_dt, num_sprints=num_sprints)
    st.text("Sprint Throughput Report:")
    project.display_report()
    filename = project.export_to_csv()
    with open(filename, "rb") as f:
        st.download_button("⬇️ Download Throughput CSV", f, file_name=filename)
    st.success(f"✅ CSV exported as {filename}")

# --- Time in Status ---
if st.button("Run Time in Status Report"):
    project = JiraTimeInStatusProject(jira_domain=jira_url, email=email, api_token=api_token)
    project.connect_to_jira()
    project.calculate_time_in_status_from_jql(jql_query)
    st.text("Time in Status Report:")
    project.display_report()
    filename = project.export_to_csv()
    with open(filename, "rb") as f:
        st.download_button("⬇️ Download TIS CSV", f, file_name=filename)
    st.success(f"✅ CSV exported as {filename}")
