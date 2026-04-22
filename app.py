import streamlit as st
from WIP import JiraDailyWIPProject
from Throughput import JiraMetricsProject
from TIS_CT import JiraTimeInStatusProject
from datetime import datetime

st.title("📊 Jira Metrics Automation")

# Input fields
jira_url = st.text_input("Jira URL", "https://yourcompany.atlassian.net")
email = st.text_input("Email")
api_token = st.text_input("API Token", type="password")
jql_query = st.text_area("JQL Query")

report_type = st.selectbox("Select Report", ["Daily WIP", "Throughput", "Time in Status"])

if st.button("Generate CSV"):
    if report_type == "Daily WIP":
        project = JiraDailyWIPProject(jira_url, email, api_token)
        project.load_jql_query(jql_query)
        project.calculate_daily_wip(days=30)
        project.export_to_csv("WIP_Report.csv")
        st.download_button("Download WIP CSV", open("WIP_Report.csv","rb").read(), "WIP_Report.csv")

    elif report_type == "Throughput":
        project = JiraMetricsProject(jira_url, email, api_token)
        project.load_jql_query(jql_query)
        sprint_start = datetime(2026, 4, 1, tzinfo=datetime.now().astimezone().tzinfo)
        project.calculate_throughput(sprint_start, num_sprints=6)
        project.export_to_csv("Throughput_Report.csv")
        st.download_button("Download Throughput CSV", open("Throughput_Report.csv","rb").read(), "Throughput_Report.csv")

    elif report_type == "Time in Status":
        project = JiraTimeInStatusProject(jira_url, email, api_token)
        project.connect_to_jira()
        project.calculate_time_in_status_from_jql(jql_query)
        project.export_to_csv("TIS_Report.csv")
        st.download_button("Download TIS CSV", open("TIS_Report.csv","rb").read(), "TIS_Report.csv")
