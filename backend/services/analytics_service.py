import asyncio
import logging
from fastapi import HTTPException
from services.github_graphql_service import get_complete_user_profile_graphql
from models import UserProfile
from typing import Dict, Any, List

async def get_complete_user_info(username: str) -> UserProfile:
    try:
        # Use GraphQL service exclusively
        user_data = await get_complete_user_profile_graphql(username)
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
    except Exception as e:
        logging.error(f"GraphQL service failed for {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")
    

async def create_radar_chart_data(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """
    Create radar chart data for the given user profiles.
    Returns a list of dicts like: {"language": "js", "shivam": 7, "ds": 0}
    Only the top 7 languages (by total usage across all users) are included.
    Instead of raw percentages, assigns reversed ranks per user (7 = most used, 1 = least used among top 7, 0 = not used).
    """
    # Convert profile.languages to dict if not already
    for profile in user_profiles:
        profile.languages = dict(profile.languages)

    # Aggregate total usage for each language across all users
    language_totals = {}
    for profile in user_profiles:
        for lang, count in profile.languages.items():
            language_totals[lang] = language_totals.get(lang, 0) + count

    # Pick top 7 languages by total usage
    top_languages = sorted(language_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    top_language_names = [lang for lang, _ in top_languages]

    # For each user, assign reversed ranks to their languages (7 = most used, 1 = least used among top 7)
    user_language_ranks = {}
    for profile in user_profiles:

        user_top_langs = [(lang, count) for lang, count in profile.languages.items() if lang in top_language_names]
        sorted_langs = sorted(user_top_langs, key=lambda x: x[1], reverse=True)
        n = len(sorted_langs)
        ranks = {}
        for idx, (lang, _) in enumerate(sorted_langs):
            # Highest usage gets highest rank (n), next gets n-1, ..., lowest gets 1
            ranks[lang] = n - idx
        user_language_ranks[profile.username] = ranks

    # Prepare radar chart data for only the top 7 languages, using reversed ranks
    radar_data = []
    for lang in top_language_names:
        lang_entry = {"language": lang}
        for profile in user_profiles:
            ranks = user_language_ranks.get(profile.username, {})
            lang_entry[profile.username] = ranks.get(lang, 0)  # 0 if not present
        radar_data.append(lang_entry)

    return {"languages": radar_data}

def create_comparison_metrics_data(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """
    Create comparison metrics data for line charts showing different parameters of comparison.
    Returns structured data for activity metrics, repository stats, and other comparison points.
    """
    if len(user_profiles) < 2:
        return {}

    # Convert profile.languages and topics to dict if not already (for consistency and speed)
    for profile in user_profiles:
        if not isinstance(profile.languages, dict):
            profile.languages = dict(profile.languages)
        if not isinstance(profile.topics, dict):
            profile.topics = dict(profile.topics)

    user_metrics = {}

    for profile in user_profiles:
        username = profile.username
        recent_activity = profile.recent_activity or []
        repos = profile.repositories or []
        languages = profile.languages
        topics = profile.topics

        # Activity metrics (optimized with single pass)
        activity_counts = {
            'pushes': 0, 
            'pull_requests': 0, 
            'issues': 0, 
            'stars': 0,
            'commits': 0,
            'releases': 0,
            'forks': 0
        }
        for activity in recent_activity:
            activity_type = activity.get('type', '')
            count = activity.get('count', 1)  # Use actual count, default to 1 for backward compatibility
            
            if activity_type == 'PushEvent':
                activity_counts['pushes'] += count
                activity_counts['commits'] += count  # For our new format, commits = pushes
            elif activity_type == 'PullRequestEvent':
                activity_counts['pull_requests'] += count
            elif activity_type == 'IssuesEvent':
                activity_counts['issues'] += count
            elif activity_type == 'WatchEvent':
                activity_counts['stars'] += count
            elif activity_type == 'ReleaseEvent':
                activity_counts['releases'] += count
            elif activity_type == 'ForkEvent':
                activity_counts['forks'] += count
            elif activity_type == 'CreateEvent':
                # Repository contributions
                activity_counts['repositories'] = activity_counts.get('repositories', 0) + count
            elif activity_type == 'PullRequestReviewEvent':
                # PR reviews
                activity_counts['pr_reviews'] = activity_counts.get('pr_reviews', 0) + count

        # Repository metrics (optimized)
        total_repos = len(repos)
        original_repos = sum(1 for r in repos if not r.get('fork', False))
        forked_repos = total_repos - original_repos
        total_stars = sum(r.get('stargazers_count', 0) for r in repos)
        total_forks = sum(r.get('forks_count', 0) for r in repos)
        
        # Calculate additional repository metrics
        total_watchers = sum(r.get('watchers_count', 0) for r in repos)
        total_size = sum(r.get('size', 0) for r in repos)  # Size in KB
        public_repos = sum(1 for r in repos if not r.get('private', False))
        private_repos = total_repos - public_repos

        # Language metrics (optimized)
        total_languages = len(languages)
        primary_language = max(languages.items(), key=lambda x: x[1])[0] if languages else "None"
        total_bytes = sum(languages.values())
        language_diversity = len(languages) / max(1, total_bytes / 1000)
        
        # Calculate language distribution percentages
        language_percentages = {}
        if total_bytes > 0:
            for lang, bytes_count in languages.items():
                language_percentages[lang] = round((bytes_count / total_bytes) * 100, 1)

        # Topic metrics (optimized)
        total_topics = len(topics)
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]
        top_topic_names = [topic for topic, _ in top_topics]

        user_metrics[username] = {
            'activity': activity_counts,
            'repositories': {
                'total_repos': total_repos,
                'original_repos': original_repos,
                'forked_repos': forked_repos,
                'public_repos': public_repos,
                'private_repos': private_repos,
                'total_stars': total_stars,
                'total_forks': total_forks,
                'total_watchers': total_watchers,
                'total_size_kb': total_size,
                'avg_repo_size': round(total_size / max(1, total_repos), 1)
            },
            'languages': {
                'total_languages': total_languages,
                'primary_language': primary_language,
                'primary_language_percentage': language_percentages.get(primary_language, 0),
                'language_diversity': round(language_diversity, 2),
                'total_code_bytes': total_bytes,
                'language_breakdown': language_percentages
            },
            'topics': {
                'total_topics': total_topics,
                'top_topics': top_topic_names,
                'topic_diversity': total_topics
            }
        }


    # Build response data structure
    activity_metrics = [{
        "label": "Activity Metrics",
        **{username: metrics['activity'] for username, metrics in user_metrics.items()}
    }]

    repo_metrics = [{
        "label": "Repository Stats",
        **{username: metrics['repositories'] for username, metrics in user_metrics.items()}
    }]

    language_metrics = [{
        "label": "Language Diversity",
        **{username: metrics['languages'] for username, metrics in user_metrics.items()}
    }]

    topic_metrics = [{
        "label": "Topic Interests",
        **{username: metrics['topics'] for username, metrics in user_metrics.items()}
    }]

    return {
        "activity_comparison": activity_metrics,
        "repository_comparison": repo_metrics,
        "language_comparison": language_metrics,
        "topic_comparison": topic_metrics
    }
        
def analyze_compatibility_metrics(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Generate numerical metrics for Chart.js visualization"""
    
    if len(user_profiles) < 2:
        return {}
    
    # Expertise-based compatibility analysis
    expertise_overlap = {}
    collaboration_potential = {}
    
    for profile in user_profiles:
        username = profile.username
        basic_info = profile.basic_info
        
        if 'expertise_analysis' in basic_info:
            expertise = basic_info['expertise_analysis']
            
            # Create expertise mapping
            expertise_overlap[username] = {
                'primary_expertise': expertise.get('primary_expertise', []),
                'collaboration_type': expertise.get('collaboration_type', 'Unknown'),
                'activity_consistency': expertise.get('activity_consistency', 0),
                'engagement_patterns': expertise.get('engagement_patterns', {})
            }
            
            # Calculate collaboration potential
            engagement = expertise.get('engagement_patterns', {})
            collaboration_potential[username] = {
                'project_initiator_ratio': engagement.get('project_initiator_ratio', 0),
                'contributor_ratio': engagement.get('contributor_ratio', 0),
                'active_projects': engagement.get('active_projects', 0),
                'recent_activity_score': engagement.get('recent_activity_score', 0)
            }
    
    # Language overlap analysis (keeping for backward compatibility)
    all_languages = set()
    user_languages = {}
    
    for profile in user_profiles:
        user_langs = {lang: bytes_count for lang, bytes_count in profile.languages}
        user_languages[profile.username] = user_langs
        all_languages.update(user_langs.keys())
    
    common_languages = []
    language_overlap = {}
    
    for lang in all_languages:
        users_with_lang = [user for user in user_languages if lang in user_languages[user]]
        if len(users_with_lang) > 1:
            common_languages.append(lang)
            language_overlap[lang] = len(users_with_lang)
    
    # Topic overlap analysis
    all_topics = set()
    user_topics = {}
    
    for profile in user_profiles:
        user_topic_set = {topic: count for topic, count in profile.topics}
        user_topics[profile.username] = user_topic_set
        all_topics.update(user_topic_set.keys())
    
    common_topics = []
    topic_overlap = {}
    
    for topic in all_topics:
        users_with_topic = [user for user in user_topics if topic in user_topics[user]]
        if len(users_with_topic) > 1:
            common_topics.append(topic)
            topic_overlap[topic] = len(users_with_topic)
    
    return {
        "language_overlap": language_overlap,
        "topic_overlap": topic_overlap,
        "common_languages": common_languages,
        "common_topics": common_topics,
        "user_language_distribution": user_languages,
        "user_topic_distribution": user_topics,
        "expertise_overlap": expertise_overlap,
        "collaboration_potential": collaboration_potential
    }