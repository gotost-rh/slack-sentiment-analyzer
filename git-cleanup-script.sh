#!/bin/bash

# Git History Cleanup Script for API References
# This script will clean your git history of any API keys or sensitive data

set -e

echo "🧹 Git History Cleanup Script"
echo "=============================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Create backup
echo "📦 Creating backup..."
BACKUP_DIR="../slack-sentiment-analyzer-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

# Create patterns file for BFG
echo "🔍 Creating cleanup patterns..."
cat > cleanup-patterns.txt << 'EOF'
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
EOF

echo "📋 Cleanup patterns created:"
cat cleanup-patterns.txt

# Check if BFG is installed
if ! command -v bfg &> /dev/null; then
    echo "⚠️  BFG Repo-Cleaner not found. Installing..."
    
    # Check if Java is installed
    if ! command -v java &> /dev/null; then
        echo "❌ Java is required for BFG. Please install Java first:"
        echo "   sudo apt update && sudo apt install default-jre"
        exit 1
    fi
    
    # Download BFG
    if [ ! -f "bfg.jar" ]; then
        echo "📥 Downloading BFG Repo-Cleaner..."
        wget -O bfg.jar https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
    fi
    
    BFG_CMD="java -jar bfg.jar"
else
    BFG_CMD="bfg"
fi

echo "🔧 Running BFG cleanup..."

# Run BFG to clean the repository
$BFG_CMD --replace-text cleanup-patterns.txt --no-blob-protection .

echo "🧽 Cleaning up git references..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "✅ Git history cleanup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Review the changes: git log --oneline"
echo "2. If satisfied, force push: git push --force-with-lease origin main"
echo "3. Notify team members to re-clone the repository"
echo ""
echo "⚠️  Important: This rewrites git history. All team members will need to re-clone."

# Clean up temporary files
rm -f cleanup-patterns.txt bfg.jar 2>/dev/null || true

echo "🎉 Cleanup script completed successfully!"
