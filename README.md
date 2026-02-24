# Wiki Automation

Automated daily updates for the [global-workflow wiki](https://github.com/AntonMFernando-NOAA/global-workflow/wiki).

## Overview

This repository contains GitHub Actions automation that:
- **Auto-discovers** all repositories under `AntonMFernando-NOAA`
- **Tracks daily activity**: commits, PRs, and issues
- **Updates the wiki** with daily summaries at 06:00 UTC (weekdays only)

## Features

- ✅ Automatic repository discovery (no manual configuration)
- ✅ Narrative summaries instead of raw commit lists
- ✅ Expandable details for full activity breakdown
- ✅ Weekday-only updates (Mon-Fri)
- ✅ Manual trigger support for custom dates

## Setup Instructions

### 1. Create GitHub Repository

```bash
# Create new repo at: https://github.com/new
# Repository name: wiki
# Description: Automated wiki updates for AntonMFernando-NOAA repositories
# Visibility: Public (or Private with wiki enabled)
```

### 2. Configure GitHub Secrets

Go to repository **Settings** → **Secrets and variables** → **Actions**:

**Secret**: `WIKI_PAT`
- Personal Access Token with:
  - `repo` scope (to read repositories)
  - `admin:org` → `read:org` (to list organization repos, if applicable)
- Generate at: https://github.com/settings/tokens/new

### 3. Push This Repository

```bash
cd /scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation

# Create .github/workflows directory
mkdir -p .github/workflows
mv .github-workflows-daily-wiki-update.yml .github/workflows/daily-wiki-update.yml

# Initialize and push
git add .
git commit -m "Initial commit: automated wiki updates"
git branch -M main
git remote add origin https://github.com/AntonMFernando-NOAA/wiki.git
git push -u origin main
```

### 4. Enable GitHub Actions

1. Go to repository **Settings** → **Actions** → **General**
2. Under "Actions permissions", select **Allow all actions**
3. Under "Workflow permissions", select **Read and write permissions**

### 5. Test the Workflow

1. Go to **Actions** → **Daily Wiki Update**
2. Click **Run workflow**
3. Leave date blank (defaults to yesterday)
4. Click **Run workflow**

The first run will create the wiki page structure.

## How It Works

### Scheduled Execution
- Runs Monday-Friday at 06:00 UTC
- Auto-discovers all `AntonMFernando-NOAA` repositories
- Collects activity from previous day
- Updates wiki with narrative summary

### Manual Execution
```bash
# Via GitHub UI: Actions → Daily Wiki Update → Run workflow
# Specify custom date or leave blank for yesterday
```

### Output Format

**Wiki page**: [Daily-Updates](https://github.com/AntonMFernando-NOAA/global-workflow/wiki/Daily-Updates)

Each entry includes:
- **Date header**: Tuesday, February 24, 2026
- **Narrative summary**: "3 PRs merged: global-workflow#123, GDASApp#456..."
- **Expandable details**: Full breakdown by repository

### Tracked Repositories

Auto-discovers all repositories including:
- global-workflow
- GDASApp  
- UFS_UTILS
- GSI
- Any other public/private repos under your account

## Customization

### Change Schedule
Edit `.github/workflows/daily-wiki-update.yml`:
```yaml
schedule:
  - cron: '0 6 * * 1-5'  # Change to your preferred time
```

### Track Different Organization
Set `GITHUB_ACTOR` variable in the workflow:
```yaml
env:
  GITHUB_ACTOR: 'different-org-name'
```

## Troubleshooting

### Workflow Not Running
- Verify repository default branch is `main`
- Check GitHub Actions is enabled
- Ensure `WIKI_PAT` secret is configured

### Permission Errors
- PAT needs `repo` scope for private repos
- PAT needs `read:org` for organization repos

### No Activity Detected
- Check PAT has access to repositories
- Verify repositories aren't archived
- Run manually with yesterday's date to test

## Maintenance

This automation is self-maintaining:
- No repository list updates needed
- Automatically includes new repositories
- Skips archived repositories

## License

This is a personal automation utility. Use freely.
