#!/bin/bash

# Manual Git History Cleanup
# For advanced users who want full control

set -e

echo "⚙️  Manual Git History Cleanup"
echo "============================="

# Create backup
echo "📦 Creating backup..."
BACKUP_DIR="../slack-sentiment-analyzer-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

echo "🔍 Searching for potential API keys in history..."

# Search for API key patterns in git history
echo "Searching for Google API keys (AIza...):"
git log --all --full-history -p | grep -n "AIza" || echo "  ✅ None found"

echo "Searching for GEMINI_API_KEY references:"
git log --all --full-history -p | grep -n "GEMINI_API_KEY" || echo "  ✅ None found"

echo "Searching for Slack tokens:"
git log --all --full-history -p | grep -n "xoxb\|xoxp" || echo "  ✅ None found"

echo "Searching for OpenAI keys:"
git log --all --full-history -p | grep -n "sk-" || echo "  ✅ None found"

echo ""
echo "🔧 If any sensitive data was found above, you can:"
echo "1. Use the BFG cleanup script: ./git-cleanup-script.sh"
echo "2. Use the filter-repo script: ./filter-repo-cleanup.sh"
echo "3. Manually rewrite history with git filter-branch"
echo ""
echo "📋 Current git status:"
git status --short

echo ""
echo "🎯 Recommended action:"
echo "Run: ./git-cleanup-script.sh (safest option)"
