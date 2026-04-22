# 📊 PMO-Spring 2026 Intern Project – Jira Metrics Automation

## Overview
This project automates the collection and reporting of Jira metrics to support sprint tracking, stakeholder reporting, and workflow analysis. It includes three Python scripts designed to handle different aspects of Jira data:

- **WIP.py** – Tracks daily WIP counts by status and category.
- **Throughput.py** – Aggregates sprint-level throughput metrics (Stories, Bugs, Story Bugs).
- **TIS_CT.py** – Calculates time spent in each workflow status and overall cycle time per ticket.

Together, these scripts provide robust, automated insights into sprint performance, workflow efficiency, and team throughput.

---

## 🔧 Requirements
- Python 3.9+
- Libraries:
  - `jira` (Atlassian Python API, install via `pip install jira`)
  - `csv` (Python standard library)
  - `datetime` (Python standard library)
  - `collections` (Python standard library, used for `defaultdict`)
  - `math` (Python standard library)
- Jira Cloud API access
- Valid Jira API token and email

---

## ⚙️ Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install jira
Configure credentials:

Plug in jira_url, email, and api_token directly in the execution block (as shown in each script).

Or use environment variables / .env file for secure storage.

📂 Scripts
1. JiraDailyWIPProject (WIP.py)
Purpose: Tracks how many issues are in each workflow status (Development, QA, etc.) on a daily basis.
Logic: Pre-populates daily counts with zeros, then processes issue changelogs to build daily status counts.
Output:

CSV file with daily counts per category (Stories, Bugs, Story Bugs, Overall).

Includes an “Average WIP” row summarizing averages per status.

Filename format: WIP_<TeamName><MMDDYYYY>.csv.

First row contains the team name.

Usage:

bash
python WIP.py
Sample Output (CSV):

Code
Sell Side Core
Stories
Date,Development,Code Review,Checked In,QA,Product Acceptance,Blocked
2026-02-01,2,1,0,3,0,0
Average WIP,1.5,0.8,0.2,2.1,0.4,0.0
2. JiraMetricsProject (Throughput.py)
Purpose: Collects sprint-level throughput metrics (Stories, Bugs, Story Bugs).
Logic:

Generates sprint boundaries from a start date.

Pre-populates only elapsed sprints (end date ≤ today) with zero counts.

Future sprints are excluded from CSV and console output.
Output:

CSV ordered from first sprint to last, grouped by team.

Filename format: Throughput_<TeamName><MMDDYYYY>.csv.

Usage:

bash
python Throughput.py
Adjusting Sprint Dates and Number of Sprints:

python
sprint_start = datetime(2026, 1, 28, tzinfo=datetime.now().astimezone().tzinfo)
project.calculate_throughput(sprint_start, num_sprints=6)
Change sprint_start to the actual start date of your first sprint.
Change num_sprints to match the number of sprints you want to analyze.

Sample Output (CSV):

Code
Type,Sprint,Team,Tickets Completed
Stories,Sprint 1,Sell Side Core,15
Bugs,Sprint 1,Sell Side Core,3
Story Bugs,Sprint 1,Sell Side Core,2
3. JiraTimeInStatusProject (TIS_CT.py)
Purpose: Calculates time spent in each workflow status and overall cycle time per ticket.
Logic:

Excludes weekends by calculating only business days.

Rounds raw hours up to whole numbers in CSV.

Provides both raw hours and formatted durations.
Output:

CSV file with raw decimal hours first, followed by formatted durations (- Formatted columns).

Filename format: TIS_CT<MMDDYYYY>.csv (default prefix TIS_CT).

Usage:

bash
python TIS_CT.py
Sample Output (CSV):

Code
Ticket,Type,Team,Development,Code Review,Checked In,QA,Product Acceptance,Blocked,Cycle Time,Development - Formatted,Code Review - Formatted,Checked In - Formatted,QA - Formatted,Product Acceptance - Formatted,Blocked - Formatted,Cycle Time - Formatted
SELL-1234,Story,Sell Side Core,25,10,34,124,12,0,195,1d 1h,10h,1d 10h,5d 4h,12h,0m,8d 3h
▶️ Usage Notes
Update the JQL queries in each script to match your team/project filters.

CSV files are automatically named based on team name and date.

Reports are printed to console and exported to CSV for stakeholder use.