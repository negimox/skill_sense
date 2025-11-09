# GitHub Integration Feature Documentation

## Overview

This feature integrates GitHub profile data into the resume upload and analysis process, providing a more comprehensive view of a candidate's technical skills, projects, and contributions.

## Features Implemented

### 1. Backend Implementation

#### GitHub Service (`apps/backend/app/services/github_service.py`)

A comprehensive service for fetching GitHub data using the GitHub REST API v3:

- **User Profile**: Fetches public profile information including name, bio, location, followers, etc.
- **Repositories**: Retrieves up to 100 repositories with details like stars, forks, language, topics
- **Languages**: Aggregates programming languages used across all repositories with percentages
- **Commits**: Fetches recent commit history across repositories (last 365 days)
- **Events**: Retrieves recent public activity/events
- **Rate Limiting**: Handles GitHub API rate limits (60/hour without token, 5000/hour with token)
- **Error Handling**: Comprehensive error handling for network issues, API errors, and rate limits

**Key Methods:**

- `get_user_profile(username)` - Fetch user profile
- `get_user_repositories(username, max_repos)` - Fetch repositories
- `get_user_commits(username, repos)` - Fetch commit history
- `get_comprehensive_profile(username)` - Fetch all data in one call
- `extract_skills_from_github(github_data)` - Extract skills for resume matching

#### Updated Resume Service (`apps/backend/app/services/resume_service.py`)

Enhanced to support GitHub data integration:

- Accepts optional `github_username` parameter in `convert_and_store_resume()`
- Fetches GitHub data during resume upload
- Stores GitHub data alongside resume data
- Passes GitHub data to skill profile creation

#### Updated Resume Upload API (`apps/backend/app/api/router/v1/resume.py`)

Modified to accept GitHub username:

```python
@resume_router.post("/upload")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    github_username: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
```

#### Configuration (`apps/backend/app/core/config.py`)

Added GitHub token configuration:

```python
GITHUB_TOKEN: Optional[str] = None  # Optional for higher rate limits
```

#### Pydantic Schemas

Created comprehensive schemas in `apps/backend/app/schemas/pydantic/github_profile.py`:

- `GitHubProfile` - User profile data
- `GitHubRepository` - Repository information
- `GitHubLanguage` - Language statistics
- `GitHubCommit` - Commit data
- `GitHubComprehensiveProfile` - Complete profile with all data
- `GitHubSkillsExtraction` - Extracted skills for resume matching

Updated resume preview schemas to include GitHub data:

- Added `GitHubProfileSummary` to `ResumePreviewerModel`
- Added `githubProfile` field to JSON schema

### 2. Frontend Implementation

#### File Upload Component (`apps/frontend/components/common/file-upload.tsx`)

Added GitHub username input:

- Text input field for GitHub username (optional)
- Validation and URL encoding
- Passes username as query parameter to upload API
- Informative help text about data collection

```tsx
<input
  id="github-username"
  type="text"
  value={githubUsername}
  onChange={(e) => setGithubUsername(e.target.value)}
  placeholder="e.g., octocat"
  disabled={isUploadingGlobal}
/>
```

#### Resume Display Component (`apps/frontend/components/dashboard/resume-component.tsx`)

Enhanced to display GitHub data:

- **GitHub Stats**: Shows total repos, stars, followers, recent commits
- **Top Languages**: Displays programming languages as badges
- **Notable Repositories**: Lists top repositories with:
  - Repository name (clickable)
  - Description
  - Stars count
  - Primary language
  - Link to GitHub

Beautiful dark-themed UI matching the existing design system.

## API Endpoints

### Upload Resume with GitHub Data

**POST** `/api/v1/resumes/upload?github_username={username}`

**Parameters:**

- `file`: Resume file (PDF/DOCX, max 2MB) - Required
- `github_username`: GitHub username - Optional query parameter

**Response:**

```json
{
  "message": "File resume.pdf successfully processed as MD and stored in the DB",
  "request_id": "uuid",
  "resume_id": "uuid"
}
```

## Data Flow

1. **User uploads resume** with optional GitHub username in frontend
2. **Backend receives** file + GitHub username
3. **Resume processing**:
   - Convert PDF/DOCX to Markdown
   - Store in database
4. **GitHub data fetching** (if username provided):
   - Fetch comprehensive profile from GitHub API
   - Extract skills, languages, projects
   - Store alongside resume data
5. **Skill profile creation**:
   - Aggregate CV data + GitHub data
   - Create comprehensive skill profile
6. **Display**:
   - Show resume with integrated GitHub section
   - Highlight projects and contributions

## GitHub API Rate Limits

### Without Token (Unauthenticated)

- **60 requests per hour**
- Suitable for light usage/testing

### With Token (Authenticated)

- **5000 requests per hour**
- Recommended for production

### Setting Up GitHub Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "SkillSense Resume Matcher")
4. Select scopes:
   - `public_repo` - Access public repositories
   - `read:user` - Read user profile data
5. Generate and copy the token
6. Add to `.env` file:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

## Configuration

### Backend (.env)

```bash
# Optional GitHub Personal Access Token
GITHUB_TOKEN=ghp_your_token_here
```

### Environment Variables

All configuration is in `apps/backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    GITHUB_TOKEN: Optional[str] = None
```

## Error Handling

### Backend

- **GitHubAPIError**: Generic GitHub API errors
- **GitHubRateLimitError**: Specific rate limit exceeded error
- Graceful fallback: Resume upload succeeds even if GitHub fetch fails

### Frontend

- User-friendly error messages
- Optional field - form works without GitHub username
- Clear indication of GitHub data availability

## Security & Privacy

### Data Collection

- Only **public** GitHub data is fetched
- No private repositories or data
- No authentication required from user
- Follows GitHub's Terms of Service

### Data Storage

- GitHub data stored in database alongside resume
- No permanent API tokens stored
- Rate limiting respected

### Best Practices

- Use GitHub token for production (higher limits)
- Cache GitHub data to reduce API calls
- Handle rate limit errors gracefully
- Provide clear user consent messaging

## Usage Examples

### 1. Basic Usage (No GitHub)

```bash
# Just upload resume
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -F "file=@resume.pdf"
```

### 2. With GitHub Profile

```bash
# Upload resume + fetch GitHub data
curl -X POST "http://localhost:8000/api/v1/resumes/upload?github_username=octocat" \
  -F "file=@resume.pdf"
```

### 3. Frontend Usage

1. Navigate to resume upload page
2. Select resume file (PDF/DOCX)
3. Enter GitHub username (optional)
4. Click upload
5. View enhanced resume with GitHub section

## Testing

### Manual Testing

1. Upload resume without GitHub username - should work normally
2. Upload resume with valid GitHub username - should fetch and display data
3. Upload resume with invalid GitHub username - should gracefully fail
4. Test rate limiting - should handle 60 req/hour limit

### Test Accounts

Use these public GitHub profiles for testing:

- `octocat` - GitHub's official test account
- `torvalds` - Linus Torvalds (Linux creator)
- `gvanrossum` - Guido van Rossum (Python creator)

## Future Enhancements

### Potential Improvements

1. **Caching**: Cache GitHub data to reduce API calls
2. **Webhooks**: Real-time updates when GitHub profile changes
3. **Private Repos**: OAuth flow for private repository access
4. **Contribution Graph**: Visual representation of contribution history
5. **Team Analysis**: Analyze organization/team repositories
6. **Tech Stack Detection**: AI-powered technology stack identification
7. **Project Categorization**: Auto-categorize projects by domain
8. **Skill Verification**: Cross-reference CV skills with GitHub activity

### Database Enhancements

Consider adding dedicated tables:

- `github_profiles` - Store GitHub profile data
- `github_repositories` - Repository details
- `github_commits` - Commit history
- Relations to `resumes` table

## Troubleshooting

### Issue: GitHub data not showing

**Solution:**

- Check if GitHub username is correct
- Verify GitHub profile is public
- Check backend logs for API errors
- Ensure httpx is installed: `pip install httpx`

### Issue: Rate limit exceeded

**Solution:**

- Add GitHub token to `.env` file
- Wait for rate limit to reset (1 hour)
- Use caching to reduce API calls

### Issue: Slow upload

**Solution:**

- GitHub API calls can take 2-5 seconds
- Consider async processing
- Add loading indicators in UI
- Limit repositories fetched (currently 30)

## API Documentation

### GitHub REST API v3

Official documentation: https://docs.github.com/en/rest

**Endpoints Used:**

- `GET /users/{username}` - User profile
- `GET /users/{username}/repos` - Repositories list
- `GET /repos/{owner}/{repo}/languages` - Repository languages
- `GET /repos/{owner}/{repo}/commits` - Commit history
- `GET /users/{username}/events/public` - Public events

### Rate Limit Headers

```
X-RateLimit-Limit: 60 (or 5000 with token)
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1372700873
```

## Dependencies

### Backend (requirements.txt)

```
httpx==0.28.1  # For GitHub API requests
```

Already included in project requirements.

### No Additional Frontend Dependencies

Uses existing React and Tailwind CSS.

## Architecture Diagram

```
┌─────────────────┐
│   Frontend      │
│  File Upload    │
│  + GitHub Input │
└────────┬────────┘
         │
         │ POST /upload?github_username=xxx
         │
┌────────▼────────┐
│  Resume API     │
│  Endpoint       │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
┌────────▼────────┐ ┌──▼────────┐ ┌──▼─────────┐
│ Resume Service  │ │  GitHub   │ │  Database  │
│ (PDF→Markdown)  │ │  Service  │ │            │
└─────────────────┘ └──┬────────┘ └────────────┘
                       │
                       │ GitHub REST API v3
                       │
                  ┌────▼──────┐
                  │  GitHub   │
                  │  Servers  │
                  └───────────┘
```

## Summary

This GitHub integration feature significantly enhances the resume analysis capability by:

1. **Providing verifiable technical skills** from actual coding activity
2. **Showcasing real projects** with metrics (stars, forks, languages)
3. **Demonstrating active contribution** through commit history
4. **Offering language proficiency evidence** through code statistics
5. **Enabling comprehensive candidate assessment** beyond traditional CV data

The implementation is:

- ✅ **Optional** - Works with or without GitHub data
- ✅ **Secure** - Only public data, proper error handling
- ✅ **Scalable** - Rate limiting, async operations
- ✅ **User-friendly** - Simple input field, beautiful display
- ✅ **Production-ready** - Comprehensive error handling and logging
