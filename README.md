# GitHub Activity Wiki Automation — Setup Guide

Automatically post **daily, weekly, and monthly summaries** of your GitHub
activity (commits, pull requests, and issues) to your repository's wiki.
Summaries are generated as narrative paragraphs using the GitHub Models API
(gpt-4o-mini) with a plain-text fallback — no external services or API keys
required beyond a standard GitHub PAT.

Great for tracking your own work and producing progress reports with minimal
effort.

---

## What it produces

| Workflow | Schedule | Wiki page |
|----------|----------|-----------|
| Daily summary | Mon–Fri at 06:00 UTC | `Daily-Updates.md` |
| Weekly summary | Every Monday at 07:00 UTC | `Weekly-Updates.md` |
| Monthly summary | 1st of each month at 08:00 UTC | `Monthly-Updates.md` |

All workflows can also be triggered manually for any date range.

---

## Repository structure

```
your-wiki-automation-repo/
├── .github/workflows/
│   ├── daily-wiki-update.yml
│   ├── weekly-wiki-update.yml
│   └── monthly-wiki-update.yml
├── generate_daily_summary.py
├── generate_weekly_summary.py
└── generate_monthly_summary.py
```

---

## Setup

### 1. Fork or copy this repository

Fork `AntonMFernando-NOAA/wiki-automation` into your own GitHub account, or
copy the files into a new repository. The repository must be **public** or you
must have a paid plan for GitHub Actions on private repos.

### 2. Initialise the wiki

GitHub wikis must have at least one page before automation can push to them.

1. Go to your repo → **Wiki** tab → **Create the first page**.
2. Set the title to `Home` and save.

### 3. Create a Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens → **Generate new token (classic)**.
2. Grant scopes: **`repo`** (full control) and **`read:org`**.
3. Set expiry to at least 90 days (or no expiry). **If it expires, the workflow
   will fail silently.**
4. Copy the token.

### 4. Add the PAT as a repository secret

In your repo → **Settings → Secrets and variables → Actions → Secrets → New repository secret**:

| Name | Value |
|------|-------|
| `WIKI_PAT` | The PAT you just created |

### 5. (Optional) Set your GitHub username as a variable

By default the scripts track the account that owns the repository. To track a
different username, add a repository variable:

In your repo → **Settings → Secrets and variables → Actions → Variables → New repository variable**:

| Name | Value |
|------|-------|
| `GITHUB_ACTOR` | Your GitHub username (e.g. `octocat`) |

### 6. Enable Actions with write permissions

In your repo → **Settings → Actions → General → Workflow permissions**:
- Select **Read and write permissions** → **Save**.

### 7. Enable the workflows

The workflow files in `.github/workflows/` will be picked up automatically by
GitHub Actions. You can verify they appear under the **Actions** tab of your
repo.

---

## Environment variables reference

| Variable | Set via | Purpose |
|----------|---------|---------|
| `GH_TOKEN` | `secrets.WIKI_PAT` | GitHub API access + GitHub Models narrative generation |
| `GITHUB_ACTOR` | `vars.GITHUB_ACTOR` (optional) | GitHub username to track; defaults to repo owner |
| `SUMMARY_DATE` | Manual workflow input (optional) | Override the target date; defaults to yesterday |
| `WEEK_START` | Manual workflow input (optional) | Override the week start date (weekly workflow) |
| `REPORT_MONTH` | Manual workflow input (optional) | Override the report month `YYYY-MM` (monthly workflow) |

No hardcoded repository list is needed — the scripts automatically discover all
non-archived repositories owned by the tracked user.

---

## Manual and backfill runs

All three workflows support manual triggers. Go to:

**Actions → [workflow name] → Run workflow**

| Field | Example | Effect |
|-------|---------|--------|
| Date (daily) | `2026-03-20` | Summarise that specific day |
| Week start (weekly) | `2026-03-16` | Summarise the week starting on that Monday |
| Month (monthly) | `2026-02` | Summarise that calendar month |

Leave fields blank to use the default (yesterday / last week / last month).
Manual triggers are not restricted to the scheduled days.

---

## How it works

```
Scheduled trigger (or manual)
        │
        ▼
GitHub Actions runner
  1. Checks out the repository
  2. Runs the summary script
        ├── Discovers all non-archived repos under GITHUB_ACTOR
        ├── Queries GitHub API for commits, PRs, and issues in the time window
        ├── Calls GitHub Models API (gpt-4o-mini) for a narrative paragraph
        │   (falls back to a template paragraph if the API is unavailable)
        └── Writes <type>_summary_patch.md
  3. Clones <your-repo>.wiki.git
  4. Prepends the new entry to the relevant wiki page
  5. Commits and pushes the wiki
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Error: GH_TOKEN is not set` | `WIKI_PAT` secret missing or expired | Regenerate PAT and update the secret |
| `403` on `git push` to wiki | Workflow permissions not set to read/write | Settings → Actions → Workflow permissions → Read and write |
| `fatal: could not read from remote` | Wiki not initialised | Create at least one wiki page manually first |
| No activity in summary | PAT lacks `repo` or `read:org` scope | Regenerate PAT with the correct scopes |
| Workflow not visible under Actions | Workflow YAML not in `.github/workflows/` | Confirm files are committed to the default branch |

---

## Customising

| What | Where |
|------|-------|
| Change schedule | Edit the `cron` expression in the relevant workflow YAML |
| Track additional users | Modify `GITHUB_ACTOR` to a comma-separated list (requires script change) |
| Change wiki page names | Edit the filename references in the workflow's push step |
| Adjust narrative style | Edit the prompt string inside `generate_*.py` |
