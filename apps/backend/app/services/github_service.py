"""
GitHub Service for fetching user profile, repositories, and commit data.

This service uses the GitHub REST API v3 to gather granular information about a user's
contributions, repositories, and activity.

API Documentation: https://docs.github.com/en/rest
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails"""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded"""
    pass


class GitHubService:
    """
    Service for fetching GitHub user data including profile, repositories, and commits.

    The GitHub REST API allows up to 60 requests per hour for unauthenticated requests
    and 5000 requests per hour for authenticated requests.
    """

    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub service.

        Args:
            github_token: Optional GitHub personal access token for higher rate limits
        """
        self.github_token = github_token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        }
        if github_token:
            self.headers["Authorization"] = f"Bearer {github_token}"

    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GitHub API with error handling.

        Args:
            url: API endpoint URL
            params: Optional query parameters
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary

        Raises:
            GitHubAPIError: If request fails
            GitHubRateLimitError: If rate limit exceeded
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=timeout,
                    follow_redirects=True
                )

                # Check rate limit
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 10:
                    logger.warning(
                        f"GitHub API rate limit low: {remaining} requests remaining"
                    )

                if response.status_code == 403 and "rate limit" in response.text.lower():
                    raise GitHubRateLimitError(
                        "GitHub API rate limit exceeded. Please try again later or provide a GitHub token."
                    )

                if response.status_code == 404:
                    logger.warning(f"GitHub resource not found: {url}")
                    return {}

                # Handle 409 Conflict (e.g., empty repository)
                if response.status_code == 409:
                    logger.warning(f"GitHub resource conflict (possibly empty repo): {url}")
                    return {}

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API HTTP error: {e.response.status_code} - {e.response.text}")
            raise GitHubAPIError(f"GitHub API request failed: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"GitHub API request error: {str(e)}")
            raise GitHubAPIError(f"Failed to connect to GitHub API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in GitHub API request: {str(e)}")
            raise GitHubAPIError(f"Unexpected error: {str(e)}")

    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Fetch public user profile information.

        Endpoint: GET /users/{username}
        Docs: https://docs.github.com/en/rest/users/users#get-a-user

        Args:
            username: GitHub username

        Returns:
            User profile data including:
            - login, name, bio
            - email, location, company
            - public_repos, followers, following
            - created_at, updated_at
        """
        url = f"{self.BASE_URL}/users/{username}"
        logger.info(f"Fetching GitHub profile for user: {username}")

        try:
            data = await self._make_request(url)
            if not data:
                logger.warning(f"No profile data found for user: {username}")
                return {}

            return {
                "login": data.get("login"),
                "name": data.get("name"),
                "email": data.get("email"),
                "bio": data.get("bio"),
                "location": data.get("location"),
                "company": data.get("company"),
                "blog": data.get("blog"),
                "twitter_username": data.get("twitter_username"),
                "avatar_url": data.get("avatar_url"),
                "html_url": data.get("html_url"),
                "public_repos": data.get("public_repos", 0),
                "public_gists": data.get("public_gists", 0),
                "followers": data.get("followers", 0),
                "following": data.get("following", 0),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "hireable": data.get("hireable"),
            }
        except GitHubAPIError as e:
            logger.error(f"Failed to fetch GitHub profile for {username}: {str(e)}")
            return {}

    async def get_user_repositories(
        self,
        username: str,
        max_repos: int = 100,
        sort: str = "updated",
        direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's public repositories.

        Endpoint: GET /users/{username}/repos
        Docs: https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user

        Args:
            username: GitHub username
            max_repos: Maximum number of repositories to fetch (default: 100)
            sort: Sort by 'created', 'updated', 'pushed', 'full_name' (default: 'updated')
            direction: Sort direction 'asc' or 'desc' (default: 'desc')

        Returns:
            List of repository data including:
            - name, description, language
            - stars, forks, watchers
            - created_at, updated_at, pushed_at
        """
        url = f"{self.BASE_URL}/users/{username}/repos"
        logger.info(f"Fetching repositories for user: {username}")

        repos = []
        page = 1
        per_page = min(100, max_repos)  # GitHub API max per_page is 100

        try:
            while len(repos) < max_repos:
                params = {
                    "sort": sort,
                    "direction": direction,
                    "per_page": per_page,
                    "page": page,
                    "type": "owner"  # Only repos owned by the user
                }

                data = await self._make_request(url, params=params)

                if not data or len(data) == 0:
                    break

                for repo in data:
                    if len(repos) >= max_repos:
                        break

                    repos.append({
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "description": repo.get("description"),
                        "html_url": repo.get("html_url"),
                        "language": repo.get("language"),
                        "stargazers_count": repo.get("stargazers_count", 0),
                        "forks_count": repo.get("forks_count", 0),
                        "watchers_count": repo.get("watchers_count", 0),
                        "open_issues_count": repo.get("open_issues_count", 0),
                        "size": repo.get("size", 0),
                        "is_fork": repo.get("fork", False),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at"),
                        "pushed_at": repo.get("pushed_at"),
                        "topics": repo.get("topics", []),
                        "has_wiki": repo.get("has_wiki", False),
                        "has_pages": repo.get("has_pages", False),
                        "license": repo.get("license", {}).get("name") if repo.get("license") else None,
                    })

                # If we received fewer than per_page, we've reached the end
                if len(data) < per_page:
                    break

                page += 1

            logger.info(f"Fetched {len(repos)} repositories for user: {username}")
            return repos

        except GitHubAPIError as e:
            logger.error(f"Failed to fetch repositories for {username}: {str(e)}")
            return []

    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Fetch languages used in a repository.

        Endpoint: GET /repos/{owner}/{repo}/languages
        Docs: https://docs.github.com/en/rest/repos/repos#list-repository-languages

        Args:
            owner: Repository owner username
            repo: Repository name

        Returns:
            Dictionary mapping language names to bytes of code
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"

        try:
            data = await self._make_request(url)
            return data if data else {}
        except GitHubAPIError as e:
            logger.error(f"Failed to fetch languages for {owner}/{repo}: {str(e)}")
            return {}

    async def get_user_commits(
        self,
        username: str,
        repos: List[Dict[str, Any]],
        max_commits_per_repo: int = 50,
        since_days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent commits by the user across their repositories.

        Endpoint: GET /repos/{owner}/{repo}/commits
        Docs: https://docs.github.com/en/rest/commits/commits#list-commits

        Args:
            username: GitHub username
            repos: List of repository dictionaries
            max_commits_per_repo: Maximum commits to fetch per repository
            since_days: Only fetch commits from last N days

        Returns:
            List of commit data including:
            - sha, message, author
            - date, repository
        """
        since_date = (datetime.now() - timedelta(days=since_days)).isoformat()
        all_commits = []

        logger.info(f"Fetching commits for user: {username} across {len(repos)} repositories")

        for repo in repos[:20]:  # Limit to top 20 repos to avoid rate limits
            try:
                url = f"{self.BASE_URL}/repos/{repo['full_name']}/commits"
                params = {
                    "author": username,
                    "since": since_date,
                    "per_page": min(100, max_commits_per_repo),
                }

                data = await self._make_request(url, params=params)

                if not data:
                    continue

                for commit in data[:max_commits_per_repo]:
                    commit_info = commit.get("commit", {})
                    all_commits.append({
                        "sha": commit.get("sha"),
                        "message": commit_info.get("message"),
                        "author": commit_info.get("author", {}).get("name"),
                        "date": commit_info.get("author", {}).get("date"),
                        "repository": repo["name"],
                        "repository_url": repo["html_url"],
                        "html_url": commit.get("html_url"),
                    })

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            except GitHubAPIError as e:
                logger.warning(f"Failed to fetch commits for repo {repo['name']}: {str(e)}")
                continue

        logger.info(f"Fetched {len(all_commits)} commits for user: {username}")
        return all_commits

    async def get_user_events(
        self,
        username: str,
        max_events: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent public events/activity for a user.

        Endpoint: GET /users/{username}/events/public
        Docs: https://docs.github.com/en/rest/activity/events#list-public-events-for-a-user

        Args:
            username: GitHub username
            max_events: Maximum number of events to fetch

        Returns:
            List of event data including:
            - type (PushEvent, CreateEvent, etc.)
            - repo, created_at
        """
        url = f"{self.BASE_URL}/users/{username}/events/public"
        logger.info(f"Fetching recent events for user: {username}")

        events = []
        page = 1
        per_page = min(100, max_events)

        try:
            while len(events) < max_events:
                params = {
                    "per_page": per_page,
                    "page": page,
                }

                data = await self._make_request(url, params=params)

                if not data or len(data) == 0:
                    break

                for event in data:
                    if len(events) >= max_events:
                        break

                    events.append({
                        "id": event.get("id"),
                        "type": event.get("type"),
                        "repo_name": event.get("repo", {}).get("name"),
                        "created_at": event.get("created_at"),
                        "payload": event.get("payload"),
                    })

                if len(data) < per_page:
                    break

                page += 1

            logger.info(f"Fetched {len(events)} events for user: {username}")
            return events

        except GitHubAPIError as e:
            logger.error(f"Failed to fetch events for {username}: {str(e)}")
            return []

    async def get_comprehensive_profile(
        self,
        username: str,
        include_commits: bool = True,
        include_events: bool = True,
        max_repos: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive GitHub profile data including all relevant information.

        This is the main method to use for aggregating GitHub data for resume matching.

        Args:
            username: GitHub username
            include_commits: Whether to fetch commit history (default: True)
            include_events: Whether to fetch recent events (default: True)
            max_repos: Maximum number of repositories to analyze

        Returns:
            Comprehensive profile dictionary with:
            - profile: Basic user information
            - repositories: List of repositories with details
            - languages: Aggregated language statistics
            - commits: Recent commit activity
            - events: Recent public events
            - statistics: Derived statistics for resume matching
        """
        logger.info(f"Fetching comprehensive GitHub profile for: {username}")

        try:
            # Fetch profile and repositories in parallel
            profile, repos = await asyncio.gather(
                self.get_user_profile(username),
                self.get_user_repositories(username, max_repos=max_repos)
            )

            if not profile:
                logger.error(f"Could not fetch profile for username: {username}")
                return {}

            # Aggregate languages from repositories
            languages_data = {}
            for repo in repos[:20]:  # Analyze top 20 repos for languages
                try:
                    repo_langs = await self.get_repository_languages(
                        profile["login"],
                        repo["name"]
                    )
                    for lang, bytes_count in repo_langs.items():
                        languages_data[lang] = languages_data.get(lang, 0) + bytes_count
                    await asyncio.sleep(0.1)  # Rate limit protection
                except Exception as e:
                    logger.warning(f"Failed to fetch languages for repo {repo['name']}: {str(e)}")

            # Calculate language percentages
            total_bytes = sum(languages_data.values())
            languages = [
                {
                    "name": lang,
                    "bytes": bytes_count,
                    "percentage": round((bytes_count / total_bytes * 100), 2) if total_bytes > 0 else 0
                }
                for lang, bytes_count in sorted(
                    languages_data.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

            # Fetch commits and events if requested
            commits = []
            events = []

            if include_commits and repos:
                commits = await self.get_user_commits(username, repos)

            if include_events:
                events = await self.get_user_events(username)

            # Calculate statistics for resume matching
            total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
            total_forks = sum(repo.get("forks_count", 0) for repo in repos)

            # Get top repositories by stars
            top_repos = sorted(
                repos,
                key=lambda x: x.get("stargazers_count", 0),
                reverse=True
            )[:5]

            # Analyze commit patterns
            commit_dates = [commit["date"] for commit in commits if commit.get("date")]
            recent_commit_count = 0
            if commit_dates:
                cutoff_date = datetime.now() - timedelta(days=90)
                for d in commit_dates:
                    if d:
                        try:
                            commit_date = datetime.fromisoformat(d.replace('Z', '+00:00'))
                            # Make both dates naive for comparison
                            if commit_date.replace(tzinfo=None) > cutoff_date:
                                recent_commit_count += 1
                        except Exception:
                            continue

            result = {
                "username": username,
                "profile": profile,
                "repositories": repos,
                "languages": languages,
                "commits": commits,
                "events": events,
                "statistics": {
                    "total_repositories": len(repos),
                    "total_stars": total_stars,
                    "total_forks": total_forks,
                    "total_commits_fetched": len(commits),
                    "recent_commits_90_days": recent_commit_count,
                    "top_repositories": top_repos,
                    "top_languages": languages[:5],
                    "account_age_days": self._calculate_account_age(profile.get("created_at")),
                    "last_activity": profile.get("updated_at"),
                },
                "fetched_at": datetime.now().isoformat(),
            }

            logger.info(f"Successfully fetched comprehensive profile for: {username}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive profile for {username}: {str(e)}")
            return {}

    @staticmethod
    def _calculate_account_age(created_at: Optional[str]) -> Optional[int]:
        """Calculate account age in days"""
        if not created_at:
            return None
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age = (datetime.now().replace(tzinfo=None) - created.replace(tzinfo=None)).days
            return age
        except Exception:
            return None

    def extract_skills_from_github(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract skill-related information from GitHub data for resume matching.

        Args:
            github_data: Comprehensive GitHub profile data

        Returns:
            Dictionary with extracted skills and evidence:
            - programming_languages: List of languages with proficiency indicators
            - technologies: Inferred technologies from repo names/descriptions
            - project_highlights: Notable projects with metrics
            - activity_metrics: Contribution and engagement metrics
        """
        if not github_data or not github_data.get("profile"):
            return {}

        # Extract programming languages
        languages = github_data.get("languages", [])
        programming_languages = [
            {
                "language": lang["name"],
                "proficiency": "Advanced" if lang["percentage"] > 30
                              else "Intermediate" if lang["percentage"] > 10
                              else "Familiar",
                "percentage": lang["percentage"],
                "evidence": f"{lang['bytes']} bytes of code"
            }
            for lang in languages[:10]
        ]

        # Extract project highlights
        repos = github_data.get("repositories", [])
        project_highlights = [
            {
                "name": repo["name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "N/A"),
                "last_updated": repo.get("updated_at"),
            }
            for repo in repos[:10]
            if not repo.get("is_fork")  # Exclude forked repos
        ]

        # Extract technologies from repo topics and descriptions
        technologies = set()
        for repo in repos:
            # Add topics as technologies
            topics = repo.get("topics", [])
            technologies.update(topics)

            # Parse description for common tech keywords
            desc = (repo.get("description") or "").lower()
            tech_keywords = [
                "react", "vue", "angular", "node", "django", "flask",
                "docker", "kubernetes", "aws", "azure", "gcp", "tensorflow",
                "pytorch", "machine learning", "ai", "blockchain", "web3"
            ]
            for keyword in tech_keywords:
                if keyword in desc:
                    technologies.add(keyword)

        # Calculate activity metrics
        stats = github_data.get("statistics", {})
        activity_metrics = {
            "total_contributions": stats.get("total_commits_fetched", 0),
            "recent_activity_90_days": stats.get("recent_commits_90_days", 0),
            "repository_count": stats.get("total_repositories", 0),
            "total_stars_received": stats.get("total_stars", 0),
            "total_forks_received": stats.get("total_forks", 0),
            "followers": github_data.get("profile", {}).get("followers", 0),
            "account_age_days": stats.get("account_age_days", 0),
        }

        return {
            "programming_languages": programming_languages,
            "technologies": sorted(list(technologies)),
            "project_highlights": project_highlights,
            "activity_metrics": activity_metrics,
            "github_url": github_data.get("profile", {}).get("html_url"),
        }
