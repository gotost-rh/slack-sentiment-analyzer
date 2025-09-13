# Security Cleanup Guide

This document provides steps to clean up any API keys that may have been committed to git history and ensure future security.

## 🔒 Current Security Status

✅ **All files checked** - No hardcoded API keys found in current codebase  
✅ **Environment protection** - `.env` files are properly ignored by git  
✅ **Template file** - `env.standalone` provides safe template  
✅ **Code security** - All API keys loaded from environment variables  

## 🧹 Git History Cleanup

To completely remove any API keys from git history, follow these steps:

### Option 1: BFG Repo-Cleaner (Recommended)

```bash
# Install BFG (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install bfg

# On macOS:
brew install bfg

# Clean the repository
cd /home/shgoto/src/slack-sentiment-analyzer
bfg --replace-text passwords.txt
git reflog expire --expire=now --all && git gc --prune=now --aggressive

# Force push to update remote
git push --force-with-lease origin main
```

Create `passwords.txt` with patterns to replace:
```
AIza******************************* # Replace with placeholder
GEMINI_API_KEY=AIza***************  # Replace with placeholder
```

### Option 2: Git Filter-Repo (Alternative)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove sensitive files from history
git filter-repo --path .env --invert-paths
git filter-repo --replace-text passwords.txt

# Force push
git push --force-with-lease origin main
```

### Option 3: Nuclear Option (Fresh Start)

If the above methods don't work or you want a completely clean start:

```bash
# Create a new repository with current clean code
cd /home/shgoto/src
mv slack-sentiment-analyzer slack-sentiment-analyzer-backup
git clone https://github.com/gotost-rh/slack-sentiment-analyzer.git slack-sentiment-analyzer-clean

# Copy clean files (excluding .git and .env)
cd slack-sentiment-analyzer-backup
cp -r *.py *.md *.txt tests/ ../slack-sentiment-analyzer-clean/

# Push clean version
cd ../slack-sentiment-analyzer-clean
git add .
git commit -m "Clean repository - removed all sensitive data"
git push origin main --force
```

## 🛡️ Security Verification Checklist

Before committing any code, verify:

- [ ] No hardcoded API keys in any files
- [ ] `.env` file is in `.gitignore`
- [ ] Only `env.standalone` template is committed (with placeholder values)
- [ ] All sensitive data loaded from environment variables
- [ ] API keys are masked in console output

### Quick Security Scan

Run this command to check for potential API keys:

```bash
# Check for common API key patterns
grep -r "AIza[0-9A-Za-z_-]\{35\}" . --exclude-dir=.git
grep -r "api_key.*=.*['\"][A-Za-z0-9]\{20,\}" . --exclude-dir=.git
grep -r "GEMINI_API_KEY.*=.*[A-Za-z0-9]" . --exclude-dir=.git

# Should return no results or only template files
```

## 🔐 Environment Setup for Team Members

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gotost-rh/slack-sentiment-analyzer.git
   cd slack-sentiment-analyzer
   ```

2. **Set up environment:**
   ```bash
   cp env.standalone .env
   # Edit .env and add your actual GEMINI_API_KEY
   ```

3. **Verify security:**
   ```bash
   # Make sure .env is ignored
   git status  # Should not show .env as untracked
   ```

## 🚨 Emergency Response

If an API key is accidentally committed:

1. **Immediately revoke the API key** at https://makersuite.google.com/app/apikey
2. **Generate a new API key**
3. **Update your local .env file** with the new key
4. **Clean git history** using one of the methods above
5. **Force push** to update remote repository
6. **Notify team members** to pull the cleaned repository

## 📋 Regular Security Practices

- **Never commit .env files**
- **Use placeholder values in templates**
- **Mask API keys in logs and console output**
- **Regularly rotate API keys**
- **Use environment-specific configurations**
- **Review commits before pushing**

## ✅ Verification Commands

```bash
# Check that .env is properly ignored
git check-ignore .env  # Should return: .env

# Verify no sensitive data in staged files
git diff --cached | grep -i "api_key\|secret\|password"

# Check git history for sensitive data
git log --all --full-history -- .env
```

## 🔗 Additional Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [Git Filter-Repo](https://github.com/newren/git-filter-repo)

