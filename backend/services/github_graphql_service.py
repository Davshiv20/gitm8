import os
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
import logging

class GitHubGraphQLService:
    def __init__(self):
        self.api_url = "https://api.github.com/graphql"
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise HTTPException(status_code=500, detail="GitHub token not set")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        # Configure SSL context and connection settings
        connector = aiohttp.TCPConnector(
            ssl=False,  # Disable SSL verification for development
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(
            headers=self.headers, 
            connector=connector,
            timeout=timeout
        ) as session:
            try:
                payload = {"query": query}
                if variables:
                    payload["variables"] = variables
                
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 401:
                        raise HTTPException(status_code=401, detail="Invalid GitHub token")
                    elif response.status == 403:
                        raise HTTPException(status_code=403, detail="Rate limit exceeded or insufficient permissions")
                    elif response.status != 200:
                        raise HTTPException(status_code=response.status, detail=f"GitHub API error: {response.status}")
                    
                    result = await response.json()
                    
                    if "errors" in result:
                        error_msg = result["errors"][0].get("message", "GraphQL error")
                        logging.error(f"GraphQL query failed: {error_msg}")
                        logging.error(f"Query: {query}")
                        logging.error(f"Variables: {variables}")
                        raise HTTPException(status_code=400, detail=f"GraphQL error: {error_msg}")
                    
                    return result["data"]
            except aiohttp.ClientError as e:
                logging.error(f"Network error in GraphQL query: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
            except asyncio.TimeoutError as e:
                logging.error(f"Timeout error in GraphQL query: {str(e)}")
                raise HTTPException(status_code=500, detail=f"GraphQL query timeout: {str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error in GraphQL query: {str(e)}")
                raise HTTPException(status_code=500, detail=f"GraphQL execution error: {str(e)}")

    async def get_complete_user_profile(self, username: str) -> Dict[str, Any]:
        """Get complete user profile in a single GraphQL query"""
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
                isViewer
                viewerIsFollowing
                viewerCanFollow
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
                repositories(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
                    totalCount
                    nodes {
                        name
                        description
                        url
                        homepageUrl
                        isFork
                        isPrivate
                        isArchived
                        isDisabled

                        primaryLanguage {
                            name
                            color
                        }
                        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                            edges {
                                size
                                node {
                                    name
                                    color
                                }
                            }
                        }
                        updatedAt
                        createdAt
                        pushedAt
                        defaultBranchRef {
                            name
                        }
                    }
                }
                starredRepositories(first: 50, orderBy: {field: STARRED_AT, direction: DESC}) {
                    totalCount
                    nodes {
                        name
                        description
                        url
                        homepageUrl
                        isPrivate
                        isArchived
                        isDisabled

                        primaryLanguage {
                            name
                            color
                        }

                        updatedAt
                        createdAt
                        pushedAt
                        owner {
                            login
                        }
                    }
                }
                contributionsCollection {
                    totalCommitContributions
                    totalIssueContributions
                    totalPullRequestContributions
                    totalPullRequestReviewContributions
                    totalRepositoryContributions
                    commitContributionsByRepository(maxRepositories: 100) {
                        repository {
                            name
                            primaryLanguage {
                                name
                            }
                        }
                        contributions {
                            totalCount
                        }
                    }
                }
                repositoriesContributedTo(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
                    totalCount
                    nodes {
                        name
                        description
                        url
                        isPrivate
                        isArchived
                        isDisabled
                        primaryLanguage {
                            name
                            color
                        }
                        updatedAt
                        pushedAt
                    }
                }
            }
        }
        """
        
        variables = {"username": username}
        data = await self._execute_query(query, variables)
        
        if not data.get("user"):
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        return self._transform_user_data(data["user"])

    def _transform_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GraphQL response to match existing UserProfile structure"""
        # Basic info
        basic_info = {
            "login": user_data["login"],
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "company": user_data.get("company"),
            "location": user_data.get("location"),
            "email": user_data.get("email"),
            "avatar_url": user_data.get("avatarUrl"),
            "created_at": user_data.get("createdAt"),
            "updated_at": user_data.get("updatedAt"),
            "public_repos": user_data.get("repositories", {}).get("totalCount", 0),
            "followers": user_data.get("followers", {}).get("totalCount", 0),
            "following": user_data.get("following", {}).get("totalCount", 0),
        }
        
        # Languages (aggregated from repositories) - null-safe
        language_stats = {}
        for repo in user_data.get("repositories", {}).get("nodes", []):
            edges = ((repo.get("languages") or {}).get("edges")) or []
            for lang_edge in edges:
                node = (lang_edge or {}).get("node") or {}
                if not node:
                    continue
                lang_name = node.get("name")
                lang_size = (lang_edge or {}).get("size", 0)
                if not lang_name:
                    continue
                if lang_name in language_stats:
                    language_stats[lang_name] += lang_size
                else:
                    language_stats[lang_name] = lang_size
        
        languages = [(lang, size) for lang, size in sorted(language_stats.items(), key=lambda x: x[1], reverse=True)]
        
        # Topics (extracted from repository descriptions and languages as fallback)
        topic_stats = {}
        for repo in user_data.get("repositories", {}).get("nodes", []):
            # Extract potential topics from description and language
            if repo.get("description"):
                desc = repo["description"].lower()
                # Common tech keywords that might indicate topics
                tech_keywords = ["api", "web", "mobile", "ai", "ml", "data", "security", "testing", "deployment", "database"]
                for keyword in tech_keywords:
                    if keyword in desc:
                        topic_stats[keyword] = topic_stats.get(keyword, 0) + 1
            
            # Use language as a topic if available
            primary_language_name = ((repo.get("primaryLanguage") or {}).get("name"))
            if primary_language_name:
                lang = primary_language_name.lower()
                topic_stats[lang] = topic_stats.get(lang, 0) + 1
        
        topics = [(topic, count) for topic, count in sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)]
        
        # Repositories
        repositories = []
        for repo in user_data.get("repositories", {}).get("nodes", []):
            repo_data = {
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("url"),
                "homepage_url": repo.get("homepageUrl"),
                "fork": repo.get("isFork", False),
                "private": repo.get("isPrivate", False),
                "archived": repo.get("isArchived", False),
                "disabled": repo.get("isDisabled", False),
                "language": ((repo.get("primaryLanguage") or {}).get("name")),
                "updated_at": repo.get("updatedAt"),
                "created_at": repo.get("createdAt"),
                "pushed_at": repo.get("pushedAt"),
                "default_branch": ((repo.get("defaultBranchRef") or {}).get("name")),
            }
            repositories.append(repo_data)
        
        # Starred repositories
        starred_repos = []
        for repo in user_data.get("starredRepositories", {}).get("nodes", []):
            starred_repo = {
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("url"),
                "homepage_url": repo.get("homepageUrl"),
                # Keep only string-ish fields to satisfy UserProfile typing
                "language": ((repo.get("primaryLanguage") or {}).get("name")),
                "updated_at": repo.get("updatedAt"),
                "created_at": repo.get("createdAt"),
                "pushed_at": repo.get("pushedAt"),
                "owner": ((repo.get("owner") or {}).get("login")),
            }
            starred_repos.append(starred_repo)
        
        # Recent activity (simulated from contributions)
        recent_activity = []
        contributions = user_data.get("contributionsCollection", {})
        
        if contributions.get("totalCommitContributions", 0) > 0:
            recent_activity.append({
                "type": "PushEvent",
                "created_at": user_data.get("updatedAt"),
                "repo": "Recent commits"
            })
        
        if contributions.get("totalPullRequestContributions", 0) > 0:
            recent_activity.append({
                "type": "PullRequestEvent",
                "created_at": user_data.get("updatedAt"),
                "repo": "Recent PRs"
            })
        
        # Expertise analysis (calculated from the data)
        expertise_analysis = self._calculate_expertise_analysis(
            repositories, languages, topics, contributions
        )
        
        return {
            "username": user_data["login"],
            "avatar_url": user_data.get("avatarUrl") or "",
            "basic_info": {**basic_info, "expertise_analysis": expertise_analysis},
            "languages": languages,
            "topics": topics,
            "starred_repos": starred_repos,
            "recent_activity": recent_activity,
            "repositories": repositories,
        }

    def _calculate_expertise_analysis(self, repositories: List[Dict], languages: List[tuple], 
                                    topics: List[tuple], contributions: Dict) -> Dict[str, Any]:
        """Calculate expertise analysis from the collected data"""
        total_repos = len(repositories)
        original_repos = len([r for r in repositories if not r["fork"]])
        forked_repos = len([r for r in repositories if r["fork"]])
        
        # Calculate language expertise
        primary_expertise = []
        for lang, bytes_count in languages[:5]:  # Top 5 languages
            repos_with_lang = len([r for r in repositories if r.get("language") == lang])
            complexity_score = min(10, repos_with_lang * 2 + (bytes_count // 1000000))  # Simple scoring
            
            primary_expertise.append({
                "language": lang,
                "level": "Expert" if complexity_score > 8 else "Advanced" if complexity_score > 5 else "Intermediate",
                "repos_count": repos_with_lang,
                "complexity_score": complexity_score
            })
        
        # Determine collaboration type
        if original_repos > forked_repos * 2:
            collaboration_type = "Project Initiator"
        elif forked_repos > original_repos * 2:
            collaboration_type = "Contributor-Focused"
        else:
            collaboration_type = "Balanced"
        
        # Calculate activity consistency
        total_contributions = (
            contributions.get("totalCommitContributions", 0) +
            contributions.get("totalPullRequestContributions", 0) +
            contributions.get("totalIssueContributions", 0)
        )
        activity_consistency = total_contributions / max(1, total_repos)  # Contributions per repo
        
        # Engagement patterns
        engagement_patterns = {
            "project_initiator_ratio": original_repos / max(1, total_repos),
            "contributor_ratio": forked_repos / max(1, total_repos),
            "active_projects": len([r for r in repositories if not r["archived"] and not r["disabled"]]),
            "recent_activity_score": min(10, total_contributions / 10)  # Normalize to 1-10
        }
        
        return {
            "collaboration_type": collaboration_type,
            "activity_consistency": activity_consistency,
            "primary_expertise": primary_expertise,
            "engagement_patterns": engagement_patterns
        }

# Convenience function for backward compatibility
async def get_complete_user_profile_graphql(username: str) -> Dict[str, Any]:
    """Get complete user profile using GraphQL (replaces multiple REST calls)"""
    service = GitHubGraphQLService()
    return await service.get_complete_user_profile(username)
