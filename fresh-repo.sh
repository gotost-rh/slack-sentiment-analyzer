#!/bin/bash

# Fresh Repository Creation
# Nuclear option: Start with completely clean history

set -e

echo "💥 Fresh Repository Creation"
echo "============================"
echo "⚠️  WARNING: This will create a completely new git history!"
echo "⚠️  All previous commits will be lost!"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 1
fi

# Create backup
echo "📦 Creating backup..."
BACKUP_DIR="../slack-sentiment-analyzer-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

# Remove git history
echo "🗑️  Removing git history..."
rm -rf .git

# Initialize new repository
echo "🆕 Initializing fresh repository..."
git init
git add .
git commit -m "Initial commit - clean history"

echo "✅ Fresh repository created!"
echo ""
echo "📋 Next steps:"
echo "1. Add remote: git remote add origin <your-repo-url>"
echo "2. Force push: git push -u origin main --force"
echo ""
echo "⚠️  Important: This completely rewrites history!"
echo "   All team members must re-clone the repository."

echo "🎉 Fresh repository setup completed!"
