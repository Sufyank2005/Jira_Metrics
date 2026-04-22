from datetime import datetime, timedelta
from collections import defaultdict
from jira import JIRA
import csv


class JiraDailyWIPProject:
    def __init__(self, jira_url=None, email=None, api_token=None):
        self.jira_url = jira_url
        self.auth = (email, api_token) if email and api_token else None
        self.data_store = {}

        # Separate daily counts by category + overall
        self.daily_counts = {
            "Stories": defaultdict(lambda: defaultdict(int)),
            "Bugs": defaultdict(lambda: defaultdict(int)),
            "Story Bugs": defaultdict(lambda: defaultdict(int)),
            "Overall": defaultdict(lambda: defaultdict(int))
        }

        # Only track these statuses
        self.allowed_statuses = {
            "Development",
            "Code Review",
            "Checked In",
            "QA",
            "Product Acceptance",
            "Blocked"
        }

        if jira_url and email and api_token:
            self.jira = JIRA(server=jira_url, basic_auth=(email, api_token))
        else:
            self.jira = None

    def load_jql_query(self, jql):
        if not self.jira:
            print("Jira connection not initialized. Provide jira_url, email, and api_token.")
            return

        all_issues = []
        next_page_token = None

        while True:
            issues = self.jira.enhanced_search_issues(
                jql,
                expand="changelog",
                maxResults=100,
                nextPageToken=next_page_token
            )
            all_issues.extend(issues)
            next_page_token = getattr(issues, "nextPageToken", None)
            if not next_page_token:
                break

        self.data_store = {"issues": all_issues}
        print(f"Successfully pulled {len(all_issues)} issues from Jira")

    def process_issue(self, issue, start_date, days=30):
        """Process a single issue's changelog to build daily status counts."""
        transitions = []
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status":
                    transitions.append({
                        "timestamp": datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z"),
                        "to": item.toString
                    })
        transitions.sort(key=lambda t: t["timestamp"])

        # Default to current status
        current_status = issue.fields.status.name

        # Determine category
        issue_type = issue.fields.issuetype.name.lower()
        if issue_type == "bug":
            category = "Bugs"
        elif issue_type == "story":
            category = "Stories"
        else:
            category = "Story Bugs"

        # Walk through each day in last N days
        for day_offset in range(days + 1):
            day = (start_date + timedelta(days=day_offset)).date()

            # Find last transition before this day
            for t in transitions:
                if t["timestamp"].date() <= day:
                    current_status = t["to"]

            # Only count if status is in allowed list
            if current_status in self.allowed_statuses:
                self.daily_counts[category][day][current_status] += 1
                self.daily_counts["Overall"][day][current_status] += 1

    def calculate_daily_wip(self, days=14):
        """Calculate daily WIP counts for last N days."""
        issues = self.data_store.get("issues", [])
        now = datetime.now().astimezone()
        start_date = now - timedelta(days=days)

        #  Pre-populate all categories with zeros for each day/status
        for category in ["Stories", "Bugs", "Story Bugs", "Overall"]:
            for day_offset in range(days + 1):
                day = (start_date + timedelta(days=day_offset)).date()
                for status in self.allowed_statuses:
                    _ = self.daily_counts[category][day][status]

        #  Now process issues normally
        for issue in issues:
            self.process_issue(issue, start_date, days)


    def display_report(self):
        print("\nPMO AUTOMATED METRICS - DAILY WIP REPORT \n")

        for category in ["Stories", "Bugs", "Story Bugs", "Overall"]:
            print(f"\n=== {category.upper()} ===\n")
            for day in sorted(self.daily_counts[category].keys()):
                print(f"{day}:")
                for status in self.allowed_statuses:
                    count = self.daily_counts[category][day].get(status, 0)
                    print(f" • {status:<20}: {count}")
                print("=" * 40)

    def export_to_csv(self, filename=None):
        """Export daily WIP counts to a CSV file with team name in first row and filename."""
        # Detect the team name from the issues
        team_name = None
        issues = self.data_store.get("issues", [])
        if issues:
            # Grab the team name from the first issue
            team_name = getattr(issues[0].fields.customfield_11870, "name", "UnknownTeam")
        if not team_name:
            team_name = "UnknownTeam"

        safe_team_name = team_name.replace(" ", "_")

        # Build filename if not provided
        today_str = datetime.now().strftime("%m%d%Y")
        if filename is None:
            filename = f"WIP_{safe_team_name}{today_str}.csv"

        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # First row: team name
            writer.writerow([team_name])

            # Define the statuses as columns
            statuses = ["Development", "Code Review", "Checked In", "QA", "Product Acceptance", "Blocked"]

            for category in ["Stories", "Bugs", "Story Bugs", "Overall"]:
                # Section header
                writer.writerow([category])
                # Column headers
                writer.writerow(["Date"] + statuses)

                # Collect totals for averages
                totals = {status: 0 for status in statuses}
                day_count = len(self.daily_counts[category])

                # Write daily rows
                for day in sorted(self.daily_counts[category].keys()):
                    row = [day.strftime("%Y-%m-%d")]
                    for status in statuses:
                        count = self.daily_counts[category][day].get(status, 0)
                        totals[status] += count
                        row.append(count)
                    writer.writerow(row)

                # Add average row
                if day_count > 0:
                    avg_row = ["Average WIP"]
                    for status in statuses:
                        avg_row.append(round(totals[status] / day_count, 2))
                    writer.writerow(avg_row)

                # Blank line between sections
                writer.writerow([])

        print(f"\nCSV export complete: {filename}")




# --- EXECUTION ---

jira_url = "https://cadent.atlassian.net"
email = "skhan2@cadent.tv"
api_token = "ATATT3xFfGF0lreP5xlVlVwbqNKLfl9oBrUrGes4Sk86KuBzMWTCIeCo14PbAl7xrIKKZvyWngLAURJ10KMOrELMRVJvcI7MOeoeG9VUwdDSAwcKxIix1dPd5HBFCJAP17dJugOLaZnN7A0n_Cg7c9U6rAuqUasIYZy3TZxkIKO33JFdKKTGSJI=0003FA17"

project = JiraDailyWIPProject(jira_url=jira_url, email=email, api_token=api_token)

jql_query = '''
type in (story, bug, "Story Bug") 
and "Program Increment[Dropdown]" =30 
and "Team[Team]"= ab077377-6409-47c9-92d4-b4755a39b363-70 
and project != "Google Cloud Migration" 
'''

project.load_jql_query(jql_query)
project.calculate_daily_wip(days=30)
project.display_report()
project.export_to_csv()
