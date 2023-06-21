import datetime
from github import Github
import json
from json2html import *
import requests

gh = Github("Your GitHub auth token")
repo = gh.get_repo("Repo to monitor - username/repo_name")
total_snyk_issues = 0
current_gh_issues = []
split_current_issues = []
current_snyk_issues = []
open_gh_issues = []
new_issues = 0
today = datetime.date.today()
yesterday_date = today - datetime.timedelta(days=1)

# "orgs" is the Snyk orgId, and has to be a string
values = """

{
  "filters": {
    "orgs": ["Your Snyk orgId"], 
    "severity": [
      "high",
      "medium",
      "low"
    ],
    "exploitMaturity": [
      "mature",
      "proof-of-concept",
      "no-known-exploit",
      "no-data"
    ],
    "types": [
      "vuln",
      "license"
    ],
    "languages": [
      "javascript"
    ],
    "projects": [],
    "issues": [],
    "identifier": "",
    "fixable": true,
    "isFixed": false
  }
}
"""

headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': 'Your Snyk auth token'
}

new_issues_url = 'https://snyk.io/api/v1/reporting/issues/?from=' + str(yesterday_date) + '&to=' + str(today)

results = requests.post(new_issues_url, data=values, headers=headers)

results_output = results.json()

# getting the issues from github
# taking the issues object, turning it into a string
# splitting the string to format properly
# taking that info, putting it into a list to compare the list of issues from snyk
# need to do this (for now) in order to grab the unique Snyk issue ID
open_issues = repo.get_issues(state='open')
for issue in open_issues:
  issue_object_to_string = str(issue)
  issue_split = issue_object_to_string[13:]
  issue_list = issue_split.split('"')[0]
  current_gh_issues.append(issue_list)
  split_current_issues = [i.split('- ')[1] for i in current_gh_issues]
  

for issue in results_output['results']:
  total_snyk_issues = total_snyk_issues + 1

if total_snyk_issues > 0:
  print(f"Total Snyk issues found: {total_snyk_issues}")

for issue in results_output['results']:
  issue_title = issue['issue']['title']
  issue_type = issue['issue']['type']
  issue_id = issue['issue']['id']
  issue_url = issue['issue']['url']
  issue_severity = issue['issue']['severity']
  issue_version = issue['issue']['version']
  issue_introducedDate = issue['introducedDate']
# if the issue id from the snyk API is not in the list of issues we pulled from GH
# add additional meta data to the issue, then create the issue
# using Snyk's issue ID as it's a unique identifier
# using Snyk's issue ID will prevent duplicated from being entered
  if issue_id not in split_current_issues:
    project_name = issue['project']['name'] 
    project_url = issue['project']['url']
    project_targetFile = issue['project']['targetFile']
    new_issues = new_issues + 1
    
    repo.create_issue(title=issue_title + " | Snyk ID - " + issue_id, body=("Title: " + issue_title) + "\n" 
                                                                      + ("  Snyk ID: " + issue_id) + "\n"
                                                                      + ("  URL: " + issue_url) + "\n"
                                                                      + ("  Severity: " + issue_severity) + "\n"
                                                                      + ("  Version: " + issue_version) + "\n"
                                                                      + ("  Introduced Date: " + issue_introducedDate) + "\n"
                                                                      + ("  Projects with Vulnerability: " + project_name) + "\n"
                                                                      + ("  Project URL: " + project_url) + "\n"
                                                                      + ("  Target File: " + project_targetFile)
                      )

#this section closes github issues once the vulns have been fixed in Snyk:
for issue_from_snyk in results_output['results']:
  snyk_issue_title = issue_from_snyk['issue']['title']
  snyk_issue_type = issue_from_snyk['issue']['type']
  snyk_issue_id = issue_from_snyk['issue']['id']
  current_snyk_issues.append(snyk_issue_title + " | Snyk ID - " + snyk_issue_id)

for gh_open_issue in open_issues:
  open_gh_issues.append(gh_open_issue.title)
  if gh_open_issue.title not in current_snyk_issues:
    print(gh_open_issue.title + " has been fixed in Snyk. The GitHub issue will be closed...")
    gh_open_issue.edit(state='closed')

#output whether or not there are any new issues found, and how many
if new_issues != 0:
  if new_issues > 1:
    print(f"{new_issues} new issues found!")
    print(f"Added {new_issues} issues to GitHub Issues")
  else:
    print(f"{new_issues} new issue found!")
    print(f"Added {new_issues} issue to GitHub Issues")
else:
  print("No new issues found since last scan.")
