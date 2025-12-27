# Setup Plan: GitHub + LangSmith

## Step 1: Prepare for GitHub

### Create .gitignore
```bash
# In weekenders_app folder
touch .gitignore
```

Add to .gitignore:
```
# API Keys - NEVER commit these
.env
*.env

# Python
__pycache__/
*.pyc
.venv/
venv/

# Test outputs (optional - may want to keep some)
**/tests/**/run_*.json

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
```

### Create .env.example (template for others)
```
TICKETMASTER_API_KEY=your_key_here
GOOGLE_PLACES_KEY=your_key_here
TAVILY_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here
```

### Move API keys to .env
Update all config.py files to use `os.getenv()` without fallback defaults (remove hardcoded keys).

## Step 2: Push to GitHub

```bash
cd /Users/lelandspeth/Data\ Initiatives/weekenders_app

# Initialize repo
git init

# Add files
git add .

# First commit
git commit -m "Initial commit: Weekenders App with 4 agents (Concert, Dining, Events, Locations)"

# Create repo on GitHub (via web or CLI)
gh repo create weekenders-app --private

# Push
git push -u origin main
```

## Step 3: Set Up LangSmith

1. **Create Account**: https://smith.langchain.com
2. **Get API Key**: Settings → API Keys → Create
3. **Add to .env**:
   ```
   LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxx
   ```

4. **Verify**: Run any agent - traces should appear in LangSmith dashboard

## Step 4: Verify LangSmith Integration

Each agent already has `@traceable` decorators. Once API key is set:

```bash
export LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxx

# Test any agent
cd "Langchain/Locations Agent/langchain_final"
python3 test_agent.py "San Francisco"
```

Check https://smith.langchain.com → your project should show traces.

## Quick Checklist

- [ ] Create .gitignore
- [ ] Create .env with all API keys
- [ ] Remove hardcoded keys from config.py files
- [ ] Create .env.example template
- [ ] git init + first commit
- [ ] Create GitHub repo
- [ ] Push to GitHub
- [ ] Create LangSmith account
- [ ] Get LangSmith API key
- [ ] Add to .env
- [ ] Test tracing works

## Time Estimate

- GitHub setup: 10 min
- LangSmith setup: 5 min
- Key migration: 15 min
- Total: ~30 min
