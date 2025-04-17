import sys
import os
import requests
import datetime
from dateutil import parser
from prettytable import PrettyTable
from collections import defaultdict

def get_github_token():
    #Get token for private repos auth
    token = input("Please enter your github token here.")
    return token

def fetch_github_api(url, token):
    #Github auth
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

def get_assigned_tasks(username, token):
    #get assigned  tasks
    url = f"https://api.github.com/search/issues?q=assignee:{username}+is:open&per_page=100"
    response = fetch_github_api(url, token)
    return response.get('items', [])

def get_completed_tasks(username, token):
    """Get completed tasks that were assigned to the user."""
    url = f"https://api.github.com/search/issues?q=assignee:{username}+is:closed&per_page=100"
    response = fetch_github_api(url, token)
    return response.get('items', [])

def format_task(task):
    """Format a task for display."""
    repo_url = task['repository_url']
    repo_name = repo_url.split('/')[-1]
    return f"{repo_name}#{task['number']}: {task['title'][:50]}{'...' if len(task['title']) > 50 else ''}"


def get_task_priority(task):
    #Get task priority
    priority = "Normal"
    for label in task.get('labels', []):
        label_name = label['name'].lower()
        if 'high' in label_name or 'critical' in label_name or 'priority:high' in label_name or 'p0' in label_name or 'p1' in label_name:
            return "High"
        elif 'medium' in label_name or 'priority:medium' in label_name or 'p2' in label_name:
            priority = "Medium"
        elif 'low' in label_name or 'priority:low' in label_name or 'p3' in label_name or 'p4' in label_name:
            if priority == "Normal":
                priority = "Low"
    return priority

def is_task_overdue(task):
###Check if task is overdue based on deadline
    for label in task.get('labels', []):
        label_name = label['name'].lower()
        if 'due:' in label_name or 'deadline:' in label_name:
            try:
                date_str = label_name.split(':')[1].strip()
                due_date = parser.parse(date_str)
                return due_date < datetime.datetime.now()
            except (IndexError, ValueError):
                pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python github_tasks.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    token = get_github_token()
    
    print(f"Fetching GitHub tasks for user: {username}")
    
    # Get tasks
    tasks_assigned_to_user = get_assigned_tasks(username, token)
    completed_tasks = get_completed_tasks(username, token)
    
    # Calculate statistics
    state_counts = defaultdict(int)
    priority_counts = defaultdict(int)
    overdue_count = 0
    
    for task in tasks_assigned_to_user:
        priority = get_task_priority(task)
        priority_counts[priority] += 1
        
        if is_task_overdue(task):
            overdue_count += 1
    
    # Print summary
    print("\n=== GitHub Tasks Summary ===")
    print(f"Username: {username}")
    print(f"Tasks assigned to {username}: {len(tasks_assigned_to_user)}")
    print(f"Completed tasks: {len(completed_tasks)}")
    print(f"Overdue tasks: {overdue_count}")

    # Print priority counts
    print("\n=== Tasks by Priority ===")
    for priority, count in priority_counts.items():
        print(f"{priority}: {count}")
    
    # Print tasks assigned to user (max 3)
    print(f"\n=== Tasks assigned to {username} (up to 3) ===")
    table = PrettyTable(['Repository/Issue', 'Priority'])
    for task in tasks_assigned_to_user[:3]:
        table.add_row([
            format_task(task),
            get_task_priority(task)
        ])
    print(table)

if __name__ == "__main__":
    main()
