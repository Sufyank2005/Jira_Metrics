from datetime import datetime, timedelta
from jira import JIRA
import csv

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
    def __init__(self, jira_url=None, email=None, api_token=None):
        self.jira_url = jira_url
        self.auth = (email, api_token) if email and api_token else None
        self.data_store = {}
        self.results = {
            "Bugs": {"Throughput": {}},
            "Stories": {"Throughput": {}},
            "Story Bugs": {"Throughput": {}}
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
                maxResults=100,
                nextPageToken=next_page_token
            )
            all_issues.extend([issue.raw for issue in issues])
            next_page_token = getattr(issues, "nextPageToken", None)
            if not next_page_token:
                break

        self.data_store = {"issues": all_issues}
        print(f"Successfully pulled {len(all_issues)} issues from Jira")

    def calculate_throughput(self, sprint_start, num_sprints=6):
        issues = self.data_store.get('issues', [])
        sprints = generate_sprints(sprint_start, num_sprints)

        for issue in issues:
            fields = issue.get('fields', {})
            team = fields.get('customfield_11870', {}).get('name', 'Unknown Team')
            issue_type = fields.get('issuetype', {}).get('name', 'Unknown Type')
            res_date = fields.get('resolutiondate')

            if issue_type.lower() == "bug":
                category = "Bugs"
            elif issue_type.lower() == "story":
                category = "Stories"
            else:
                category = "Story Bugs"

            # Only team name, no issue type label
            group_key = team

            if res_date:
                res_dt = datetime.strptime(res_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                for idx, (start, end) in enumerate(sprints, 1):
                    if start <= res_dt < end:
                        sprint_key = f"Sprint {idx}"
                        if sprint_key not in self.results[category]["Throughput"]:
                            self.results[category]["Throughput"][sprint_key] = {}
                        self.results[category]["Throughput"][sprint_key][group_key] = \
                            self.results[category]["Throughput"][sprint_key].get(group_key, 0) + 1
                        break

    def display_report(self):
        print("\nPMO AUTOMATED METRICS - SPRINT REPORT")

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

        print("\n" + "="*45)

    def export_to_csv(self, filename=None):
        """Export metrics results into a CSV file named after the team, ordered by sprint and category."""
        # Try to detect the first team name from results
        team_name = None
        for category in ["Stories", "Bugs", "Story Bugs"]:
            metrics = self.results.get(category, {})
            throughput = metrics.get("Throughput", {})
            for sprint, groups in throughput.items():
                for group in groups.keys():
                    team_name = group
                    break
                if team_name:
                    break
            if team_name:
                break

        if not team_name:
            team_name = "UnknownTeam"

        today_str = datetime.now().strftime("%m%d%Y")
        safe_team_name = team_name.replace(" ", "_")
        if filename is None:
            filename = f"Throughput_{safe_team_name}{today_str}.csv"

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Sprint", "Team", "Tickets Completed"])

            # Ensure categories are written in the same order as display_report
            for category in ["Stories", "Bugs", "Story Bugs"]:
                metrics = self.results.get(category, {})
                throughput = metrics.get("Throughput", {})
                # Sort sprints numerically (Sprint 1, Sprint 2, …)
                for sprint in sorted(throughput.keys(), key=lambda x: int(x.split()[1])):
                    groups = throughput[sprint]
                    for group, count in groups.items():
                        writer.writerow([category, sprint, group, count])

        print(f"CSV export complete: {filename}")





# --- EXECUTION ---

jira_url = "https://cadent.atlassian.net"
email = "skhan2@cadent.tv"
api_token = "ATATT3xFfGF0lreP5xlVlVwbqNKLfl9oBrUrGes4Sk86KuBzMWTCIeCo14PbAl7xrIKKZvyWngLAURJ10KMOrELMRVJvcI7MOeoeG9VUwdDSAwcKxIix1dPd5HBFCJAP17dJugOLaZnN7A0n_Cg7c9U6rAuqUasIYZy3TZxkIKO33JFdKKTGSJI=0003FA17"

project = JiraMetricsProject(jira_url=jira_url, email=email, api_token=api_token)

jql_query = '''
type in (story, bug, "Story Bug") 
and "Program Increment[Dropdown]" =30 
and "Team[Team]"= is not empty
and project != "Google Cloud Migration" 
and status = Done
'''
project.load_jql_query(jql_query)

sprint_start = datetime(2026, 1, 28, tzinfo=datetime.now().astimezone().tzinfo)

project.calculate_throughput(sprint_start, num_sprints=6)
project.display_report()
project.export_to_csv()
