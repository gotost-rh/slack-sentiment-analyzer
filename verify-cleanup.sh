#!/bin/bash

# Verification Script for Git History Cleanup
# Run this after cleanup to ensure no API keys remain

set -e

echo "🔍 Git History Verification"
echo "=========================="

# Function to check for patterns
check_pattern() {
    local pattern="$1"
    local description="$2"
    
    echo "Checking for $description..."
    
    # Check current files
    if grep -r "$pattern" . --exclude-dir=.git --exclude="*.sh" --exclude="verify-cleanup.sh" 2>/dev/null; then
        echo "  ❌ Found in current files!"
        return 1
    fi
    
    # Check git history
    if git log --all --full-history -p | grep -q "$pattern" 2>/dev/null; then
        echo "  ❌ Found in git history!"
        return 1
    fi
    
    echo "  ✅ Clean"
    return 0
}

echo "🔍 Scanning for API key patterns..."
echo ""

# Track overall status
overall_status=0

# Check for Google API keys
check_pattern "AIza[0-9A-Za-z_-]\{35\}" "Google API keys (AIza...)" || overall_status=1

# Check for GEMINI_API_KEY with actual values
check_pattern "GEMINI_API_KEY.*=.*[A-Za-z0-9]\{20,\}" "GEMINI_API_KEY with values" || overall_status=1

# Check for Slack bot tokens
check_pattern "xoxb-[0-9]\+-[0-9]\+-[0-9]\+-[a-z0-9]\{24\}" "Slack bot tokens" || overall_status=1

# Check for Slack user tokens
check_pattern "xoxp-[0-9]\+-[0-9]\+-[0-9]\+-[a-z0-9]\{24\}" "Slack user tokens" || overall_status=1

# Check for OpenAI keys
check_pattern "sk-[a-zA-Z0-9]\{48\}" "OpenAI API keys" || overall_status=1

# Check for generic API key patterns
check_pattern "api_key.*=.*['\"][A-Za-z0-9]\{20,\}['\"]" "Generic API keys with values" || overall_status=1

# Check for secret keys with values
check_pattern "secret_key.*=.*['\"][A-Za-z0-9]\{20,\}['\"]" "Secret keys with values" || overall_status=1

echo ""
echo "🔍 Additional security checks..."

# Check for .env files in history
echo "Checking for .env files in git history..."
if git log --all --name-only | grep -q "\.env$" 2>/dev/null; then
    echo "  ⚠️  .env files found in history - consider removing them"
    overall_status=1
else
    echo "  ✅ No .env files in history"
fi

# Check current .gitignore
echo "Checking .gitignore configuration..."
if [ -f ".gitignore" ]; then
    if grep -q "\.env" .gitignore; then
        echo "  ✅ .env files are ignored"
    else
        echo "  ⚠️  Consider adding .env to .gitignore"
    fi
else
    echo "  ⚠️  No .gitignore file found"
fi

echo ""
echo "📊 Verification Results"
echo "======================"

if [ $overall_status -eq 0 ]; then
    echo "🎉 SUCCESS: No API keys or sensitive data found!"
    echo "✅ Your repository appears to be clean."
else
    echo "❌ ISSUES FOUND: Sensitive data detected!"
    echo "🔧 Please run one of the cleanup scripts:"
    echo "   - ./git-cleanup-script.sh (recommended)"
    echo "   - ./filter-repo-cleanup.sh (alternative)"
    echo "   - ./fresh-repo.sh (nuclear option)"
fi

echo ""
echo "📋 Security recommendations:"
echo "1. Always use environment variables for API keys"
echo "2. Add .env to .gitignore"
echo "3. Use git hooks to prevent committing secrets"
echo "4. Regularly scan your repository for sensitive data"
echo "5. Rotate any API keys that may have been exposed"

exit $overall_status
