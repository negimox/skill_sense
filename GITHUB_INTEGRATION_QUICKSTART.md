# GitHub Integration Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Configuration (Optional)

For higher API rate limits, add GitHub token to `.env`:

```bash
cd apps/backend
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

**Get Token**: [GitHub Settings → Tokens](https://github.com/settings/tokens)

### 2. Dependencies

Already included! No additional installation needed.

- Backend: `httpx==0.28.1` (already in requirements.txt)
- Frontend: No new dependencies

### 3. Usage

#### Option A: With GitHub Username

```bash
# Upload resume with GitHub profile
curl -X POST "http://localhost:8000/api/v1/resumes/upload?github_username=octocat" \
  -F "file=@resume.pdf"
```

#### Option B: Without GitHub Username

```bash
# Regular upload (works as before)
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -F "file=@resume.pdf"
```

## 📱 Frontend Usage

1. **Navigate** to upload page: `http://localhost:3000/resume`
2. **Enter** GitHub username (optional): `octocat`
3. **Select** resume file (PDF/DOCX)
4. **Upload** and view enhanced resume!

## 🎨 What You'll See

### GitHub Profile Section

- ✨ **Stats**: Total repos, stars, followers, recent commits
- 🌈 **Languages**: Top programming languages as colorful badges
- 📦 **Projects**: Notable repositories with stars and descriptions
- 🔗 **Links**: Direct links to GitHub profile and repos

## 🔧 Rate Limits

| Type              | Limit     | How                          |
| ----------------- | --------- | ---------------------------- |
| **Without Token** | 60/hour   | Default, no setup            |
| **With Token**    | 5000/hour | Add `GITHUB_TOKEN` to `.env` |

## ✅ Testing

### Test Usernames

Try these public GitHub profiles:

- `octocat` - GitHub's official account
- `torvalds` - Linus Torvalds (Linux)
- `gvanrossum` - Guido van Rossum (Python)

### Test Command

```bash
# Test with octocat
curl -X POST "http://localhost:8000/api/v1/resumes/upload?github_username=octocat" \
  -F "file=@test-resume.pdf"
```

## 📚 Full Documentation

For complete details, see:

- **[GITHUB_INTEGRATION.md](./GITHUB_INTEGRATION.md)** - Complete feature documentation
- **[GITHUB_INTEGRATION_SUMMARY.md](./GITHUB_INTEGRATION_SUMMARY.md)** - Implementation summary

## 🐛 Troubleshooting

### Issue: GitHub data not showing

**Fix**:

- Check username spelling
- Ensure profile is public
- Check backend logs

### Issue: Rate limit exceeded

**Fix**:

- Add GitHub token to `.env`
- Wait 1 hour for reset
- Reduce requests

### Issue: Slow upload

**Expected**: GitHub API calls add 2-5 seconds

## 🎯 Features

✅ Optional - works with or without GitHub data
✅ Secure - only public data accessed
✅ Fast - async operations
✅ Beautiful - matches existing UI
✅ Smart - extracts skills automatically

## 📊 Data Collected (Public Only)

- 👤 Profile: Name, bio, location
- 📦 Repositories: Projects, stars, forks
- 💻 Languages: Python, JavaScript, etc.
- 📈 Commits: Recent contributions
- 🎯 Skills: Extracted from code

## 🔒 Privacy & Security

- ✅ Public data only
- ✅ No authentication required
- ✅ Optional feature
- ✅ Follows GitHub ToS
- ✅ Secure API calls

---

**Need Help?** Check [GITHUB_INTEGRATION.md](./GITHUB_INTEGRATION.md) for detailed documentation.
