import json
from datetime import datetime, timedelta
from jira import JIRA

def generate_sprints(start_date, num_sprints=6, sprint_length_days=14):
    """Generate sprint boundaries given a start date."""
    sprints = []
    current_start = start_date
    for i in range(num_sprints):
        current_end = current_start + timedelta(days=sprint_length_days)
        sprints.append((current_start, current_end))
        current_start = current_end
    return sprints


class JiraMetricsProject:
    def __init__(self, jira_url=None, email=None, api_token=None, file_name=None):
        self.jira_url = jira_url
        self.auth = (email, api_token) if email and api_token else None
        self.file_name = file_name
        self.data_store = {}
        self.results = {
            "Bugs": {"Throughput": {}, "Unclosed": {}},
            "Stories": {"Throughput": {}, "Unclosed": {}},
            "Story Bugs": {"Throughput": {}, "Unclosed": {}}
        }
        # Connect to Jira only if details are provided
        if jira_url and email and api_token:
            self.jira = JIRA(server=jira_url, basic_auth=(email, api_token))
        else:
            self.jira = None

    def load_json_file(self):
        """Load a single JSON file into memory."""
        try:
            with open(self.file_name, 'r', encoding='utf-8') as f:
                self.data_store = json.load(f)
                print(f"Successfully imported: {self.file_name}")
        except FileNotFoundError:
            print(f"Warning: {self.file_name} not found.")
        except UnicodeDecodeError:
            print(f"Encoding Error: {self.file_name} requires UTF-8.")

    def load_jql_query(self, jql):
        """Run a JQL query and load issues into memory."""
        if not self.jira:
            print("Jira connection not initialized. Provide jira_url, email, and api_token.")
            return
        
        all_issues = []
        next_page_token = None
        
        while True:
            # Call enhanced_search_issues with pagination
            issues = self.jira.enhanced_search_issues(
                jql,
                maxResults=100,
                nextPageToken=next_page_token
            )
            
            # Append raw issue data
            all_issues.extend([issue.raw for issue in issues])

            # The ResultList has an attribute for pagination
            next_page_token = getattr(issues, "nextPageToken", None)
            if not next_page_token:
                break
        self.data_store = {"issues": all_issues}
        print(f"Successfully pulled {len(all_issues)} issues from Jira")

    def calculate_throughput(self, sprint_start, num_sprints=6):
        """
        Counts closed tickets by Team and Type, aligned to sprint boundaries.
        """
        issues = self.data_store.get('issues', [])
        sprints = generate_sprints(sprint_start, num_sprints)

        for issue in issues:
            fields = issue.get('fields', {})
            team = fields.get('customfield_11870', {}).get('name', 'Unknown Team')
            issue_type = fields.get('issuetype', {}).get('name', 'Unknown Type')
            res_date = fields.get('resolutiondate')

            # Decide category
            if issue_type.lower() == "bug":
                category = "Bugs"
            elif issue_type.lower() == "story":
                category = "Stories"
            else:
                category = "Story Bugs"

            group_key = f"{team} ({issue_type})"

            if res_date:
                res_dt = datetime.strptime(res_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                # Find which sprint this resolution falls into
                for idx, (start, end) in enumerate(sprints, 1):
                    if start <= res_dt < end:
                        sprint_key = f"Sprint {idx}"
                        if sprint_key not in self.results[category]["Throughput"]:
                            self.results[category]["Throughput"][sprint_key] = {}
                        self.results[category]["Throughput"][sprint_key][group_key] = \
                            self.results[category]["Throughput"][sprint_key].get(group_key, 0) + 1
                        break
            else:
                # Unclosed tickets
                self.results[category]["Unclosed"][group_key] = \
                    self.results[category]["Unclosed"].get(group_key, 0) + 1

    def display_report(self):
        print("\nPMO AUTOMATED METRICS - SPRINT REPORT")

        # Order changed: Stories first, then Bugs, then Other
        for category in ["Stories", "Bugs", "Story Bugs"]:
            print(f"\n=== {category.upper()} ===")

            print(f"\n[METRIC: THROUGHPUT BY SPRINT]")
            if not self.results[category]["Throughput"]:
                print(" - No data calculated yet.")
            else:
                for sprint in sorted(self.results[category]["Throughput"].keys(),
                                     key=lambda x: int(x.split()[1])):
                    groups = self.results[category]["Throughput"][sprint]
                    print(f"\n{sprint}:")
                    for group, count in groups.items():
                        print(f" • {group:<35}: {count} ticket(s) completed")

            print(f"\n[METRIC: UNRESOLVED TICKETS]")
            if not self.results[category]["Unclosed"]:
                print(" - No unresolved tickets calculated yet.")
            else:
                for group, count in self.results[category]["Unclosed"].items():
                    print(f" • {group:<35}: {count} open ticket(s)")

        print("\n" + "="*45)


# --- EXECUTION ---

# Option 1: Use Jira JQL
jira_url = "https://cadent.atlassian.net"
email = "skhan2@cadent.tv"
api_token = "ATATT3xFfGF0lreP5xlVlVwbqNKLfl9oBrUrGes4Sk86KuBzMWTCIeCo14PbAl7xrIKKZvyWngLAURJ10KMOrELMRVJvcI7MOeoeG9VUwdDSAwcKxIix1dPd5HBFCJAP17dJugOLaZnN7A0n_Cg7c9U6rAuqUasIYZy3TZxkIKO33JFdKKTGSJI=0003FA17"

project = JiraMetricsProject(jira_url=jira_url, email=email, api_token=api_token)

jql_query = '''
type in (story, bug, "Story
Bug") and resolutiondate >=-12w 
and "Program Increment[Dropdown]" is not empty 
and "Team[Team]" is not empty 
and project != "Google Cloud Migration"
'''
project.load_jql_query(jql_query)

# --- EXECUTION ---
#my_file = "json_sample_2_tickets.json"
#my_file = "ADM-3881 Fields.json"
#my_file = "ADM-3890 Change History.json"
#my_file = "ADM-3881 Change History.json"
#my_file = "expanded_sample_json.json"
#project = JiraMetricsProject(my_file)
#project.load_json_file()

# Define sprint start date (first sprint boundary)
sprint_start = datetime(2026, 1, 28, tzinfo=datetime.now().astimezone().tzinfo)

project.calculate_throughput(sprint_start, num_sprints=6)
project.display_report()
