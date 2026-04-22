import csv
from datetime import datetime, timedelta
import math
from jira import JIRA, Issue

class JiraTimeInStatusProject:
    def __init__(self, jira_domain=None, email=None, api_token=None):
        # Jira connection details 
        self.jira_domain = jira_domain
        self.email = email
        self.api_token = api_token
        self.jira = None

        # Results per ticket
        self.results = {}

    def connect_to_jira(self):
        """Authenticate to Jira Cloud using API token."""
        if self.jira_domain and self.email and self.api_token:
            self.jira = JIRA(
                server=self.jira_domain,
                basic_auth=(self.email, self.api_token)
            )
            print("Connected to Jira successfully.")
        else:
            print("Missing Jira connection details.")

    def business_hours_between(self, start, end):
        """Calculate hours between two datetimes, excluding weekends."""
        total_seconds = 0
        current = start
        while current < end:
            if current.weekday() < 5:  # Mon-Fri
                total_seconds += 60
            current += timedelta(minutes=1)
        return total_seconds / 3600

    def format_duration(self, hours_float):
        """Convert fractional hours into days, hours, and minutes."""
        total_minutes = int(hours_float * 60)
        days = total_minutes // (24 * 60)
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "0m"

    def calculate_time_in_status(self, issue=None, issue_key=None, issue_summary=None, changelog=None):
        transitions = []
        for history in changelog:
            for item in history.get("items", []):
                if item.get("field") == "status":
                    transitions.append({
                        "from": item.get("fromString"),
                        "to": item.get("toString"),
                        "timestamp": datetime.strptime(history["created"], "%Y-%m-%dT%H:%M:%S.%f%z")
                    })
        transitions.sort(key=lambda t: t["timestamp"])

        ticket_results = {"TimeInStatus": {}, "CycleTime": {}}

        # Time in Status
        for i in range(len(transitions) - 1):
            current = transitions[i]
            next_transition = transitions[i + 1]
            duration_hours = self.business_hours_between(current["timestamp"], next_transition["timestamp"])
            status_name = current["to"]
            ticket_results["TimeInStatus"][status_name] = ticket_results["TimeInStatus"].get(status_name, 0) + duration_hours

        # Cycle Time
        dev_start, done_time = None, None
        for t in transitions:
            if t["to"] == "Development" and dev_start is None:
                dev_start = t["timestamp"]
            if t["to"] == "Done":
                done_time = t["timestamp"]
                break
        if dev_start and done_time:
            cycle_hours = self.business_hours_between(dev_start, done_time)
            ticket_results["CycleTime"][issue_key or "Ticket Cycle Time"] = cycle_hours

        self.results[issue_key or issue_summary or "Unknown Ticket"] = {
            "TimeInStatus": ticket_results["TimeInStatus"],
            "CycleTime": ticket_results["CycleTime"],
            "Team": getattr(issue.fields.customfield_11870, "name", "Unknown Team"),
            "Type": getattr(issue.fields.issuetype, "name", "Unknown Type")
        }

    def calculate_time_in_status_from_jql(self, jql_query):
        """Run a JQL query with pagination using nextPageToken."""
        all_issues = []
        next_page_token = None

        while True:
            issues = self.jira.enhanced_search_issues(
                jql_query,
                expand="changelog",
                maxResults=100,
                nextPageToken=next_page_token
            )

            all_issues.extend(issues)

            for issue in issues:
                changelog = []
                for history in issue.changelog.histories:
                    changelog.append({
                        "created": history.created,
                        "items": [
                            {
                                "field": item.field,
                                "fromString": item.fromString,
                                "toString": item.toString
                            }
                            for item in history.items
                        ]
                    })
                self.calculate_time_in_status(
                    issue=issue,
                    issue_key=issue.key,
                    issue_summary=issue.fields.summary,
                    changelog=changelog
                )

            next_page_token = getattr(issues, "nextPageToken", None)
            if not next_page_token:
                break

        print(f"Successfully pulled {len(all_issues)} issues from Jira")

    def display_report(self):
        print("\nPMO AUTOMATED METRICS - TIME IN STATUS REPORT")
        print(f"Total Tickets Pulled: {len(self.results)}")
        
        for ticket, metrics in self.results.items():
            print(f"\nTicket: {ticket}")
            print(f"\n[METRIC: TIME IN STATUS]")
            if not metrics["TimeInStatus"]:
                print(" - No status durations calculated yet.")
            else:
                for status, hours in metrics["TimeInStatus"].items():
                    print(f" • {status:<25}: {self.format_duration(hours)}")
            print(f"\n[METRIC: CYCLE TIME]")
            if not metrics["CycleTime"]:
                print(" - No cycle time calculated yet.")
            else:
                for t, hours in metrics["CycleTime"].items():
                    print(f" • {t:<25}: {self.format_duration(hours)}")
            print("\n" + "="*45)

    def export_to_csv(self, filename_prefix="TIS_CT"):
        """Export results into a CSV file with raw hours first, then formatted columns."""
        # Define the statuses in the order you want them as columns
        statuses = ["Development", "Code Review", "Checked In", "QA", "Product Acceptance", "Blocked"]
        
        # Generate filename with today's date in month-day-year format
        today_str = datetime.now().strftime("%m%d%Y")
        filename = f"{filename_prefix}{today_str}.csv"
        
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row: raw hours first, then formatted columns
            header = ["Ticket", "Type", "Team"] + statuses + ["Cycle Time"]
            header += [f"{status} - Formatted" for status in statuses] + ["Cycle Time - Formatted"]
            writer.writerow(header)

            for ticket, metrics in self.results.items():
                row = [ticket, metrics.get("Type", "Unknown Type"), metrics.get("Team", "Unknown Team")]

                # Raw hours for each status
                for status in statuses:
                    hours = metrics["TimeInStatus"].get(status, 0)
                    row.append(math.ceil(hours))

                # Raw cycle time
                cycle_hours = 0
                if metrics["CycleTime"]:
                    cycle_hours = list(metrics["CycleTime"].values())[0]
                row.append(math.ceil(cycle_hours))

                # Formatted durations for each status
                for status in statuses:
                    hours = metrics["TimeInStatus"].get(status, 0)
                    row.append(self.format_duration(hours))

                # Formatted cycle time
                cycle_time_fmt = self.format_duration(cycle_hours)
                row.append(cycle_time_fmt)

                writer.writerow(row)

        print(f"Results exported to {filename}")


# --- EXECUTION  ---
jira_url = "https://cadent.atlassian.net"
email = "skhan2@cadent.tv"
api_token = "ATATT3xFfGF0lreP5xlVlVwbqNKLfl9oBrUrGes4Sk86KuBzMWTCIeCo14PbAl7xrIKKZvyWngLAURJ10KMOrELMRVJvcI7MOeoeG9VUwdDSAwcKxIix1dPd5HBFCJAP17dJugOLaZnN7A0n_Cg7c9U6rAuqUasIYZy3TZxkIKO33JFdKKTGSJI=0003FA17"

project = JiraTimeInStatusProject(jira_domain=jira_url, email=email, api_token=api_token)

jql_query = '''
type in (story, bug, "Story Bug") 
and "Program Increment[Dropdown]" =30 
and "Team[Team]"= ab077377-6409-47c9-92d4-b4755a39b363-70  
and project != "Google Cloud Migration" 
and status = Done
'''
project.connect_to_jira()
project.calculate_time_in_status_from_jql(jql_query)
project.display_report()
project.export_to_csv()
