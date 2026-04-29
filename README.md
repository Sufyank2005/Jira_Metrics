# 📊 PMO-Spring 2026 Intern Project – Jira Metrics Automation

## Overview

This project automates the collection and reporting of Jira metrics to support sprint tracking, stakeholder reporting, and workflow analysis. It includes three Python scripts and one Streamlit dashboard designed to handle different aspects of Jira data:

* **WIP.py** – Tracks daily Work In Progress (WIP) counts by workflow status and category.
* **Throughput.py** – Aggregates sprint-level throughput metrics (Stories, Bugs, Story Bugs).
* **TIS_CT.py** – Calculates time spent in each workflow status and overall cycle time per ticket.
* **app.py** – Streamlit dashboard for running reports interactively and downloading CSV outputs.

Together, these tools provide robust, automated insights into sprint performance, workflow efficiency, and team throughput.

---

## 🔧 Requirements

* Python 3.9+
* Libraries:

  * `jira` (Atlassian Python API, install via `pip install jira`)
  * `streamlit` (for the dashboard interface)
  * `csv` (Python standard library)
  * `datetime` (Python standard library)
  * `collections` (Python standard library, used for `defaultdict`)
  * `math` (Python standard library)
* Jira Cloud API access
* Valid Jira credentials

---

## ⚙️ Setup

1. Clone this repository.

2. Install dependencies:

```bash 
pip install -r requirements.txt
```

3. Run the Streamlit dashboard:

```bash "
streamlit run app.py
```

4. Or run the scripts individually:

```bash 
python WIP.py
python Throughput.py
python TIS_CT.py
```

---

## 📂 Scripts

## 1. JiraDailyWIPProject (WIP.py)

**Purpose:** Tracks how many issues are in each workflow status on a daily basis.

**Tracked Statuses:**

* Development
* Code Review
* Checked In
* QA
* Product Acceptance
* Blocked

**Logic:** Pre-populates daily counts with zeros, then processes issue changelogs to build daily status counts.

**Output:**

* CSV file with daily counts per category (Stories, Bugs, Story Bugs, Overall)
* Includes an **Average WIP** row summarizing averages per status
* First row contains the team name

**Filename Format:**

```text 
WIP_<TeamName><MMDDYYYY>.csv
```

**Usage:**

```bash 
python WIP.py
```

**Sample Output (CSV):**

```text 
Sell Side Core

Stories
Date,Development,Code Review,Checked In,QA,Product Acceptance,Blocked
2026-02-01,2,1,0,3,0,0
Average WIP,1.5,0.8,0.2,2.1,0.4,0.0
```

---

## 2. JiraMetricsProject (Throughput.py)

**Purpose:** Collects sprint-level throughput metrics (Stories, Bugs, Story Bugs).

**Logic:**

* Generates sprint boundaries from a start date
* Includes completed sprints only
* Counts tickets resolved within each sprint

**Output:**

* CSV ordered from first sprint to last
* Grouped by Type, Sprint, and Team

**Filename Format:**

```text 
Throughput_<TeamName><MMDDYYYY>.csv
```

**Usage:**

```bash 
python Throughput.py
```

**Adjusting Sprint Dates and Number of Sprints:**

```python id="gmj13l"
sprint_start = datetime(2026, 4, 1, tzinfo=datetime.now().astimezone().tzinfo)
project.calculate_throughput(sprint_start, num_sprints=6)
```

Change `sprint_start` to the first sprint start date.
Change `num_sprints` to the number of sprints to analyze.

**Sample Output (CSV):**

```text 
Type,Sprint,Team,Tickets Completed
Stories,Sprint 1,Sell Side Core,15
Bugs,Sprint 1,Sell Side Core,3
Story Bugs,Sprint 1,Sell Side Core,2
```

---

## 3. JiraTimeInStatusProject (TIS_CT.py)

**Purpose:** Calculates time spent in each workflow status and overall cycle time per ticket.

**Logic:**

* Measures weekday hours only between status transitions
* Rounds raw hours up to whole numbers in CSV
* Provides both raw hours and formatted durations
* Cycle time is measured from first entry into Development through Done

**Output:**

* CSV file with raw hour totals first, followed by formatted duration columns

**Filename Format:**

```text 
TIS_CT<MMDDYYYY>.csv
```

(Default prefix: `TIS_CT`)

**Usage:**

```bash 
python TIS_CT.py
```

**Sample Output (CSV):**

```text 
Ticket,Type,Team,Development,Code Review,Checked In,QA,Product Acceptance,Blocked,Cycle Time,Development - Formatted,Code Review - Formatted,Checked In - Formatted,QA - Formatted,Product Acceptance - Formatted,Blocked - Formatted,Cycle Time - Formatted

SELL-1234,Story,Sell Side Core,25,10,34,124,12,0,195,1d 1h,10h,1d 10h,5d 4h,12h,0m,8d 3h
```

---

## 4. Streamlit Dashboard (app.py)

**Purpose:** Provides an interactive web interface to run reports and download CSV outputs.

**Features:**

* Jira URL, Email, API Token, and JQL query inputs
* Run Daily WIP, Time in Status, and Throughput reports
* Download generated CSV files
* Sprint start date and sprint count selectors
* Input validation and error handling

**Usage:**

```bash
streamlit run app.py
```

---

## ▶️ Usage Notes

* Update the JQL queries in each script to match your team/project filters.
* Plug in your Jira credentials (URL, email, API token) inside each of the three Python   files — WIP.py, Throughput.py, and TIS_CT.py — before execution. These credentials are required for the scripts to connect to Jira Cloud
* CSV files are automatically named based on team name and date.
* Reports are printed to console and exported to CSV.
* The Streamlit dashboard allows reports to be generated without editing Python files directly.
