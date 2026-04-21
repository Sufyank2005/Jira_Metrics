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

        # Results
        self.results = {
            "TimeInStatus": {},
            "CycleTime": {}
        }
        self.issue_key = None
        self.issue_summary = None

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

    # --- Metrics from JSON (unchanged) ---
    def calculate_time_in_status(self):
        transitions = []
        for entry in self.data_store.get("values", []):
            for item in entry.get("items", []):
                if item.get("field") == "status":
                    transitions.append({
                        "from": item.get("fromString"),
                        "to": item.get("toString"),
                        "timestamp": datetime.strptime(entry["created"], "%Y-%m-%dT%H:%M:%S.%f%z")
                    })
        transitions.sort(key=lambda t: t["timestamp"])
        # Time in Status
        for i in range(len(transitions) - 1):
            current = transitions[i]
            next_transition = transitions[i + 1]
            duration_hours = self.business_hours_between(current["timestamp"], next_transition["timestamp"])
            status_name = current["to"]
            self.results["TimeInStatus"][status_name] = self.results["TimeInStatus"].get(status_name, 0) + duration_hours
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
            self.results["CycleTime"][self.issue_key or " Ticket Cycle Time"] = cycle_hours

    # --- Metrics from Jira live ---
    def calculate_time_in_status_from_jira(self, issue_key):
        issue = self.jira.issue(issue_key, expand="changelog")
        self.issue_key = issue.key
        self.issue_summary = issue.fields.summary
        transitions = []
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status":
                    transitions.append({
                        "from": item.fromString,
                        "to": item.toString,
                        "timestamp": datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                    })
        transitions.sort(key=lambda t: t["timestamp"])
        # Time in Status
        for i in range(len(transitions) - 1):
            current = transitions[i]
            next_transition = transitions[i + 1]
            duration_hours = self.business_hours_between(current["timestamp"], next_transition["timestamp"])
            status_name = current["to"]
            self.results["TimeInStatus"][status_name] = self.results["TimeInStatus"].get(status_name, 0) + duration_hours
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
            self.results["CycleTime"][self.issue_key] = cycle_hours

    def display_report(self):
        print("\nPMO AUTOMATED METRICS - TIME IN STATUS REPORT")
        if self.issue_key and self.issue_summary:
            print(f"\nTicket: {self.issue_key} - {self.issue_summary}")
        print(f"\n[METRIC: TIME IN STATUS]")
        if not self.results["TimeInStatus"]:
            print(" - No status durations calculated yet.")
        else:
            for status, hours in self.results["TimeInStatus"].items():
                print(f" • {status:<25}: {self.format_duration(hours)}")
        print(f"\n[METRIC: CYCLE TIME]")
        if not self.results["CycleTime"]:
            print(" - No cycle time calculated yet.")
        else:
            for ticket, hours in self.results["CycleTime"].items():
                print(f" • {ticket:<25}: {self.format_duration(hours)}")
        print("\n" + "="*45)


# --- EXECUTION EXAMPLE (JSON workflow, unchanged) ---
#my_file = "PLA-6936_changelog.json"
#my_file = "PLA-6872 Change History.json"
#my_file = "PLA-6990 Change History.json"
#my_file = "ADM-3890 Change History.json"
#my_file = "ADM-3881 Change History.json"
#project = JiraTimeInStatusProject(file_name=my_file)
#project.load_json_file()
#project.calculate_time_in_status()
#project.display_report()

# --- EXECUTION EXAMPLE (Live Jira workflow) ---
project = JiraTimeInStatusProject(jira_domain="https://cadent.atlassian.net", email="skhan2@cadent.tv")
project.connect_to_jira()
project.calculate_time_in_status_from_jira("PLA-6872")
project.display_report()