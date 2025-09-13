#!/bin/bash

# Git Filter-Repo Cleanup Script
# Alternative method using git-filter-repo

set -e

echo "🔧 Git Filter-Repo Cleanup"
echo "=========================="

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "📦 Installing git-filter-repo..."
    pip3 install git-filter-repo
fi

# Create backup
echo "📦 Creating backup..."
BACKUP_DIR="../slack-sentiment-analyzer-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

# Create replacement patterns
cat > replacements.txt << 'EOF'
regex:AIza[0-9A-Za-z_-]{35}==>***REMOVED_API_KEY***
regex:xoxb-[0-9]+-[0-9]+-[0-9]+-[a-z0-9]{24}==>***REMOVED_SLACK_BOT_TOKEN***
regex:xoxp-[0-9]+-[0-9]+-[0-9]+-[a-z0-9]{24}==>***REMOVED_SLACK_TOKEN***
regex:sk-[a-zA-Z0-9]{48}==>***REMOVED_OPENAI_KEY***
literal:GEMINI_API_KEY===>***REMOVED_GEMINI_KEY***
EOF

echo "🧹 Running git-filter-repo cleanup..."

# Run git-filter-repo
git filter-repo --replace-text replacements.txt --force

echo "✅ Cleanup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Review changes: git log --oneline"
echo "2. Force push: git push --force-with-lease origin main"
echo ""
echo "⚠️  Warning: This rewrites history. Team members need to re-clone."

# Cleanup
rm -f replacements.txt

echo "🎉 Filter-repo cleanup completed!"
