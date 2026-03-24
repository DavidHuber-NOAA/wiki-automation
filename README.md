# Daily Wiki Update Automation — Setup Guide

This folder contains the scripts and workflow configuration that automate a daily
summary of GitHub activity (commits, pull requests, and issues) to the
**AntonMFernando-NOAA/wiki-automation** wiki.

---

## Repository structure

The automation lives in `AntonMFernando-NOAA/wiki-automation`:

```
wiki-automation/
├── .github/workflows/
│   ├── daily-wiki-update.yml     # runs Mon–Fri at 06:00 UTC
│   ├── weekly-wiki-update.yml
│   └── monthly-wiki-update.yml
├── generate_daily_summary.py     # script called by the daily workflow
├── generate_weekly_summary.py
└── generate_monthly_summary.py
```

---

## One-time setup

### 1. Create a Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens → **Generate new token (classic)**.
2. Grant scopes: **`repo`** (full control), **`read:org`**.
3. Copy the token. Avoid setting a short expiry — if it expires the workflow fails silently.

### 2. Add the PAT as a repository secret

In `AntonMFernando-NOAA/wiki-automation` → **Settings → Secrets and variables → Actions → Secrets**:

| Name | Value |
|------|-------|
| `WIKI_PAT` | The PAT created above |

### 3. Ensure the wiki has at least one page

GitHub wikis must be initialised before the workflow can push to them.  
Go to https://github.com/AntonMFernando-NOAA/wiki-automation/wiki and create a `Home` page if one does not exist.

### 4. Enable Actions with write permissions

In `AntonMFernando-NOAA/wiki-automation` → **Settings → Actions → General → Workflow permissions**:
- Select **Read and write permissions**.

---

## Environment variables used by the scripts

| Variable | Source | Purpose |
|----------|--------|---------|
| `GH_TOKEN` | `secrets.WIKI_PAT` | GitHub API access + GitHub Models API |
| `GITHUB_ACTOR` | `vars.GITHUB_ACTOR` or hardcoded default `AntonMFernando-NOAA` | Username to track |
| `SUMMARY_DATE` | `inputs.date` (optional) | Override date; defaults to yesterday |

No `REPOS` or `WIKI_AUTHOR_USERNAME` variables are needed — the scripts
auto-discover repositories owned by `GITHUB_ACTOR`.

---

## How the daily workflow works

```
Every weekday at 06:00 UTC (Mon–Fri)
        │
        ▼
GitHub Actions runner (wiki-automation repo)
  1. Checks out the repo
  2. Runs generate_daily_summary.py
        ├── Discovers all non-archived repos under GITHUB_ACTOR
        ├── Queries GitHub API for yesterday's commits, PRs, and issues
        └── Writes daily_summary_patch.md
  3. Clones wiki-automation.wiki.git
  4. Prepends today's entry to Daily-Updates.md
  5. Adds [[Daily Updates]] link to _Sidebar.md (once)
  6. Commits and pushes the wiki
```

The wiki page `Daily-Updates.md` grows with the newest entries at the top.

**Wiki location:** https://github.com/AntonMFernando-NOAA/wiki-automation/wiki/Daily-Updates

---

## Manual / backfill run

Trigger the workflow manually from:
**Actions → Daily Wiki Update → Run workflow**
https://github.com/AntonMFernando-NOAA/wiki-automation/actions/workflows/daily-wiki-update.yml

Supply a specific date (e.g. `2026-03-20`) to backfill a missed day.  
The manual trigger works on any day — it is not restricted to weekdays.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Error: GH_TOKEN is not set` | `WIKI_PAT` secret missing or expired | Regenerate PAT and update the secret |
| `403` on `git push` | Workflow permissions not set to read/write | Settings → Actions → Workflow permissions → Read and write |
| `fatal: could not read from remote` | Wiki not initialised | Create at least one wiki page manually |
| No activity in summary | PAT lacks `repo` or `read:org` scope | Regenerate PAT with correct scopes |

---

## Customising

| What | Where |
|------|-------|
| Change schedule | Edit `cron` in `.github/workflows/daily-wiki-update.yml` |
| Track a different user | Set `GITHUB_ACTOR` repo variable in Settings → Variables |
| Change wiki page name | Edit the `Daily-Updates.md` references in the workflow's push step |
