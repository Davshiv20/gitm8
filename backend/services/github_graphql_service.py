"""
GitHub GraphQL Service - Centralized GitHub data fetching and transformation.

This service handles all GitHub API interactions using GraphQL for efficiency.
"""
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Callable
from fastapi import HTTPException
import logging
from functools import wraps
from datetime import datetime
from collections import defaultdict
from config.settings import get_settings
from services.endpoint_registry import HTTPMethod, registry

logger = logging.getLogger(__name__)


# =============================================================================
# DECORATOR FOR AUTO-ROUTE REGISTRATION
# =============================================================================

def register_endpoint(
    endpoint_name: str = None,
    method: HTTPMethod = HTTPMethod.GET,
    path: str = None,
    tags: list = None,
    service_class: str = None
):
    """Decorator to register a function as an API endpoint."""
    def decorator(func: Callable) -> Callable:
        name = endpoint_name or func.__name__
        registry.register(
            name=name,
            func=func,
            method=method,
            path=path,
            tags=tags,
            service_class=service_class
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# GITHUB GRAPHQL SERVICE
# =============================================================================

class GitHubGraphQLService:
    """Service for fetching GitHub data via GraphQL API."""
    
    _shared_session: Optional[aiohttp.ClientSession] = None
    _session_lock = asyncio.Lock()

    def __init__(self):
        self.api_url = "https://api.github.com/graphql"
        settings = get_settings()
        self.token = settings.github_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get or create shared aiohttp session for connection pooling."""
        if cls._shared_session is None or cls._shared_session.closed:
            async with cls._session_lock:
                if cls._shared_session is None or cls._shared_session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=100,
                        limit_per_host=10,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        enable_cleanup_closed=False
                    )
                    timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)
                    cls._shared_session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        connector_owner=True
                    )
                    logger.info("Created new shared ClientSession")
        return cls._shared_session

    @classmethod
    async def release_session(cls):
        """Close the shared session gracefully."""
        if cls._shared_session and not cls._shared_session.closed:
            await cls._shared_session.close()
            cls._shared_session = None
            await asyncio.sleep(0.25)
            logger.info("Released shared ClientSession")

    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against GitHub API."""
        session = await self.get_session()
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                if response.status == 401:
                    raise HTTPException(status_code=401, detail="Invalid GitHub token")
                elif response.status == 403:
                    raise HTTPException(status_code=403, detail="Rate limit exceeded")
                elif response.status != 200:
                    raise HTTPException(status_code=response.status, detail=f"GitHub API error: {response.status}")
                
                result = await response.json()
                
                if "errors" in result:
                    error_msg = result["errors"][0].get("message", "GraphQL error")
                    raise HTTPException(status_code=400, detail=f"GraphQL error: {error_msg}")
                
                return result["data"]
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            raise HTTPException(status_code=503, detail="Service unavailable")
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            raise HTTPException(status_code=504, detail="Request timeout")

    async def fetch_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch comprehensive user data from GitHub GraphQL API."""
        query = """
        query GetUserProfile($username: String!) {
            user(login: $username) {
                login
                name
                bio
                company
                location
                email
                avatarUrl
                createdAt
                updatedAt
                isHireable
                websiteUrl
                twitterUsername
                followers { totalCount }
                following { totalCount }
                repositories(
                    first: 100,
                    ownerAffiliations: OWNER,
                    orderBy: {field: UPDATED_AT, direction: DESC}
                ) {
                    totalCount
                    nodes {
                        name
                        description
                        url
                        homepageUrl
                        stargazerCount
                        forkCount
                        isFork
                        isPrivate
                        isArchived
                        isDisabled
                        createdAt
                        updatedAt
                        pushedAt
                        primaryLanguage { name color }
                        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                            edges {
                                node { name color }
                                size
                            }
                            totalSize
                        }
                        defaultBranchRef { name }
                    }
                }
                starredRepositories(first: 20, orderBy: {field: STARRED_AT, direction: DESC}) {
                    nodes {
                        name
                        description
                        url
                        primaryLanguage { name }
                        owner { login }
                    }
                }
                contributionsCollection {
                    totalCommitContributions
                    totalPullRequestContributions
                    totalIssueContributions
                    totalRepositoryContributions
                    totalPullRequestReviewContributions
                    contributionCalendar { totalContributions }
                }
            }
        }
        """
        data = await self._execute_query(query, {"username": username})
        return data.get("user")

    def transform_to_analytics_format(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw GitHub data to analytics format (single pass)."""
        repos_data = user_data.get("repositories", {})
        repos_nodes = repos_data.get("nodes", [])
        contributions = user_data.get("contributionsCollection", {})
        
        # SINGLE PASS: Extract languages, topics, and build repositories
        language_bytes: Dict[str, int] = defaultdict(int)
        topic_counts: Dict[str, int] = defaultdict(int)
        repositories = []
        tech_keywords = frozenset(["api", "web", "mobile", "ai", "ml", "data", "security", "testing", "deployment", "database"])
        
        for repo in repos_nodes:
            # Aggregate languages
            for edge in (repo.get("languages") or {}).get("edges", []):
                node = edge.get("node") or {}
                name = node.get("name")
                if name:
                    language_bytes[name] += edge.get("size", 0)
            
            # Extract topics from description
            desc = (repo.get("description") or "").lower()
            for keyword in tech_keywords:
                if keyword in desc:
                    topic_counts[keyword] += 1
                    break
            
            # Count primary language as topic
            primary_lang = repo.get("primaryLanguage") or {}
            lang_name = primary_lang.get("name")
            if lang_name:
                topic_counts[lang_name.lower()] += 1
            
            # Build repository entry
            repositories.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("url"),
                "homepage_url": repo.get("homepageUrl"),
                "fork": repo.get("isFork", False),
                "private": repo.get("isPrivate", False),
                "archived": repo.get("isArchived", False),
                "disabled": repo.get("isDisabled", False),
                "language": lang_name,
                "stargazers_count": repo.get("stargazerCount", 0),
                "forks_count": repo.get("forkCount", 0),
                "updated_at": repo.get("updatedAt"),
                "created_at": repo.get("createdAt"),
                "pushed_at": repo.get("pushedAt"),
            })
        
        # Sort aggregated data
        languages = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
        topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Build starred repos
        starred_repos = [
            {
                "name": r.get("name"),
                "description": r.get("description"),
                "url": r.get("url"),
                "language": (r.get("primaryLanguage") or {}).get("name"),
                "owner": (r.get("owner") or {}).get("login"),
            }
            for r in user_data.get("starredRepositories", {}).get("nodes", [])
        ]
        
        # Build recent activity
        activity_types = [
            ("totalCommitContributions", "PushEvent", "commits"),
            ("totalPullRequestContributions", "PullRequestEvent", "pull requests"),
            ("totalIssueContributions", "IssuesEvent", "issues"),
            ("totalRepositoryContributions", "CreateEvent", "repositories"),
            ("totalPullRequestReviewContributions", "PullRequestReviewEvent", "PR reviews"),
        ]
        recent_activity = []
        for field, event_type, label in activity_types:
            count = contributions.get(field, 0)
            if count > 0:
                recent_activity.append({
                        "type": event_type,
                    "created_at": user_data.get("updatedAt"),
                        "repo": f"{count} {label}",
                        "count": count
                    })
        
        # Calculate expertise
        expertise = self._calculate_expertise(repositories, languages, contributions)
        
        return {
            "username": user_data["login"],
            "avatar_url": user_data.get("avatarUrl") or "",
            "basic_info": {
                "login": user_data["login"],
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "company": user_data.get("company"),
                "location": user_data.get("location"),
                "email": user_data.get("email"),
                "avatar_url": user_data.get("avatarUrl"),
                "created_at": user_data.get("createdAt"),
                "updated_at": user_data.get("updatedAt"),
                "public_repos": repos_data.get("totalCount", 0),
                "followers": user_data.get("followers", {}).get("totalCount", 0),
                "following": user_data.get("following", {}).get("totalCount", 0),
                "expertise_analysis": expertise,
            },
            "languages": languages,
            "topics": topics,
            "starred_repos": starred_repos,
            "recent_activity": recent_activity,
            "repositories": repositories,
        }

    def transform_to_dashboard_format(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw GitHub data to dashboard-friendly format."""
        repos_data = user_data.get("repositories", {})
        repos_nodes = repos_data.get("nodes", [])
        contributions = user_data.get("contributionsCollection", {})
        
        # Single pass: aggregate languages with colors
        language_bytes: Dict[str, int] = defaultdict(int)
        language_colors: Dict[str, str] = {}
        
        for repo in repos_nodes:
            for edge in (repo.get("languages") or {}).get("edges", []):
                node = edge.get("node") or {}
                name = node.get("name")
                if name:
                    language_bytes[name] += edge.get("size", 0)
                    language_colors[name] = node.get("color", "#000000")
        
        total_bytes = sum(language_bytes.values())
        languages = [
            {
                "name": name,
                "bytes": bytes_used,
                "percentage": round((bytes_used / total_bytes * 100), 2) if total_bytes > 0 else 0,
                "color": language_colors.get(name, "#000000")
            }
            for name, bytes_used in sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Top repos by stars
        top_repos = [
            {
                "name": r.get("name"),
                "stars": r.get("stargazerCount", 0),
                "language": (r.get("primaryLanguage") or {}).get("name"),
                "language_color": (r.get("primaryLanguage") or {}).get("color"),
            }
            for r in sorted(repos_nodes, key=lambda x: x.get("stargazerCount", 0), reverse=True)[:5]
        ]
        
        return {
            "username": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "avatar_url": user_data.get("avatarUrl"),
            "email": user_data.get("email"),
            "company": user_data.get("company"),
            "location": user_data.get("location"),
            "website": user_data.get("websiteUrl"),
            "twitter": user_data.get("twitterUsername"),
            "stats": {
                "followers": user_data.get("followers", {}).get("totalCount", 0),
                "following": user_data.get("following", {}).get("totalCount", 0),
                "public_repos": repos_data.get("totalCount", 0),
                "total_contributions": contributions.get("contributionCalendar", {}).get("totalContributions", 0)
            },
            "languages": languages,
            "top_repos": top_repos,
            "hireable": user_data.get("isHireable", False),
            "created_at": user_data.get("createdAt"),
            "updated_at": user_data.get("updatedAt"),
        }

    def _calculate_expertise(self, repositories: List[Dict], languages: List[tuple],
                             contributions: Dict) -> Dict[str, Any]:
        """Calculate expertise analysis in single pass."""
        # Single pass through repos
        total_repos = 0
        forked_repos = 0
        active_projects = 0
        lang_repo_counts: Dict[str, int] = defaultdict(int)
        
        for repo in repositories:
            total_repos += 1
            if repo.get("fork", False):
                forked_repos += 1
            if not repo.get("archived") and not repo.get("disabled"):
                active_projects += 1
            lang = repo.get("language")
            if lang:
                lang_repo_counts[lang] += 1
        
        original_repos = total_repos - forked_repos
        
        # Build expertise for top 5 languages
        primary_expertise = []
        for lang, bytes_count in languages[:5]:
            repos_count = lang_repo_counts.get(lang, 0)
            score = min(10, repos_count * 2 + bytes_count // 1000000)
            level = "Expert" if score > 8 else "Advanced" if score > 5 else "Intermediate"
            primary_expertise.append({
                "language": lang,
                "level": level,
                "repos_count": repos_count,
                "complexity_score": score
            })
        
        # Collaboration type
        if original_repos > forked_repos * 2:
            collaboration_type = "Project Initiator"
        elif forked_repos > original_repos * 2:
            collaboration_type = "Contributor-Focused"
        else:
            collaboration_type = "Balanced"
        
        total_contribs = (
            contributions.get("totalCommitContributions", 0) +
            contributions.get("totalPullRequestContributions", 0) +
            contributions.get("totalIssueContributions", 0)
        )
        
        return {
            "collaboration_type": collaboration_type,
            "activity_consistency": total_contribs / max(1, total_repos),
            "primary_expertise": primary_expertise,
            "engagement_patterns": {
                "project_initiator_ratio": original_repos / max(1, total_repos),
                "contributor_ratio": forked_repos / max(1, total_repos),
                "active_projects": active_projects,
                "recent_activity_score": min(10, total_contribs / 10)
            }
        }

    @register_endpoint(
        endpoint_name="get_user_profile",
        method=HTTPMethod.GET,
        path="/{username}",
        tags=["github"],
        service_class="GitHubGraphQLService"
    )
    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get complete user profile (dashboard format)."""
        try:
            user_data = await self.fetch_user_data(username)
            
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User '{username}' not found on GitHub")
            
            profile = self.transform_to_dashboard_format(user_data)
            
            return {
                "success": True,
                "data": profile,
                "meta": {
                    "username": username,
                    "fetched_at": datetime.utcnow().isoformat()
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching profile for {username}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch user profile")

    async def get_user_for_analytics(self, username: str) -> Dict[str, Any]:
        """Get user data in analytics format."""
        user_data = await self.fetch_user_data(username)
        
        if not user_data:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        return self.transform_to_analytics_format(user_data)

    async def fetch_users_batch(self, usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple users with automatic fallback strategy.
        
        Strategy:
        1. Try lightweight batch query first (reduced data per user)
        2. If batch fails (502/503/504), fall back to sequential fetching
        
        This handles heavy users (lots of commits/repos) gracefully.
        """
        if not usernames:
            return {}
        
        try:
            # Try lightweight batch first
            return await self._fetch_users_batch_light(usernames)
        except HTTPException as e:
            if e.status_code in (502, 503, 504):
                logger.warning(f"Batch query failed with {e.status_code}, falling back to sequential fetching")
                return await self._fetch_users_sequential(usernames)
            raise

    async def _fetch_users_batch_light(self, usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Lightweight batch query - reduced data to avoid 502 errors.
        Fetches 25 repos (vs 100), 5 languages (vs 10), 10 starred (vs 20).
        """
        user_fragments = []
        for i, username in enumerate(usernames):
            user_fragments.append(f'''
                user{i}: user(login: "{username}") {{
                    login
                    name
                    bio
                    company
                    location
                    email
                    avatarUrl
                    createdAt
                    updatedAt
                    isHireable
                    websiteUrl
                    twitterUsername
                    followers {{ totalCount }}
                    following {{ totalCount }}
                    repositories(
                        first: 25,
                        ownerAffiliations: OWNER,
                        orderBy: {{field: UPDATED_AT, direction: DESC}}
                    ) {{
                        totalCount
                        nodes {{
                            name
                            description
                            url
                            homepageUrl
                            stargazerCount
                            forkCount
                            isFork
                            isPrivate
                            isArchived
                            isDisabled
                            createdAt
                            updatedAt
                            pushedAt
                            primaryLanguage {{ name color }}
                            languages(first: 5, orderBy: {{field: SIZE, direction: DESC}}) {{
                                edges {{
                                    node {{ name color }}
                                    size
                                }}
                                totalSize
                            }}
                        }}
                    }}
                    starredRepositories(first: 10, orderBy: {{field: STARRED_AT, direction: DESC}}) {{
                        nodes {{
                            name
                            primaryLanguage {{ name }}
                            owner {{ login }}
                        }}
                    }}
                    contributionsCollection {{
                        totalCommitContributions
                        totalPullRequestContributions
                        totalIssueContributions
                        totalRepositoryContributions
                        totalPullRequestReviewContributions
                        contributionCalendar {{ totalContributions }}
                    }}
                }}
            ''')
        
        query = "query GetMultipleUsers {\n" + "\n".join(user_fragments) + "\n}"
        data = await self._execute_query(query)
        
        # Map results back to usernames
        results = {}
        for i, username in enumerate(usernames):
            user_data = data.get(f"user{i}")
            if user_data:
                results[username] = user_data
        
        return results

    async def _fetch_users_sequential(self, usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fallback: Fetch users one at a time using the full query.
        Slower but handles heavy users reliably.
        """
        results = {}
        for username in usernames:
            try:
                user_data = await self.fetch_user_data(username)
                if user_data:
                    results[username] = user_data
            except HTTPException as e:
                if e.status_code == 404:
                    logger.warning(f"User {username} not found, skipping")
                    continue
                raise
        return results

    async def get_users_for_analytics_batch(self, usernames: List[str]) -> List[Dict[str, Any]]:
        """Get multiple users in analytics format with a SINGLE API call."""
        user_data_map = await self.fetch_users_batch(usernames)
        
        # Check for missing users
        missing = [u for u in usernames if u not in user_data_map]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Users not found: {', '.join(missing)}"
            )
        
        # Transform and return in order
        return [
            self.transform_to_analytics_format(user_data_map[username])
            for username in usernames
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def get_complete_user_profile_graphql(username: str) -> Dict[str, Any]:
    """Get complete user profile in analytics format (single user)."""
    service = GitHubGraphQLService()
    return await service.get_user_for_analytics(username)


async def get_users_batch_graphql(usernames: List[str]) -> List[Dict[str, Any]]:
    """Get multiple user profiles in analytics format (batched - FAST)."""
    service = GitHubGraphQLService()
    return await service.get_users_for_analytics_batch(usernames)
