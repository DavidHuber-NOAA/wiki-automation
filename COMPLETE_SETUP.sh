#!/bin/bash
# Complete setup guide with manual wiki initialization

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════
                    Wiki Automation Complete Setup
═══════════════════════════════════════════════════════════════════════

This will set up your wiki automation in 3 main steps:
  1. Create GitHub repository
  2. Initialize the wiki
  3. Migrate content from global-workflow wiki

═══════════════════════════════════════════════════════════════════════
STEP 1: Create GitHub Repository
═══════════════════════════════════════════════════════════════════════

Open this URL in your browser:
  https://github.com/new

Fill in:
  Repository name:    wiki
  Description:        Automated daily wiki updates for AntonMFernando-NOAA repositories
  Visibility:         Public (or Private)
  ✅ Check:           "Add a README file"
  ✅ Check:           "Add a wiki" (IMPORTANT!)
  
Click: Create repository

───────────────────────────────────────────────────────────────────────
Press Enter when repository is created...
EOF
read

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "STEP 2: Push local code to GitHub"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

cd /scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation || exit 1

# Check if remote exists
if git remote get-url origin &>/dev/null; then
    echo "✅ Remote already configured"
else
    echo "Adding remote..."
    git remote add origin https://github.com/AntonMFernando-NOAA/wiki.git
fi

git branch -M main

echo "Pushing to GitHub..."
git push -u origin main || {
    echo "❌ Push failed. Make sure repository exists and you have access."
    exit 1
}

echo "✅ Code pushed to GitHub"
echo ""

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════
STEP 3: Initialize the Wiki
═══════════════════════════════════════════════════════════════════════

Since GitHub created a default wiki, we need to populate it with content.

Open this URL in your browser:
  https://github.com/AntonMFernando-NOAA/wiki/wiki

You should see a default wiki. Now let's copy content from global-workflow:

───────────────────────────────────────────────────────────────────────
Press Enter to migrate content from global-workflow wiki...
EOF
read

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "STEP 4: Migrate Wiki Content"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Check for GitHub token
if [ -z "$WIKI_PAT" ]; then
    echo "⚠️  WIKI_PAT not set. For public wikis, we can try without auth."
    echo ""
    read -p "Do you want to continue without authentication? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Please export your GitHub token and run again:"
        echo "  export WIKI_PAT='your-github-token'"
        echo "  ./COMPLETE_SETUP.sh"
        exit 1
    fi
    GIT_PREFIX="https://github.com"
else
    GIT_PREFIX="https://x-access-token:${WIKI_PAT}@github.com"
fi

# Clone global-workflow wiki
echo "Cloning global-workflow wiki..."
git clone ${GIT_PREFIX}/AntonMFernando-NOAA/global-workflow.wiki.git temp-source-wiki || {
    echo "❌ Could not clone global-workflow wiki"
    exit 1
}

# Clone wiki-automation wiki
echo "Cloning wiki-automation wiki..."
git clone ${GIT_PREFIX}/AntonMFernando-NOAA/wiki.wiki.git temp-target-wiki || {
    echo "❌ Could not clone wiki-automation wiki"
    echo "   Make sure wiki is enabled and initialized"
    rm -rf temp-source-wiki
    exit 1
}

# Copy pages
cd temp-source-wiki
echo ""
echo "Found pages in global-workflow wiki:"
ls -1 *.md | sed 's/^/  - /'
echo ""

for file in *.md; do
    if [ "$file" = "Daily-Updates.md" ]; then
        echo "⏩ Skipping Daily-Updates.md (will be auto-generated)"
        continue
    fi
    
    if [ -f "$file" ]; then
        echo "📄 Copying $file..."
        cp "$file" ../temp-target-wiki/
    fi
done

# Update the Home page to make it better
cat > ../temp-target-wiki/Home.md << 'EOFHOME'
# Wiki Automation

This wiki automatically tracks daily activity across all **AntonMFernando-NOAA** repositories.

## 📊 Daily Updates

See **[[Daily Updates|Daily-Updates]]** for automated daily summaries of:
- Merged pull requests
- Commits across all repositories  
- Opened and closed issues

Updates are generated automatically every weekday at 06:00 UTC.

## 📅 Weekly Updates

See **[[Weekly Updates|Weekly-Updates]]** for weekly summary narratives.

## 🔧 About This Automation

This wiki is automatically maintained by GitHub Actions workflows in the [wiki-automation repository](https://github.com/AntonMFernando-NOAA/wiki).

The automation:
- Auto-discovers all AntonMFernando-NOAA repositories
- Tracks commits, PRs, and issues
- Generates narrative summaries
- Updates this wiki daily

## Tracked Repositories

All repositories under AntonMFernando-NOAA are automatically tracked, including:
- global-workflow
- GDASApp
- UFS_UTILS
- GSI
- And any others you create

---

_Last updated: $(date +'%Y-%m-%d')_
EOFHOME

cd ../temp-target-wiki

# Commit and push
git config user.name "wiki-migration"
git config user.email "noreply@github.com"

git add .
git status

if git diff --cached --quiet; then
    echo "✅ Wiki already up to date"
else
    git commit -m "Initialize wiki with content from global-workflow

Migrated pages:
- Home.md (enhanced)
- Weekly-Updates.md
- _Sidebar.md

Daily-Updates.md will be auto-generated by GitHub Actions."

    git push
    echo ""
    echo "✅ Wiki content migrated successfully!"
fi

# Cleanup
cd ..
rm -rf temp-source-wiki temp-target-wiki

echo ""
cat << 'EOF'
═══════════════════════════════════════════════════════════════════════
✅ SETUP COMPLETE!
═══════════════════════════════════════════════════════════════════════

Your wiki is now at:
  https://github.com/AntonMFernando-NOAA/wiki/wiki

Next steps:

1. Configure GitHub Actions secret:
   https://github.com/AntonMFernando-NOAA/wiki/settings/secrets/actions
   
   Create secret: WIKI_PAT
   Value: Your GitHub Personal Access Token
   Scopes needed: repo, read:org
   Generate at: https://github.com/settings/tokens/new

2. Enable GitHub Actions:
   https://github.com/AntonMFernando-NOAA/wiki/settings/actions
   ✅ Allow all actions
   ✅ Read and write permissions

3. Test the workflow:
   https://github.com/AntonMFernando-NOAA/wiki/actions
   Click: Daily Wiki Update → Run workflow

4. (Optional) Clean up global-workflow:
   - Delete feature/daily-wiki-automation branch
   - Disable wiki on global-workflow repo

═══════════════════════════════════════════════════════════════════════
EOF
