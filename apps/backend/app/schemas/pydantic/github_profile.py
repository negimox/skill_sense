"""
Pydantic schemas for GitHub profile data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class GitHubProfile(BaseModel):
    """GitHub user profile information"""
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Public email address")
    bio: Optional[str] = Field(None, description="User bio")
    location: Optional[str] = Field(None, description="User location")
    company: Optional[str] = Field(None, description="Company name")
    blog: Optional[str] = Field(None, description="Blog/website URL")
    twitter_username: Optional[str] = Field(None, description="Twitter username")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    html_url: Optional[str] = Field(None, description="GitHub profile URL")
    public_repos: int = Field(0, description="Number of public repositories")
    public_gists: int = Field(0, description="Number of public gists")
    followers: int = Field(0, description="Number of followers")
    following: int = Field(0, description="Number of accounts following")
    created_at: Optional[str] = Field(None, description="Account creation date")
    updated_at: Optional[str] = Field(None, description="Last profile update")
    hireable: Optional[bool] = Field(None, description="Whether user is hireable")


class GitHubRepository(BaseModel):
    """GitHub repository information"""
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Repository description")
    html_url: str = Field(..., description="Repository URL")
    language: Optional[str] = Field(None, description="Primary programming language")
    stargazers_count: int = Field(0, description="Number of stars")
    forks_count: int = Field(0, description="Number of forks")
    watchers_count: int = Field(0, description="Number of watchers")
    open_issues_count: int = Field(0, description="Number of open issues")
    size: int = Field(0, description="Repository size in KB")
    is_fork: bool = Field(False, description="Whether this is a forked repository")
    created_at: Optional[str] = Field(None, description="Repository creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")
    pushed_at: Optional[str] = Field(None, description="Last push date")
    topics: List[str] = Field(default_factory=list, description="Repository topics/tags")
    license: Optional[str] = Field(None, description="Repository license")


class GitHubLanguage(BaseModel):
    """Programming language statistics"""
    name: str = Field(..., description="Language name")
    bytes: int = Field(..., description="Bytes of code in this language")
    percentage: float = Field(..., description="Percentage of codebase in this language")


class GitHubCommit(BaseModel):
    """GitHub commit information"""
    sha: Optional[str] = Field(None, description="Commit SHA")
    message: Optional[str] = Field(None, description="Commit message")
    author: Optional[str] = Field(None, description="Commit author name")
    date: Optional[str] = Field(None, description="Commit date")
    repository: Optional[str] = Field(None, description="Repository name")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    html_url: Optional[str] = Field(None, description="Commit URL")


class GitHubEvent(BaseModel):
    """GitHub public event"""
    id: str = Field(..., description="Event ID")
    type: str = Field(..., description="Event type (PushEvent, CreateEvent, etc.)")
    repo_name: Optional[str] = Field(None, description="Repository name")
    created_at: Optional[str] = Field(None, description="Event creation date")


class GitHubStatistics(BaseModel):
    """Aggregated GitHub statistics"""
    total_repositories: int = Field(0, description="Total number of repositories")
    total_stars: int = Field(0, description="Total stars across all repositories")
    total_forks: int = Field(0, description="Total forks across all repositories")
    total_commits_fetched: int = Field(0, description="Total commits fetched")
    recent_commits_90_days: int = Field(0, description="Commits in last 90 days")
    account_age_days: Optional[int] = Field(None, description="Account age in days")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class GitHubComprehensiveProfile(BaseModel):
    """Comprehensive GitHub profile with all aggregated data"""
    username: str = Field(..., description="GitHub username")
    profile: GitHubProfile = Field(..., description="User profile information")
    repositories: List[GitHubRepository] = Field(
        default_factory=list, 
        description="List of repositories"
    )
    languages: List[GitHubLanguage] = Field(
        default_factory=list,
        description="Programming languages used"
    )
    commits: List[GitHubCommit] = Field(
        default_factory=list,
        description="Recent commits"
    )
    events: List[GitHubEvent] = Field(
        default_factory=list,
        description="Recent public events"
    )
    statistics: GitHubStatistics = Field(..., description="Aggregated statistics")
    fetched_at: str = Field(..., description="Data fetch timestamp")


class GitHubProgrammingLanguage(BaseModel):
    """Programming language with proficiency"""
    language: str = Field(..., description="Language name")
    proficiency: str = Field(..., description="Proficiency level (Advanced/Intermediate/Familiar)")
    percentage: float = Field(..., description="Percentage of use")
    evidence: str = Field(..., description="Evidence of proficiency")


class GitHubProjectHighlight(BaseModel):
    """Notable GitHub project"""
    name: str = Field(..., description="Project name")
    description: str = Field("", description="Project description")
    url: str = Field(..., description="Project URL")
    stars: int = Field(0, description="Number of stars")
    forks: int = Field(0, description="Number of forks")
    language: str = Field("N/A", description="Primary language")
    last_updated: Optional[str] = Field(None, description="Last update date")


class GitHubActivityMetrics(BaseModel):
    """GitHub activity and contribution metrics"""
    total_contributions: int = Field(0, description="Total contributions")
    recent_activity_90_days: int = Field(0, description="Activity in last 90 days")
    repository_count: int = Field(0, description="Number of repositories")
    total_stars_received: int = Field(0, description="Total stars received")
    total_forks_received: int = Field(0, description="Total forks received")
    followers: int = Field(0, description="Number of followers")
    account_age_days: int = Field(0, description="Account age in days")


class GitHubSkillsExtraction(BaseModel):
    """Extracted skills and information from GitHub for resume matching"""
    programming_languages: List[GitHubProgrammingLanguage] = Field(
        default_factory=list,
        description="Programming languages with proficiency"
    )
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies and frameworks used"
    )
    project_highlights: List[GitHubProjectHighlight] = Field(
        default_factory=list,
        description="Notable projects"
    )
    activity_metrics: GitHubActivityMetrics = Field(
        ...,
        description="Activity and contribution metrics"
    )
    github_url: Optional[str] = Field(None, description="GitHub profile URL")


class ResumeUploadWithGitHub(BaseModel):
    """Resume upload request with optional GitHub username"""
    github_username: Optional[str] = Field(
        None,
        description="Optional GitHub username to fetch and aggregate profile data",
        min_length=1,
        max_length=39  # GitHub username max length
    )
