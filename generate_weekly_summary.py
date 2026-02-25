#!/usr/bin/env python3
"""
Generate a weekly activity summary with narrative and context.

Environment variables:
    GH_TOKEN         PAT with repo read scope.
    GITHUB_ACTOR     GitHub organization/user to track (default: AntonMFernando-NOAA)
    WEEK_START       ISO date (YYYY-MM-DD). Defaults to last Monday.
"""

import os
import sys
import requests
from datetime import date, timedelta, timezone, datetime
from collections import defaultdict

# ── Config ───────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    sys.exit("Error: GH_TOKEN is not set.")

GITHUB_ACTOR = os.environ.get("GITHUB_ACTOR", "AntonMFernando-NOAA")
WEEK_START_STR = os.environ.get("WEEK_START", "").strip()

# Calculate week start (last Monday) if not provided
if WEEK_START_STR:
    WEEK_START_DATE = date.fromisoformat(WEEK_START_STR)
else:
    today = date.today()
    days_since_monday = (today.weekday()) % 7
    WEEK_START_DATE = today - timedelta(days=days_since_monday)

WEEK_END_DATE = WEEK_START_DATE + timedelta(days=6)  # Sunday

WEEK_START = datetime(WEEK_START_DATE.year, WEEK_START_DATE.month, WEEK_START_DATE.day, 0, 0, 0, tzinfo=timezone.utc)
WEEK_END = datetime(WEEK_END_DATE.year, WEEK_END_DATE.month, WEEK_END_DATE.day, 23, 59, 59, tzinfo=timezone.utc)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def gh_get(url, params=None):
    """Paginated GitHub API GET request."""
    results, p = [], {"per_page": 100, **(params or {})}
    while url:
        r = requests.get(url, headers=HEADERS, params=p)
        r.raise_for_status()
        results.extend(r.json() if isinstance(r.json(), list) else [r.json()])
        url = r.links.get("next", {}).get("url")
        p = None  # Only send params on first request
    return results

def parse_iso(iso_str):
    """Parse ISO timestamp."""
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None

def discover_repos():
    """Discover all repositories the user owns or contributes to."""
    repos = set()
    
    # Owned repos
    try:
        owned = gh_get(f"https://api.github.com/users/{GITHUB_ACTOR}/repos")
        repos.update(r['full_name'] for r in owned if not r.get('fork'))
    except Exception as e:
        print(f"Warning: Could not fetch owned repos: {e}", file=sys.stderr)
    
    # Recent commits on any repo
    try:
        since = WEEK_START.isoformat()
        events = gh_get(f"https://api.github.com/users/{GITHUB_ACTOR}/events", {"per_page": 100})
        for event in events:
            created = parse_iso(event.get('created_at'))
            if created and created >= WEEK_START - timedelta(days=7):
                if 'repo' in event and 'name' in event['repo']:
                    repos.add(event['repo']['name'])
    except Exception as e:
        print(f"Warning: Could not fetch events: {e}", file=sys.stderr)
    
    return sorted(repos)

# ── Activity Collection ───────────────────────────────────────────────────────
def collect_week_activity(repos):
    """Collect all activity for the week."""
    activity = {
        'commits': [],
        'commit_messages': defaultdict(list),
        'prs_merged': [],
        'prs_opened': [],
        'prs_reviewed': [],
        'issues_opened': [],
        'issues_closed': [],
        'issue_comments': [],
        'pr_comments': [],
        'repos_active': set(),
    }
    
    for repo in repos:
        try:
            print(f"  Checking {repo}...", file=sys.stderr)
            
            # Commits
            try:
                since_str = WEEK_START.isoformat()
                until_str = WEEK_END.isoformat()
                commits = gh_get(f"https://api.github.com/repos/{repo}/commits",
                               {"author": GITHUB_ACTOR, "since": since_str, "until": until_str})
                for commit in commits:
                    activity['commits'].append({
                        'repo': repo,
                        'sha': commit['sha'][:7],
                        'message': commit['commit']['message'].split('\n')[0],  # First line only
                        'url': commit['html_url']
                    })
                    activity['commit_messages'][repo].append(commit['commit']['message'].split('\n')[0])
                    activity['repos_active'].add(repo)
            except Exception as e:
                print(f"    Warning: Could not fetch commits: {e}", file=sys.stderr)
            
            # Pull Requests
            try:
                prs = gh_get(f"https://api.github.com/repos/{repo}/pulls", {"state": "all"})
                for pr in prs:
                    created = parse_iso(pr.get('created_at'))
                    merged = parse_iso(pr.get('merged_at'))
                    closed = parse_iso(pr.get('closed_at'))
                    
                    if created and WEEK_START <= created <= WEEK_END and pr['user']['login'] == GITHUB_ACTOR:
                        activity['prs_opened'].append({
                            'repo': repo,
                            'number': pr['number'],
                            'title': pr['title'],
                            'url': pr['html_url']
                        })
                        activity['repos_active'].add(repo)
                    
                    if merged and WEEK_START <= merged <= WEEK_END and pr['user']['login'] == GITHUB_ACTOR:
                        activity['prs_merged'].append({
                            'repo': repo,
                            'number': pr['number'],
                            'title': pr['title'],
                            'url': pr['html_url']
                        })
                        activity['repos_active'].add(repo)
            except Exception as e:
                print(f"    Warning: Could not fetch PRs: {e}", file=sys.stderr)
            
            # Issues
            try:
                issues = gh_get(f"https://api.github.com/repos/{repo}/issues", {"state": "all", "creator": GITHUB_ACTOR})
                for issue in issues:
                    # Skip PRs (they appear in issues API too)
                    if 'pull_request' in issue:
                        continue
                    
                    created = parse_iso(issue.get('created_at'))
                    closed = parse_iso(issue.get('closed_at'))
                    
                    if created and WEEK_START <= created <= WEEK_END:
                        activity['issues_opened'].append({
                            'repo': repo,
                            'number': issue['number'],
                            'title': issue['title'],
                            'url': issue['html_url']
                        })
                        activity['repos_active'].add(repo)
                    
                    if closed and WEEK_START <= closed <= WEEK_END:
                        activity['issues_closed'].append({
                            'repo': repo,
                            'number': issue['number'],
                            'title': issue['title'],
                            'url': issue['html_url']
                        })
                        activity['repos_active'].add(repo)
            except Exception as e:
                print(f"    Warning: Could not fetch issues: {e}", file=sys.stderr)
            
            # Issue Comments
            try:
                since_str = WEEK_START.isoformat()
                comments = gh_get(f"https://api.github.com/repos/{repo}/issues/comments", {"since": since_str})
                for comment in comments:
                    if comment['user']['login'] == GITHUB_ACTOR:
                        created = parse_iso(comment['created_at'])
                        if created and WEEK_START <= created <= WEEK_END:
                            activity['issue_comments'].append({
                                'repo': repo,
                                'url': comment['html_url'],
                                'body': comment['body'][:100]  # First 100 chars
                            })
                            activity['repos_active'].add(repo)
            except Exception as e:
                print(f"    Warning: Could not fetch issue comments: {e}", file=sys.stderr)
            
            # PR Reviews
            try:
                prs_all = gh_get(f"https://api.github.com/repos/{repo}/pulls", {"state": "all"})
                for pr in prs_all:
                    try:
                        reviews = gh_get(f"https://api.github.com/repos/{repo}/pulls/{pr['number']}/reviews")
                        for review in reviews:
                            if review['user']['login'] == GITHUB_ACTOR:
                                submitted = parse_iso(review.get('submitted_at'))
                                if submitted and WEEK_START <= submitted <= WEEK_END:
                                    activity['prs_reviewed'].append({
                                        'repo': repo,
                                        'number': pr['number'],
                                        'title': pr['title'],
                                        'state': review['state'],
                                        'url': review['html_url']
                                    })
                                    activity['repos_active'].add(repo)
                    except Exception:
                        pass  # PR might not have reviews
            except Exception as e:
                print(f"    Warning: Could not fetch PR reviews: {e}", file=sys.stderr)
            
            # PR Review Comments
            try:
                since_str = WEEK_START.isoformat()
                comments = gh_get(f"https://api.github.com/repos/{repo}/pulls/comments", {"since": since_str})
                for comment in comments:
                    if comment['user']['login'] == GITHUB_ACTOR:
                        created = parse_iso(comment['created_at'])
                        if created and WEEK_START <= created <= WEEK_END:
                            activity['pr_comments'].append({
                                'repo': repo,
                                'url': comment['html_url'],
                                'body': comment['body'][:100]
                            })
                            activity['repos_active'].add(repo)
            except Exception as e:
                print(f"    Warning: Could not fetch PR comments: {e}", file=sys.stderr)
                
        except Exception as e:
            print(f"Warning: Error processing {repo}: {e}", file=sys.stderr)
    
    return activity

# ── Summary Generation ────────────────────────────────────────────────────────
def generate_commit_themes(commit_messages):
    """Extract themes from commit messages."""
    themes = defaultdict(list)
    
    for repo, messages in commit_messages.items():
        repo_short = repo.split('/')[-1]
        for msg in messages:
            msg_lower = msg.lower()
            # Simple keyword extraction
            if any(kw in msg_lower for kw in ['fix', 'bug', 'error', 'issue']):
                themes['Bug Fixes'].append(f"{repo_short}: {msg}")
            elif any(kw in msg_lower for kw in ['add', 'new', 'implement', 'create']):
                themes['New Features'].append(f"{repo_short}: {msg}")
            elif any(kw in msg_lower for kw in ['update', 'change', 'modify', 'refactor']):
                themes['Updates'].append(f"{repo_short}: {msg}")
            elif any(kw in msg_lower for kw in ['doc', 'readme', 'comment']):
                themes['Documentation'].append(f"{repo_short}: {msg}")
            elif any(kw in msg_lower for kw in ['test', 'ci', 'build']):
                themes['CI/Testing'].append(f"{repo_short}: {msg}")
            else:
                themes['Other Changes'].append(f"{repo_short}: {msg}")
    
    return themes

def generate_narrative(activity):
    """Generate narrative summary of the week."""
    parts = []
    
    total_commits = len(activity['commits'])
    num_repos = len(activity['repos_active'])
    
    # Primary narrative
    if total_commits > 0:
        repo_names = [r.split('/')[-1] for r in sorted(activity['repos_active'])]
        parts.append(f"Active development week with **{total_commits} commits** across {num_repos} {'repository' if num_repos == 1 else 'repositories'} ({', '.join(repo_names)})")
    
    # PR activity
    if activity['prs_merged']:
        parts.append(f"**{len(activity['prs_merged'])} PR{'s' if len(activity['prs_merged']) > 1 else ''} merged**")
    if activity['prs_opened'] and len(activity['prs_opened']) != len(activity['prs_merged']):
        parts.append(f"**{len(activity['prs_opened'])} PR{'s' if len(activity['prs_opened']) > 1 else ''} opened**")
    
    # Issues
    if activity['issues_opened']:
        parts.append(f"**{len(activity['issues_opened'])} issue{'s' if len(activity['issues_opened']) > 1 else ''} opened**")
    if activity['issues_closed']:
        parts.append(f"**{len(activity['issues_closed'])} issue{'s' if len(activity['issues_closed']) > 1 else ''} closed**")
    
    # Collaboration
    collab = []
    if activity['prs_reviewed']:
        collab.append(f"{len(activity['prs_reviewed'])} PR review{'s' if len(activity['prs_reviewed']) > 1 else ''}")
    if activity['issue_comments']:
        collab.append(f"{len(activity['issue_comments'])} issue comment{'s' if len(activity['issue_comments']) > 1 else ''}")
    if activity['pr_comments']:
        collab.append(f"{len(activity['pr_comments'])} PR comment{'s' if len(activity['pr_comments']) > 1 else ''}")
    
    if collab:
        parts.append(f"Collaboration: {', '.join(collab)}")
    
    if not parts:
        return "Quiet week - focus on planning and design work."
    
    return ". ".join(parts) + "."

def write_summary(activity):
    """Write weekly summary to file."""
    output = []
    
    # Week header
    week_num = WEEK_START_DATE.isocalendar()[1]
    output.append(f"## Week of {WEEK_START_DATE.strftime('%B %d, %Y')} (Week {week_num})\n")
    
    # Narrative
    narrative = generate_narrative(activity)
    output.append(f"{narrative}\n")
    
    # Work Summary (themes from commits)
    if activity['commit_messages']:
        themes = generate_commit_themes(activity['commit_messages'])
        if themes:
            output.append("\n### Work Summary\n")
            for theme, items in sorted(themes.items()):
                if items:
                    output.append(f"\n**{theme}**\n")
                    for item in items[:5]:  # Top 5 per category
                        output.append(f"- {item}\n")
                    if len(items) > 5:
                        output.append(f"- _{len(items) - 5} more..._\n")
    
    # Key Pull Requests
    if activity['prs_merged'] or activity['prs_opened']:
        output.append("\n### Pull Requests\n")
        if activity['prs_merged']:
            output.append("\n**Merged:**\n")
            for pr in activity['prs_merged'][:10]:
                output.append(f"- [{pr['repo'].split('/')[-1]}#{pr['number']}]({pr['url']}): {pr['title']}\n")
        if activity['prs_opened']:
            unmerged = [pr for pr in activity['prs_opened'] if pr not in activity['prs_merged']]
            if unmerged:
                output.append("\n**Opened:**\n")
                for pr in unmerged[:10]:
                    output.append(f"- [{pr['repo'].split('/')[-1]}#{pr['number']}]({pr['url']}): {pr['title']}\n")
    
    # Issues
    if activity['issues_opened'] or activity['issues_closed']:
        output.append("\n### Issues\n")
        if activity['issues_opened']:
            output.append("\n**Opened:**\n")
            for issue in activity['issues_opened'][:10]:
                output.append(f"- [{issue['repo'].split('/')[-1]}#{issue['number']}]({issue['url']}): {issue['title']}\n")
        if activity['issues_closed']:
            output.append("\n**Closed:**\n")
            for issue in activity['issues_closed'][:10]:
                output.append(f"- [{issue['repo'].split('/')[-1]}#{issue['number']}]({issue['url']}): {issue['title']}\n")
    
    # Reviews and Comments
    if activity['prs_reviewed'] or activity['issue_comments'] or activity['pr_comments']:
        output.append("\n### Collaboration Activity\n")
        if activity['prs_reviewed']:
            output.append(f"\n**Code Reviews ({len(activity['prs_reviewed'])}):**\n")
            for review in activity['prs_reviewed'][:10]:
                state_emoji = {"APPROVED": "✅", "CHANGES_REQUESTED": "🔄", "COMMENTED": "💬"}.get(review['state'], "👁️")
                output.append(f"- {state_emoji} [{review['repo'].split('/')[-1]}#{review['number']}]({review['url']}): {review['title']}\n")
        
        total_comments = len(activity['issue_comments']) + len(activity['pr_comments'])
        if total_comments:
            output.append(f"\n**Comments:** {total_comments} ({len(activity['issue_comments'])} on issues, {len(activity['pr_comments'])} on PRs)\n")
    
    # Statistics (collapsed)
    output.append("\n<details>\n<summary>Statistics</summary>\n\n")
    output.append(f"- **Repositories Active**: {len(activity['repos_active'])}\n")
    output.append(f"- **Total Commits**: {len(activity['commits'])}\n")
    output.append(f"- **PRs**: {len(activity['prs_merged'])} merged, {len(activity['prs_opened'])} opened\n")
    output.append(f"- **Issues**: {len(activity['issues_opened'])} opened, {len(activity['issues_closed'])} closed\n")
    output.append(f"- **Reviews**: {len(activity['prs_reviewed'])}\n")
    output.append(f"- **Comments**: {len(activity['issue_comments']) + len(activity['pr_comments'])}\n")
    output.append("\n</details>\n")
    
    output.append("\n---\n\n")
    
    with open("weekly_summary_patch.md", "w") as f:
        f.write("".join(output))
    
    print(f"✓ Weekly summary written for week {week_num} ({WEEK_START_DATE} to {WEEK_END_DATE})")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Discovering repositories for {GITHUB_ACTOR}...")
    repos = discover_repos()
    print(f"Found {len(repos)} repositories")
    
    print(f"Collecting activity for week of {WEEK_START_DATE} to {WEEK_END_DATE}...")
    activity = collect_week_activity(repos)
    
    print(f"\nActivity summary:")
    print(f"  Commits: {len(activity['commits'])}")
    print(f"  PRs merged: {len(activity['prs_merged'])}")
    print(f"  PRs opened: {len(activity['prs_opened'])}")
    print(f"  Issues opened: {len(activity['issues_opened'])}")
    print(f"  Issues closed: {len(activity['issues_closed'])}")
    print(f"  Reviews: {len(activity['prs_reviewed'])}")
    print(f"  Comments: {len(activity['issue_comments']) + len(activity['pr_comments'])}")
    
    write_summary(activity)

if __name__ == "__main__":
    main()
