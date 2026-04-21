import json
from datetime import datetime, timedelta
from jira import JIRA

class JiraTimeInStatusProject:
    def __init__(self, file_name=None, jira_domain=None, email=None):
        # JSON file path 
        self.file_name = file_name
        self.data_store = {}

        # Jira connection details 
        self.jira_domain = jira_domain
        self.email = email
        self.api_token = "ATATT3xFfGF0lreP5xlVlVwbqNKLfl9oBrUrGes4Sk86KuBzMWTCIeCo14PbAl7xrIKKZvyWngLAURJ10KMOrELMRVJvcI7MOeoeG9VUwdDSAwcKxIix1dPd5HBFCJAP17dJugOLaZnN7A0n_Cg7c9U6rAuqUasIYZy3TZxkIKO33JFdKKTGSJI=0003FA17"
        self.jira = None

        # Results per ticket
        self.results = {}

    # --- JSON loader (unchanged) ---
    def load_json_file(self):
        try:
            with open(self.file_name, 'r', encoding='utf-8') as f:
                self.data_store = json.load(f)
                print(f"Successfully imported: {self.file_name}")
        except FileNotFoundError:
            print(f"Warning: {self.file_name} not found.")
        except UnicodeDecodeError:
            print(f"Encoding Error: {self.file_name} requires UTF-8.")

    # --- Jira connection ---
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

    # --- Unified calculation for JSON or Jira issues ---
    def calculate_time_in_status(self, issue_key=None, issue_summary=None, changelog=None):
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

        self.results[issue_key or issue_summary or "Unknown Ticket"] = ticket_results

    # --- Jira JQL workflow ---
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


# --- EXECUTION EXAMPLE (JSON workflow, unchanged) ---
#my_file = "PLA-6936_changelog.json"
#my_file = "PLA-6872 Change History.json"
#my_file = "PLA-6990 Change History.json"
#my_file = "ADM-3890 Change History.json"
#my_file = "ADM-3881 Change History.json"
#project = JiraTimeInStatusProject(file_name=my_file)
#project.load_json_file()
#project.calculate_time_in_status(issue_summary=my_file, changelog=project.data_store.get("values", []))
#project.display_report()

# --- EXECUTION EXAMPLE (Live Jira workflow with JQL) ---
project = JiraTimeInStatusProject(jira_domain="https://cadent.atlassian.net", email="skhan2@cadent.tv")
project.connect_to_jira()
project.calculate_time_in_status_from_jql('''
type in (story, bug, "Story Bug") 
and "Program Increment[Dropdown]" =30 
and "Team[Team]" = ab077377-6409-47c9-92d4-b4755a39b363-70 
and project != "Google Cloud Migration" 
and status = Done
''')
project.display_report()
