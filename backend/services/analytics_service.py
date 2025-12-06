"""
Analytics Service - User profile analysis and comparison metrics.

This service handles compatibility analysis, chart data generation,
and user comparison metrics for the frontend dashboard.
"""
import logging
from collections import defaultdict
from fastapi import HTTPException
from services.github_graphql_service import get_complete_user_profile_graphql, get_users_batch_graphql
from models import UserProfile
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# USER PROFILE FETCHING
# =============================================================================

def _user_data_to_profile(user_data: Dict[str, Any]) -> UserProfile:
    """Convert raw user data dict to UserProfile model."""
    return UserProfile(
        username=user_data["username"],
        avatar_url=user_data["avatar_url"],
        basic_info=user_data["basic_info"],
        languages=user_data["languages"],
        topics=user_data["topics"],
        starred_repos=user_data["starred_repos"],
        recent_activity=user_data["recent_activity"],
        repositories=user_data["repositories"],
    )


async def get_complete_user_info(username: str) -> UserProfile:
    """Fetch complete user info and return as UserProfile model."""
    try:
        user_data = await get_complete_user_profile_graphql(username)
        return _user_data_to_profile(user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user info for {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")


async def get_users_batch(usernames: List[str]) -> List[UserProfile]:
    """Fetch multiple users in a SINGLE API call."""
    try:
        users_data = await get_users_batch_graphql(usernames)
        return [_user_data_to_profile(data) for data in users_data]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch users batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


# =============================================================================
# USER PROFILE ANALYZER - Calculate once, use everywhere
# =============================================================================

class UserProfileAnalyzer:
    """
    Analyzes multiple user profiles with cached computations.
    
    Usage:
        analyzer = UserProfileAnalyzer(profiles)
        radar_data = analyzer.get_radar_chart_data()
        metrics = analyzer.get_comparison_metrics()
        compat = analyzer.get_compatibility_metrics()
    """
    
    def __init__(self, profiles: List[UserProfile]):
        self.profiles = profiles
        self._user_count = len(profiles)
        
        # Cache containers
        self._user_languages: Dict[str, Dict[str, int]] = {}
        self._user_topics: Dict[str, Dict[str, int]] = {}
        self._user_metrics: Dict[str, Dict[str, Any]] = {}
        self._language_totals: Dict[str, int] = {}
        self._top_languages: List[str] = []
        self._user_language_ranks: Dict[str, Dict[str, int]] = {}
        self._language_overlap: Dict[str, int] = {}
        self._topic_overlap: Dict[str, int] = {}
        self._common_languages: List[str] = []
        self._common_topics: List[str] = []
        self._all_languages: set = set()
        self._all_topics: set = set()
        
        self._precompute()
    
    def _precompute(self):
        """Pre-compute all metrics efficiently."""
        # Track user counts per language/topic for overlap
        lang_user_count: Dict[str, int] = defaultdict(int)
        topic_user_count: Dict[str, int] = defaultdict(int)
        
        # SINGLE PASS through profiles
        for profile in self.profiles:
            username = profile.username
            
            # Normalize languages/topics
            languages = dict(profile.languages) if not isinstance(profile.languages, dict) else profile.languages
            topics = dict(profile.topics) if not isinstance(profile.topics, dict) else profile.topics
            
            # Cache normalized data
            self._user_languages[username] = languages
            self._user_topics[username] = topics
            
            # Aggregate totals and track user counts
            for lang, count in languages.items():
                self._language_totals[lang] = self._language_totals.get(lang, 0) + count
                lang_user_count[lang] += 1
            
            for topic in topics:
                topic_user_count[topic] += 1
            
            # Calculate per-user metrics
            self._user_metrics[username] = {
                "activity": self._count_activity(profile.recent_activity or []),
                "repositories": self._calculate_repo_metrics(profile.repositories or []),
                "languages": self._calculate_language_metrics(languages),
                "topics": self._calculate_topic_metrics(topics),
                "expertise": profile.basic_info.get("expertise_analysis", {}),
            }
        
        # Sort languages once, extract top 10
        sorted_langs = sorted(self._language_totals.items(), key=lambda x: x[1], reverse=True)
        self._top_languages = [lang for lang, _ in sorted_langs[:10]]
        top_lang_set = frozenset(self._top_languages)
        
        # Compute user language ranks
        for username, languages in self._user_languages.items():
            user_top = sorted(
                ((l, c) for l, c in languages.items() if l in top_lang_set),
                key=lambda x: x[1], reverse=True
            )
            rank_count = len(user_top)
            self._user_language_ranks[username] = {
                lang: rank_count - idx for idx, (lang, _) in enumerate(user_top)
            }
        
        # Compute overlap (using pre-tracked counts)
        self._language_overlap = {lang: count for lang, count in lang_user_count.items() if count > 1}
        self._common_languages = list(self._language_overlap.keys())
        
        self._topic_overlap = {topic: count for topic, count in topic_user_count.items() if count > 1}
        self._common_topics = list(self._topic_overlap.keys())
        
        self._all_languages = set(self._language_totals.keys())
        self._all_topics = set(topic_user_count.keys())
    
    # =========================================================================
    # PUBLIC METHODS - Return cached data
    # =========================================================================
    
    def get_radar_chart_data(self) -> Dict[str, Any]:
        """Get radar chart data for language comparison."""
        radar_data = []
        for lang in self._top_languages:
            entry = {"language": lang}
            for profile in self.profiles:
                entry[profile.username] = self._user_language_ranks.get(
                    profile.username, {}
                ).get(lang, 0)
            radar_data.append(entry)
        
        return {"languages": radar_data}
    
    def get_comparison_metrics(self) -> Dict[str, Any]:
        """Get comparison metrics for activity, repos, languages, topics."""
        if self._user_count < 2:
            return {}
        
        return {
            "activity_comparison": [{
                "label": "Activity Metrics",
                **{u: m["activity"] for u, m in self._user_metrics.items()}
            }],
            "repository_comparison": [{
                "label": "Repository Stats",
                **{u: m["repositories"] for u, m in self._user_metrics.items()}
            }],
            "language_comparison": [{
                "label": "Language Diversity",
                **{u: m["languages"] for u, m in self._user_metrics.items()}
            }],
            "topic_comparison": [{
                "label": "Topic Interests",
                **{u: m["topics"] for u, m in self._user_metrics.items()}
            }],
        }
    
    def get_compatibility_metrics(self) -> Dict[str, Any]:
        """Get compatibility metrics for visualization."""
        if self._user_count < 2:
            return {}
        
        expertise_overlap = {}
        collaboration_potential = {}
        
        for username, metrics in self._user_metrics.items():
            expertise = metrics["expertise"]
            engagement = expertise.get("engagement_patterns", {})
            
            expertise_overlap[username] = {
                "primary_expertise": expertise.get("primary_expertise", []),
                "collaboration_type": expertise.get("collaboration_type", "Unknown"),
                "activity_consistency": expertise.get("activity_consistency", 0),
                "engagement_patterns": engagement,
            }
            
            collaboration_potential[username] = {
                "project_initiator_ratio": engagement.get("project_initiator_ratio", 0),
                "contributor_ratio": engagement.get("contributor_ratio", 0),
                "active_projects": engagement.get("active_projects", 0),
                "recent_activity_score": engagement.get("recent_activity_score", 0),
            }
        
        return {
            "language_overlap": self._language_overlap,
            "topic_overlap": self._topic_overlap,
            "common_languages": self._common_languages,
            "common_topics": self._common_topics,
            "user_language_distribution": self._user_languages,
            "user_topic_distribution": self._user_topics,
            "expertise_overlap": expertise_overlap,
            "collaboration_potential": collaboration_potential,
        }
    
    def get_user_summary(self, username: str) -> Optional[Dict[str, Any]]:
        """Get summary metrics for a specific user."""
        return self._user_metrics.get(username)
    
    # =========================================================================
    # STATIC COMPUTATION METHODS
    # =========================================================================
    
    @staticmethod
    def _count_activity(activities: List[Dict]) -> Dict[str, int]:
        """Count activities by type in single pass."""
        counts = {
            "pushes": 0, "pull_requests": 0, "issues": 0,
            "stars": 0, "commits": 0, "releases": 0, "forks": 0,
            "repositories": 0, "pr_reviews": 0
        }
        
        type_map = {
            "PushEvent": ("pushes", "commits"),
            "PullRequestEvent": ("pull_requests",),
            "IssuesEvent": ("issues",),
            "WatchEvent": ("stars",),
            "ReleaseEvent": ("releases",),
            "ForkEvent": ("forks",),
            "CreateEvent": ("repositories",),
            "PullRequestReviewEvent": ("pr_reviews",),
        }
        
        for activity in activities:
            event_type = activity.get("type", "")
            count = activity.get("count", 1)
            for key in type_map.get(event_type, ()):
                counts[key] += count
        
        return counts
    
    @staticmethod
    def _calculate_repo_metrics(repos: List[Dict]) -> Dict[str, Any]:
        """Calculate repository metrics in single pass."""
        total = forked = private = stars = forks = watchers = size = 0
        
        for repo in repos:
            total += 1
            if repo.get("fork", False):
                forked += 1
            if repo.get("private", False):
                private += 1
            stars += repo.get("stargazers_count", 0)
            forks += repo.get("forks_count", 0)
            watchers += repo.get("watchers_count", 0)
            size += repo.get("size", 0)
        
        return {
            "total_repos": total,
            "original_repos": total - forked,
            "forked_repos": forked,
            "public_repos": total - private,
            "private_repos": private,
            "total_stars": stars,
            "total_forks": forks,
            "total_watchers": watchers,
            "total_size_kb": size,
            "avg_repo_size": round(size / max(1, total), 1),
        }
    
    @staticmethod
    def _calculate_language_metrics(languages: Dict[str, int]) -> Dict[str, Any]:
        """Calculate language metrics."""
        total_bytes = sum(languages.values())
        primary = max(languages.items(), key=lambda x: x[1])[0] if languages else "None"
        
        percentages = {}
        if total_bytes > 0:
            percentages = {lang: round((b / total_bytes) * 100, 1) for lang, b in languages.items()}
        
        return {
            "total_languages": len(languages),
            "primary_language": primary,
            "primary_language_percentage": percentages.get(primary, 0),
            "language_diversity": round(len(languages) / max(1, total_bytes / 1000), 2),
            "total_code_bytes": total_bytes,
            "language_breakdown": percentages,
        }
    
    @staticmethod
    def _calculate_topic_metrics(topics: Dict[str, int]) -> Dict[str, Any]:
        """Calculate topic metrics."""
        top_topics = [t for t, _ in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]]
        return {
            "total_topics": len(topics),
            "top_topics": top_topics,
            "topic_diversity": len(topics),
        }


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

async def create_radar_chart_data(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Create radar chart data using UserProfileAnalyzer."""
    return UserProfileAnalyzer(user_profiles).get_radar_chart_data()


def create_comparison_metrics_data(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Create comparison metrics using UserProfileAnalyzer."""
    return UserProfileAnalyzer(user_profiles).get_comparison_metrics()


def analyze_compatibility_metrics(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Generate compatibility metrics using UserProfileAnalyzer."""
    return UserProfileAnalyzer(user_profiles).get_compatibility_metrics()
